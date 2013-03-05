# -*- coding: utf-8 -*-

'''
Created on 2013-2-3

@author: lxy@hesong.net
'''

import os
import sys
from ctypes import string_at, c_char, c_byte, c_int, c_char_p , c_void_p, c_ushort, c_long
from types import FunctionType, MethodType

if sys.version_info[0] < 3:
    import _c_smartbus_netcli_interface as sbncif
    from smartbus import PackInfo
    from smartbus.utils import default_encoding, bytes_to_text, text_to_bytes, ifnone
else:
    from . import _c_smartbus_netcli_interface as sbncif
    from .. import PackInfo
    from ..utils import default_encoding, bytes_to_text, text_to_bytes, ifnone

class PackInfo(object):
    def __init__(self, lp_head_struct):
        self.__cmd = 0
        self.__cmdType = 0
        self.__srcUnitClientType = 0
        self.__srcUnitId = 0
        self.__srcUnitClientId = 0
        self.__dstUnitClientType = 0
        self.__dstUnitId = 0
        self.__dstUnitClientId = 0
        if lp_head_struct:
            head_struct = lp_head_struct.contents
            if head_struct:
                self.__cmd = head_struct.cmd
                self.__cmdType = head_struct.cmdtype
                self.__srcUnitClientType = ord(head_struct.src_unit_client_type)
                self.__srcUnitId = ord(head_struct.src_unit_id)
                self.__srcUnitClientId = ord(head_struct.src_unit_client_id)
                self.__dstUnitClientType = ord(head_struct.dest_unit_client_type)
                self.__dstUnitId = ord(head_struct.dest_unit_id)
                self.__dstUnitClientId = ord(head_struct.dest_unit_client_id)
                
    @property
    def cmd(self):
        return self.__cmd
    
    @property
    def cmdType(self):
        return self.__cmdType
    
    @property
    def srcUnitClientType(self):
        return self.__srcUnitClientType
    
    @property
    def srcUnitId(self):
        return self.__srcUnitId
    
    @property
    def srcUnitClientId(self):
        return self.__srcUnitClientId
    
    @property
    def dstUnitClientType(self):
        return self.__dstUnitClientType
    
    @property
    def dstUnitId(self):
        return self.__dstUnitId
    
    @property
    def dstUnitClientId(self):
        return self.__dstUnitClientId


