#-*- coding: utf-8 -*-

##@package smartbus.ipcclient
#smartbus 进程通信客户端的Python接口类
#
#
# @date 2013-1-28
#
# @author: lxy@hesong.net
#

import os
import sys
from ctypes import create_string_buffer, string_at, byref, c_char, c_byte, c_int, c_void_p, c_char_p 
from types import FunctionType, MethodType

if sys.version_info[0] < 3:
    import _c_smartbus_ipccli_interface as sbicif
    from smartbus import PackInfo
    from smartbus.utils import default_encoding, bytes_to_text, text_to_bytes
else:
    from . import _c_smartbus_ipccli_interface as sbicif
    from .. import PackInfo
    from ..utils import default_encoding, bytes_to_text, text_to_bytes

## SmartBus IPC 客户端类
#
# 这个类封装了 SmartBus IPC 客户端的一系列方法与事件
class Client(object):
    __lib = None
    __instance = None
    
    ## 构造函数
    # @param self
    # @param encoding 收/发字符串时使用的编码。默认为操作系统编码。
    # @see smartbus.utils.default_encoding
    # @see encoding
    def __init__(self, encoding=default_encoding):
        ## 编码
        #
        # 收/发字符串时使用该编码进行编解码处理。该属性由构造函数的encoding参数指定
        self.encoding = encoding
        cls = type(self)
        if not cls.__lib:
            raise NotInitializedError()
        if cls.__instance:
            raise AlreadyExistsError()
        cls.__instance = self
    
    def __del__(self):
        cls = type(self)
        cls.__instance = None
    
    ## 初始化
    #
    # 每次使用之前，必须先调用该类方法，进行初始化
    # @param cls 类
    # @param clientid 客户端ID。在同一个节点中，ID必须唯一。
    # @param clienttype 客户端类型。
    # @param libraryfile 库文件。如果不指定该参数，则加载时，会自动搜索库文件，其搜索的目录次序为：系统目录、当前目录、运行目录、文件目录。@see _c_smartbus_ipccli_interface.lib_filename
    @classmethod
    def initialize(cls, clientid, clienttype, libraryfile=sbicif.lib_filename):
        if cls.__lib:
            raise AlreadyInitializedError()
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

        sbicif._c_fn_Init(clienttype, clientid)
        cls.__c_fn_connection_cb = sbicif._c_fntyp_connection_cb(cls.__connection_cb)
        cls.__c_fn_recvdata_cb = sbicif._c_fntyp_recvdata_cb(cls.__recvdata_cb)
        cls.__c_fn_disconnect_cb = sbicif._c_fntyp_disconnect_cb(cls.__disconnect_cb)
        cls.__c_fn_invokeflow_ret_cb = sbicif._c_fntyp_invokeflow_ret_cb(cls.__invokeflow_ret_cb)
        sbicif._c_fn_SetCallBackFn(
            cls.__c_fn_connection_cb,
            cls.__c_fn_recvdata_cb,
            cls.__c_fn_disconnect_cb,
            cls.__c_fn_invokeflow_ret_cb,
            c_void_p(None)
        )

    ## 释放库
    # @param cls 类
    @classmethod 
    def finalize(cls):
        if cls.__instance:
            del cls.__instance
            cls.__instance = None
        if cls.__lib:
            sbicif._c_fn_Release()
            cls.__lib = None
    
    ## 判断是否初始化
    #
    # @param cls 类
    # @return 布尔型返回值
    @classmethod  
    def isInitialized(cls):
        return cls.__lib is not None
    
    ## 返回该类型的实例
    #
    # 由于一个进程只能有一个实例，所以可用该方法返回目前的实例。
    @classmethod
    def instance(cls):
        if cls.__instance:
            return cls.__instance
        else:
            return Client()
    
    @classmethod
    def __connection_cb(cls, arg, local_clientid, accesspoint_unitid, ack):
        inst = cls.__instance
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
        inst = cls.__instance
        if hasattr(inst, 'onDisconnect'):
            fn = inst.onDisconnect
            if isinstance(fn, FunctionType):
                fn(inst)
            elif isinstance(fn, MethodType):
                fn()
    
    @classmethod
    def __recvdata_cb(cls, param, local_clientid, head, data, size):
        inst = cls.__instance
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
        inst = cls.__instance
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
    
    
    ## @name 事件
    ## @{
    
    ## 连接成功事件
    # @param self 
    # @param unitId 实例ID
    def onConnectSuccess(self, unitId):
        pass
    
    ## 连接失败事件
    # @param self 
    # @param unitId 实例ID
    # @param errno 错误编码
    def onConnectFail(self, unitId, errno):
        pass

    ## 连接中断事件
    # @param self 
    # @param unitId 实例ID
    # @param errno 错误编码    
    def onDisconnect(self):
        pass
    
    ## 收到文本事件
    # @param self 
    # @param packInfo 数据包信息
    # @param txt 收到的文本 
    # @see PackInfo
    def onReceiveText(self, packInfo, txt):
        pass
    
    ## 收到流程返回数据事件
    # @param self 
    # @param packInfo 数据包信息。
    # @param project 流程所在的项目
    # @param invokeId 调用ID。它对应于 @ref invokeFlow "invokeFlow 方法"返回的ID
    # @param result 返回的数据。是一个Python对象。通常是一个list
    # @see PackInfo
    def onInvokeFlowRespond(self, packInfo, project, invokeId, result):
        pass
    
    ## 流程返回超时事件
    # @param self 
    # @param packInfo 数据包信息。
    # @param project 流程所在的项目
    # @param invokeId 调用ID。它对应于该对象的 @ref invokeFlow "invokeFlow() 方法"返回值
    # @see PackInfo
    def onInvokeFlowTimeout(self, packInfo, project, invokeId):
        pass
    
    ## @}
    
    ## 连接
    # @param self 
    # @param username
    # @param password
    # @param info
    def connect(self, username=None, password=None, info=None):
        b_username = text_to_bytes(username, self.encoding)
        b_password = text_to_bytes(password, self.encoding)
        b_info = text_to_bytes(info, self.encoding)
        result = sbicif._c_fn_CreateConnect(c_char_p(b_username), c_char_p(b_password), c_char_p(b_info))
        if result != 0:
            raise ConnectError()
 
    ## 发送文本
    # @param self 
    # @param cmd 命令
    # @param cmdType 命令类型
    # @param dstUnitId 目标节点ID
    # @param dstClientId 目标客户端ID
    # @param dstClientType 目标客户端类型
    # @param txt 待发送文本
    # @param encoding 文本的编码。默认为该对象的 @ref encoding "编码"属性。
    def sendText(self, cmd, cmdType, dstUnitId, dstClientId, dstClientType, txt, encoding=None):
        if not encoding:
            encoding = self.encoding
        data = text_to_bytes(txt, encoding)
        data_pc = create_string_buffer(data) if data else None
        data_sz = len(data_pc) if data_pc else 0
        result = sbicif._c_fn_SendData(
            c_byte(cmd),
            c_byte(cmdType),
            c_int(dstUnitId),
            c_int(dstClientId),
            c_int(dstClientType),
            byref(data_pc),
            c_int(data_sz)
        )
        if result != 0:
            raise SendDataError('SmartBusIpcCli_SendData() returns %d' % (result))
        
    ## 发送二进制数据
    # @param self 
    # @param cmd 命令
    # @param cmdType 命令类型
    # @param dstUnitId 目标节点ID
    # @param dstClientId 目标客户端ID
    # @param dstClientType 目标客户端类型
    # @param data 待发送数据。必须是bytes类型。
    def sendBytes(self, cmd, cmdType, dstUnitId, dstClientId, dstClientType, data):
        result = sbicif._c_fn_SendData(
            c_byte(cmd),
            c_byte(cmdType),
            c_int(dstUnitId),
            c_int(dstClientId),
            c_int(dstClientType),
            c_char_p(data),
            c_int(len(data) if data else 0)
        )
        if result != 0:
            raise SendDataError('SmartBusIpcCli_SendData() returns %d' % (result))
    
    ## 调用流程
    # @param self 
    # @param server IPSC流程服务所在节点
    # @param process IPSC进程索引值
    # @param project 流程项目名称
    # @param flow 流程名称
    # @param parameters 流程传入参数
    # @param isNeedReturn 是否需要流程返回值
    # @param timeout 等待流程返回超时值，单位为秒。
    # @param encoding 文本的编码。默认为该对象的 @ref encoding "编码"属性。
    # @return 当需要等待流程返回值时，该返回值是@ref onInvokeFlowRespond "流程返回事件"中对应的ID.
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
        result = sbicif._c_fn_RemoteInvokeFlow(
            c_server_unitid,
            c_processindex,
            c_project_id,
            c_flowid,
            c_invoke_mode,
            c_timeout,
            c_in_valuelist
        )
        if result <= 0:
            raise SendDataError('SmartBusIpcCli_RemoteInvokeFlow reutrns %d' % (result))
        return  result

## @name 异常类
## @{

## @exception 已经初始化，无法重复的初始化
class AlreadyInitializedError(Exception):
    pass

## @exception 尚未初始化，无法使用
class NotInitializedError(Exception):
    pass

## @exception 对象已经存在，无法再次新建
class AlreadyExistsError(Exception):
    pass

## @exception 连接服务器错误
class ConnectError(Exception):
    pass

## @exception 发送数据错误
class SendDataError(Exception):
    pass

## @}
