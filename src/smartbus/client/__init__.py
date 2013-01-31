#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on 2013-1-28

@author: lxy@hesong.net
'''

import os
import sys
from ctypes import c_char, c_byte, c_int, c_char_p , c_void_p
from types import FunctionType, MethodType

if sys.version_info[0] == 2:
    import _c_smartbus_ipccli_interface as sbicif
elif sys.version_info[0] == 3:
    from . import _c_smartbus_ipccli_interface as sbicif

default_encoding = sys.getfilesystemencoding()

def text_to_bytes(txt, encoding=default_encoding):
    data = None
    datasz = 0
    if txt is not None:
        if sys.version_info[0] == 2:
            import types
            if type(txt) == types.StringType:
                data = txt
            elif type(txt) == types.UnicodeType:
                data = txt.encode(encoding)
            else:
                raise TypeError('agument "text" must be StringType or UnicodeType')
            datasz = len(data)
        elif sys.version_info[0] == 3:
            data = txt.encode(encoding)
            datasz = len(data)
        else:
            raise NotImplementedError()
    return data, datasz

def bytes_to_text(data, encoding=default_encoding):
    txt = None
    if data is not None:
        txt = data.decode(encoding)            
    return txt
    

class NotInitializedError(Exception):
    pass

class AlreadyExistsError(Exception):
    pass

class Client(object):
    __lib = None
    __inited = False
    __instance = None
    
    
    @classmethod
    def initialize(cls, clientid, clienttype, libraryfile=sbicif.lib_filename):
        if not libraryfile:
            libraryfile = sbicif.lib_filename
        try:
            cls.__lib = sbicif.load_lib(libraryfile)
        except:
            try:
                cls.__lib = sbicif.load_lib(os.path.join(os.path.curdir, libraryfile))
            except:
                try:
                    cls.__lib = sbicif.load_lib(os.path.join(os.getcwd(), libraryfile))
                except:
                    try:
                        cls.__lib = sbicif.load_lib(os.path.join(os.path.dirname(__file__), libraryfile))
                    except:
                        raise
        if not cls.__inited:
            sbicif._c_fn_Init(clienttype, clientid)
            cls.__inited = True
    
    @classmethod 
    def finalize(cls):
        if cls.__inited:
            sbicif._c_fn_Release()
            cls.__inited = False
    
    @classmethod  
    def isInitialize(cls):
        return cls.__inited
    
    def __init__(self, encoding=default_encoding):
        if sys.version_info[0] == 2:
            ''.decode(encoding)
        elif sys.version_info[0] == 3:
            ''.encode(encoding)
        else:
            raise NotImplementedError()
        self.encoding = encoding
        if not Client.__inited:
            raise NotInitializedError()
        if Client.__instance:
            raise AlreadyExistsError()
        else:
            self.__c_fn_connection_cb = sbicif._c_fntyp_connection_cb(self.__connection_cb)
            self.__c_fn_recvdata_cb = sbicif._c_fntyp_recvdata_cb(self.__recvdata_cb)
            self.__c_fn_disconnect_cb = sbicif._c_fntyp_disconnect_cb(self.__disconnect_cb)
            self.__c_fn_invokeflow_ret_cb = sbicif._c_fntyp_invokeflow_ret_cb(self.__invokeflow_ret_cb)
            sbicif._c_fn_SetCallBackFn(
                self.__c_fn_connection_cb,
                self.__c_fn_recvdata_cb,
                self.__c_fn_disconnect_cb,
                self.__c_fn_invokeflow_ret_cb,
                c_void_p(None)
            )
            Client.__instance = self          
    
    @classmethod
    def instance(cls):
        if cls.__instance:
            return cls.__instance
        else:
            return Client()
    
    def __connection_cb(self, arg, ack):
        result = 0
        if ack == 0:  # 连接成功
            if hasattr(self, 'onConnectSuccess'):
                fn = self.onConnectSuccess
                if isinstance(fn, FunctionType):
                    result = fn()
                elif isinstance(fn, MethodType):
                    result = fn(self)
                if result is None:
                    result = 0
                if not isinstance(result, int):
                    raise TypeError('"onConnectSuccess" must return an Integer or None')
        else:  # 连接失败
            if hasattr(self, 'onConnectFail'):
                fn = self.onConnectFail
                if isinstance(fn, FunctionType):
                    fn(ack)
                elif isinstance(fn, MethodType):
                    fn(self, ack)
        return result

    def __disconnect_cb(self, param):
        if hasattr(self, 'onDisconnect'):
            fn = self.onDisconnect
            if isinstance(fn, FunctionType):
                fn()
            elif isinstance(fn, MethodType):
                fn(self)
    
    def __recvdata_cb(self, param, head, data, size):
        if hasattr(self, 'onReceiveText'):
            fn = self.onReceiveText
            if callable(fn):
                txt = bytes_to_text(data, self.encoding)
                if isinstance(fn, FunctionType):
                    fn(txt)
                elif isinstance(fn, MethodType):
                    fn(self, txt)
    
    def __invokeflow_ret_cb(self, arg, head, projectid, invoke_id, ret, param):
        if ret == 1:
            if hasattr(self, 'onInvokeFlowRespond'):
                fn = self.onInvokeFlowRespond
                if callable(fn):
                    txt_projectid = bytes_to_text(projectid, self.encoding)
                    txt_param = bytes_to_text(param, self.encoding)
                    if isinstance(fn, FunctionType):
                        fn(txt_projectid, invoke_id, txt_param)
                    elif isinstance(fn, MethodType):
                        fn(self, txt_projectid, invoke_id, txt_param)
        elif ret == -1:
            if hasattr(self, 'onInvokeFlowTimeout'):
                fn = self.onInvokeFlowTimeout
                if callable(fn):
                    txt_projectid = bytes_to_text(projectid, self.encoding)
                    if isinstance(fn, FunctionType):
                        fn(txt_projectid, invoke_id)
                    elif isinstance(self, MethodType):
                        fn(self, txt_projectid, invoke_id)
        
    def onConnectSuccess(self):
        pass
    
    def onConnectFail(self, errno):
        pass
    
    def onDisconnect(self):
        pass
    
    def onReceiveText(self, txt):
        pass
    
    def onInvokeFlowRespond(self, project, invokeId, result):
        pass
    
    def onInvokeFlowTimeout(self, project, invokeId):
        pass
    
    def connect(self, username=None, password=None, info=None):
        b_username, _ = text_to_bytes(username, self.encoding)
        b_password, _ = text_to_bytes(password, self.encoding)
        b_info, _ = text_to_bytes(info, self.encoding)
        return sbicif._c_fn_CreateConnect(c_char_p(b_username), c_char_p(b_password), c_char_p(b_info))
 
    def sendText(self, cmd, cmdType, dstUnitId, dstClientId, dstClientType, txt, encoding=None):
        if not encoding:
            encoding = self.encoding
        data, data_sz = text_to_bytes(txt, encoding)
        return sbicif._c_fn_SendData(c_byte(cmd), c_byte(cmdType), c_int(dstUnitId), c_int(dstClientId), c_int(dstClientType), c_char_p(data), c_int(data_sz))
    
    def invokeFlow(self, server, process, project, flow, parameter=None, isNeedReturn=True, timeout=30):
        c_server_unitid = c_int(server)
        c_processindex = c_int(process)
        c_project_id = c_char_p(text_to_bytes(project, self.encoding)[0])
        c_flowid = c_char_p(text_to_bytes(flow, self.encoding)[0])
        c_invoke_mode = c_int(0) if isNeedReturn else c_int(1)
        c_timeout = c_int(int(timeout / 1000))
        if parameter is not None:
            if isinstance(parameter, str):
                parameter, _ = text_to_bytes(parameter, self.encoding)
            else:
                raise NotImplementedError()
        c_in_valuelist = c_char_p(parameter)
        return sbicif._c_fn_RemoteInvokeFlow(c_server_unitid, c_processindex, c_project_id, c_flowid, c_invoke_mode, c_timeout, c_in_valuelist)
    