class Client(object):
    __lib = None
    __unitid = None
    __instances = {}
    
    @classmethod
    def initialize(cls, unitid, libraryfile=sbncif.lib_filename):
        if cls.__unitid is not None:
            raise AlreadyInitializedError()
        if not libraryfile:
            libraryfile = sbncif.lib_filename
        try:
            cls.__lib = sbncif.load_lib(libraryfile)
        except:
            try:
                cls.__lib = sbncif.load_lib(os.path.join(os.path.curdir, libraryfile))
            except:
                try:
                    cls.__lib = sbncif.load_lib(os.path.join(os.getcwd(), libraryfile))
                except:
                    try:
                        cls.__lib = sbncif.load_lib(os.path.join(os.path.dirname(__file__), libraryfile))
                    except:
                        raise
        sbncif._c_fn_Init(unitid)
        cls.__unitid = unitid
        cls.__c_fn_connection_cb = sbncif._c_fntyp_connection_cb(cls.__connection_cb)
        cls.__c_fn_recvdata_cb = sbncif._c_fntyp_recvdata_cb(cls.__recvdata_cb)
        cls.__c_fn_disconnect_cb = sbncif._c_fntyp_disconnect_cb(cls.__disconnect_cb)
        cls.__c_fn_invokeflow_ret_cb = sbncif._c_fntyp_invokeflow_ret_cb(cls.__invokeflow_ret_cb)
        sbncif._c_fn_SetCallBackFn(
            cls.__c_fn_connection_cb,
            cls.__c_fn_recvdata_cb,
            cls.__c_fn_disconnect_cb,
            cls.__c_fn_invokeflow_ret_cb,
            c_void_p(None)
        )
    
    @classmethod 
    def finalize(cls):
        while len(cls.__instances):
            _, inst = cls.__instances.popitem()
            del inst            
        if cls.__unitid is not None:
            sbncif._c_fn_Release()
            cls.__unitid = None
    
    @classmethod  
    def isInitialized(cls):
        return cls.__unitid is not None
    
    @classmethod
    def getUnitId(cls):
        return cls.__unitid
    
    @classmethod
    def __connection_cb(cls, arg, local_clientid, accesspoint_unitid, ack):
        inst = cls.__instances.get(local_clientid, None)
        if inst is not None:
            if ack == 0:  # 连接成功
                if hasattr(inst, 'onConnectSuccess'):
                    fn = inst.onConnectSuccess
                    if isinstance(fn, FunctionType):
                        fn(inst, accesspoint_unitid)
                    elif isinstance(fn, MethodType):
                        fn(accesspoint_unitid)
            else:  # 连接失败
                if hasattr(inst, 'onConnectFail'):
                    fn = inst.onConnectFail
                    if isinstance(fn, FunctionType):
                        fn(inst, accesspoint_unitid, ack)
                    elif isinstance(fn, MethodType):
                        fn(accesspoint_unitid, ack)

    @classmethod
    def __disconnect_cb(cls, param, local_clientid):
        inst = cls.__instances.get(local_clientid, None)
        if inst is not None:
            if hasattr(inst, 'onDisconnect'):
                fn = inst.onDisconnect
                if isinstance(fn, FunctionType):
                    fn(inst)
                elif isinstance(fn, MethodType):
                    fn()
    
    ## @todo: TODO: 广播的处理
    @classmethod
    def __recvdata_cb(cls, param, local_clientid, head, data, size):
        inst = cls.__instances.get(local_clientid, None)
        if inst is not None:
            if hasattr(inst, 'onReceiveText'):
                fn = inst.onReceiveText
                if callable(fn):
                    packInfo = PackInfo(head)
                    txt = bytes_to_text(string_at(data, size), inst.encoding)
                    if isinstance(fn, FunctionType):
                        fn(inst, packInfo, txt)
                    elif isinstance(fn, MethodType):
                        fn(packInfo, txt)
    
    @classmethod
    def __invokeflow_ret_cb(cls, arg, local_clientid, head, projectid, invoke_id, ret, param):
        inst = cls.__instances.get(local_clientid, None)
        if inst is not None:
            if ret == 1:
                if hasattr(inst, 'onInvokeFlowRespond'):
                    fn = inst.onInvokeFlowRespond
                    if callable(fn):
                        packInfo = PackInfo(head)
                        txt_projectid = bytes_to_text(projectid, inst.encoding)
                        txt_param = bytes_to_text(param, inst.encoding)
                        py_param = eval(txt_param)
                        if isinstance(fn, FunctionType):
                            fn(inst, packInfo, txt_projectid, invoke_id, py_param)
                        elif isinstance(fn, MethodType):
                            fn(packInfo, txt_projectid, invoke_id, py_param)
            elif ret == -1:
                if hasattr(inst, 'onInvokeFlowTimeout'):
                    fn = inst.onInvokeFlowTimeout
                    if callable(fn):
                        txt_projectid = bytes_to_text(projectid, inst.encoding)
                        packInfo = PackInfo(head)
                        if isinstance(fn, FunctionType):
                            fn(inst, packInfo, txt_projectid, invoke_id)
                        elif isinstance(inst, MethodType):
                            fn(packInfo, txt_projectid, invoke_id)
        
        
    def __init__(self, localClientId, localClientType, masterHost, masterPort, slaverHost=None, slaverPort=0, authorUsr=None, authorPwd=None, extInfo=None, encoding=default_encoding):
        if not Client.isInitialized():
            raise NotInitializedError()
        if localClientId in self.__instances:
            raise AlreadyExistsError()
        self.__instances[localClientId] = self
        self.__localClientId = localClientId
        self.__localClientType = localClientType
        self.__masterHost = masterHost
        self.__masterPort = masterPort
        self.__slaverHost = slaverHost
        self.__slaverPort = slaverPort
        self.__authorUsr = authorUsr
        self.__authorPwd = authorPwd
        self.__extInfo = extInfo
        self.__encoding = encoding
        self.__c_localClientId = c_byte(self.__localClientId)
        self.__c_localClientType = c_long(self.__localClientType)
        self.__c_masterHost = c_char_p(text_to_bytes(self.__masterHost, self.encoding))
        self.__c_masterPort = c_ushort(self.__masterPort)
        self.__c_slaverHost = c_char_p(text_to_bytes(self.__slaverHost, self.encoding))
        self.__c_slaverPort = c_ushort(self.__slaverPort)
        self.__c_authorUsr = c_char_p(text_to_bytes(self.__authorUsr, self.encoding))
        self.__c_authorPwd = c_char_p(text_to_bytes(self.__authorPwd, self.encoding))
        self.__c_extInfo = c_char_p(text_to_bytes(self.__extInfo, self.encoding))
        
    def __del__(self):
        self.__instances.pop(self.__localClientId, None)
        
    @property
    def localClientId(self):
        return self.__localClientId
    
    @property
    def localClientType(self):
        return self.__localClientType
    
    @property
    def masterHost(self):
        return self.__masterHost
    
    @property
    def slaverHost(self):
        return self.__slaverHost
    
    @property
    def slaverPort(self):
        return self.__slaverPort
    
    @property
    def authorUsr(self):
        return self.__authorUsr
    
    @property
    def authorPwd(self):
        return self.__authorPwd
    
    @property
    def extInfo(self):
        return self.__extInfo
    
    @property
    def encoding(self):
        return self.__encoding
    
    def onConnectSuccess(self, unitId):
        pass
    
    def onConnectFail(self, unitId, errno):
        pass
    
    def onDisconnect(self):
        pass
    
    def onReceiveText(self, packInfo, txt):
        pass
    
    def onInvokeFlowRespond(self, packInfo, project, invokeId, result):
        pass
    
    def onInvokeFlowTimeout(self, packInfo, project, invokeId):
        pass


    ##
    #@param local_clientid 本地clientid, >= 0 and <= 255
    #@param local_clienttype 本地clienttype
    #@param masterip 目标主IP地址
    #@param masterport 目标主端口
    #@param slaverip 目标从IP地址
    #@param slaverport 目标从端口
    #@param author_username 验证用户名
    #@param author_pwd 验证密码
    #@param add_info 附加信息    
    def connect(self):
        result = sbncif._c_fn_CreateConnect(
            self.__c_localClientId,
            self.__c_localClientType,
            self.__c_masterHost,
            self.__c_masterPort,
            self.__c_slaverHost,
            self.__c_slaverPort,
            self.__c_authorUsr,
            self.__c_authorPwd,
            self.__c_extInfo
        )
        if result != 0:
            raise ConnectError()
        return result
 
    def sendText(self, cmd, cmdType, dstUnitId, dstClientId, dstClientType, txt, encoding=None):
        if not encoding:
            encoding = self.encoding
        data = text_to_bytes(txt, encoding)
        data_sz = len(data) + 1 if data else 0
        result = sbncif._c_fn_SendData(
            self.__c_localClientId,
            c_byte(cmd),
            c_byte(cmdType),
            c_int(dstUnitId),
            c_int(dstClientId),
            c_int(dstClientType),
            c_char_p(data),
            c_int(data_sz)
        )
        if result != 0:
            raise SendDataError('SmartBusNetCli_SendData() returns %d' % (result))

    def sendBytes(self, cmd, cmdType, dstUnitId, dstClientId, dstClientType, data):
        result = sbncif._c_fn_SendData(
            c_byte(cmd),
            c_byte(cmdType),
            c_int(dstUnitId),
            c_int(dstClientId),
            c_int(dstClientType),
            c_char_p(data),
            c_int(len(data) if data else 0)
        )
        if result != 0:
            raise SendDataError('SmartBusNetCli_SendData() returns %d' % (result))
    
    def invokeFlow(self, server, process, project, flow, parameters=[], isNeedReturn=True, timeout=30, encoding=None):
        if not encoding:
            encoding = self.encoding
        c_server_unitid = c_int(server)
        c_processindex = c_int(process)
        c_project_id = c_char_p(text_to_bytes(project, encoding))
        c_flowid = c_char_p(text_to_bytes(flow, encoding))
        c_invoke_mode = c_int(0) if isNeedReturn else c_int(1)
        c_timeout = c_int(int(timeout * 1000))
        if parameters is None:
            parameters = []
        else:
            if isinstance(parameters, (int, float, str, bool , dict)):
                parameters = [parameters]
            else:
                parameters = list(parameters)
        c_in_valuelist = c_char_p(text_to_bytes(str(parameters), encoding))
        result = sbncif._c_fn_RemoteInvokeFlow(
            self.__c_localClientId,
            c_server_unitid,
            c_processindex,
            c_project_id,
            c_flowid,
            c_invoke_mode,
            c_timeout,
            c_in_valuelist
        )
        if result <= 0:
            raise SendDataError('SmartBusNetCli_RemoteInvokeFlow reutrns %d' % (result))
        return result


class AlreadyInitializedError(Exception):
    pass

class NotInitializedError(Exception):
    pass

class AlreadyExistsError(Exception):
    pass

class ConnectError(Exception):
    pass

class SendDataError(Exception):
    pass
