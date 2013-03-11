# -*- coding: utf-8 -*-

'''
Created on 2013-2-3

@author: lxy@hesong.net
'''

import os
import sys
from ctypes import create_string_buffer, string_at, byref, c_char, c_byte, c_int, c_long, c_ushort, c_void_p, c_char_p 
from types import FunctionType, MethodType

if sys.version_info[0] < 3:
    import _c_smartbus_netcli_interface as sbncif
    from smartbus import PackInfo
    from smartbus.utils import default_encoding, bytes_to_text, text_to_bytes
else:
    from . import _c_smartbus_netcli_interface as sbncif
    from .. import PackInfo
    from ..utils import default_encoding, bytes_to_text, text_to_bytes

class Client(object):
    __lib = None
    __unitid = None
    __instances = {}

    def __init__(self, localClientId, localClientType, masterHost, masterPort, slaverHost=None, slaverPort=0, authorUsr=None, authorPwd=None, extInfo=None, encoding=default_encoding):
        if not Client.isInitialized():
            raise NotInitializedError()
        cls = type(self)
        if localClientId in cls.__instances:
            raise AlreadyExistsError()
        cls.__instances[localClientId] = self
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
        cls.__instances.clear()
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
                    txt = None
                    if data:
                        txt = bytes_to_text(string_at(data, size), inst.encoding)
                        txt = txt.strip('\x00')
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

    def dispose(self):
        cls = type(self)
        cls.__instances.pop(self.__localClientId, None)

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
        pass

    def sendText(self, cmd, cmdType, dstUnitId, dstClientId, dstClientType, txt, encoding=None):
        if not encoding:
            encoding = self.encoding
        data = text_to_bytes(txt, encoding)
        data_pc = create_string_buffer(data) if data else None
        data_sz = len(data_pc) if data_pc else 0
        result = sbncif._c_fn_SendData(
            self.__c_localClientId,
            c_byte(cmd),
            c_byte(cmdType),
            c_int(dstUnitId),
            c_int(dstClientId),
            c_int(dstClientType),
            byref(data_pc),
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
