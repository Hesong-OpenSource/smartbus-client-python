# -*- coding: utf-8 -*-

'''smartbus 进程间通信客户端的Python接口类客户端类型
:author: lxy@hesong.net
:date: 2013-6-8
'''

from __future__ import absolute_import

import sys
import os
import platform
import logging
from ctypes import create_string_buffer, string_at, byref, c_byte, c_int, c_void_p, c_char_p

import json

from . import _c_smartbus_ipccli_interface as sbicif
from .._c_smartbus import PackInfo
from ..utils import default_encoding, to_str, to_bytes
from .. import errors


class Client(object):
    '''SmartBus IPC 客户端类
    
    这个类封装了 SmartBus IPC 客户端的一系列方法与事件
    '''
    __lib = None
    __instance = None

    # # 构造函数
    # @param self
    # @param encoding 
    # @see encoding
    def __init__(self, username=None, password=None, extInfo=None, encoding=default_encoding):
        '''构造函数
        
        :param username: 验证用户名
        :param password: 验证密码
        :param extInfo: 附加信息
        :param encoding: 收/发字符串时使用的编码。默认为 smartbus.utils.default_encoding
        '''
        # # 编码
        #
        # 收/发字符串时使用该编码进行编解码处理。该属性由构造函数的encoding参数指定
        self.__username = username
        self.__password = password
        self.__extInfo = extInfo
        self.encoding = encoding
        self._c_username = to_bytes(self.__username, self.encoding)
        self._c_password = to_bytes(self.__password, self.encoding)
        self.__c_extInfo = c_char_p(to_bytes(self.__extInfo, self.encoding))
        cls = type(self)
        if not cls.__lib:
            raise errors.NotInitializedError()
        if cls.__instance:
            raise errors.AlreadyExistsError()
        cls.__instance = self

    def __del__(self):
        cls = type(self)
        cls.__instance = None

    # # 初始化
    #
    # 调用其他方法前，必须首先初始化库
    # @param cls 类
    # @param clientid 客户端ID。在同一个节点中，ID必须唯一。
    # @param clienttype 客户端类型。
    # @param libraryfile 库文件。如果不指定该参数，则加载时，会自动搜索库文件，
    # 其搜索的目录次序为：系统目录、../cdll/${system}/${machine}、 运行目录、当前目录、本文件目录。@see _c_smartbus_ipccli_interface.lib_filename
    @classmethod
    def initialize(cls, clientid, clienttype, onglobalconnect=None, libraryfile=sbicif.lib_filename, logging_option=(True, logging.DEBUG, logging.ERROR)):
        '''初始化
        
        这是一个类方法。调用其他方法前，必须首先使用这个方法初始化库。
        :param clientid: 客户端ID。在同一个节点中，ID必须唯一。不得小于等于16
        :param clienttype: 客户端类型。
        :param onglobalconnect:
        :param libraryfile:
        '''
        cls._clientid = clientid
        cls._clienttype = clienttype
        cls.__logging_option = logging_option
        cls.__logger = logging.getLogger('{}.{}'.format(cls.__module__, cls.__qualname__ if hasattr(cls, '__qualname__') else cls.__name__))
        if cls.__lib:
            raise errors.AlreadyInitializedError()
        if not libraryfile:
            libraryfile = sbicif.lib_filename
        try:
            cls.__lib = sbicif.load_lib(libraryfile)
        except:
            try:
                cls.__lib = sbicif.load_lib(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cdll', platform.system(), platform.machine(), libraryfile))
            except:
                try:
                    cls.__lib = sbicif.load_lib(os.path.join(os.getcwd(), libraryfile))    
                except:
                    try:
                        cls.__lib = sbicif.load_lib(os.path.join(os.path.curdir, libraryfile))
                    except:
                        cls.__lib = sbicif.load_lib(os.path.join(os.path.dirname(os.path.abspath(__file__)), libraryfile))
        errors.check_restval(sbicif._c_fn_Init(clienttype, clientid))
        cls.__c_fn_connection_cb = sbicif._c_fntyp_connection_cb(cls.__connection_cb)
        cls.__c_fn_recvdata_cb = sbicif._c_fntyp_recvdata_cb(cls.__recvdata_cb)
        cls.__c_fn_disconnect_cb = sbicif._c_fntyp_disconnect_cb(cls.__disconnect_cb)
        cls.__c_fn_invokeflow_ret_cb = sbicif._c_fntyp_invokeflow_ret_cb(cls.__invokeflow_ret_cb)
        cls.__c_fn_invokeflow_ack_cb = sbicif._c_fntyp_invokeflow_ret_cb(cls.__invokeflow_ack_cb)
        cls.__c_fn_global_connect_cb = sbicif._c_fntyp_global_connect_cb(cls.__global_connect_cb)
        cls.__onglobalconnect = onglobalconnect
        sbicif._c_fn_SetCallBackFn(
            cls.__c_fn_connection_cb,
            cls.__c_fn_recvdata_cb,
            cls.__c_fn_disconnect_cb,
            cls.__c_fn_invokeflow_ret_cb,
            cls.__c_fn_global_connect_cb,
            c_void_p(None)
        )
        sbicif._c_fn_SetCallBackFnEx(c_char_p(b"smartbus_invokeflow_ack_cb"), cls.__c_fn_invokeflow_ack_cb)
        if logging_option[0]:
            cls.__c_fn_trace_cb = sbicif._c_fntyp_trace_str_cb(cls.__trace_cb)
            cls.__c_fn_traceerr_cb = sbicif._c_fntyp_trace_str_cb(cls.__traceerr_cb)
            sbicif._c_fn_SetTraceStr(cls.__c_fn_trace_cb, cls.__c_fn_traceerr_cb)

    # # 释放库
    # @param cls 类
    @classmethod
    def finalize(cls):
        if cls.__instance:
            del cls.__instance
            cls.__instance = None
        if cls.__lib:
            sbicif._c_fn_Release()
            cls.__lib = None

    # # 判断是否初始化
    #
    # @param cls 类
    # @return 布尔型返回值
    @classmethod
    def isInitialized(cls):
        return cls.__lib is not None

    # # 返回该类型的实例
    #
    # 由于一个进程只能有一个实例，所以可用该方法返回目前的实例。
    @classmethod
    def instance(cls, username=None, password=None, extInfo=None):
        if cls.__instance:
            return cls.__instance
        else:
            return Client(username, password, extInfo)

    @classmethod
    def __connection_cb(cls, arg, local_clientid, accesspoint_unitid, ack):
        inst = cls.__instance
        inst._unitid = accesspoint_unitid
        inst._clientid = local_clientid
        if ack == 0:  # 连接成功
            if callable(inst.onConnectSuccess):
                inst.onConnectSuccess(accesspoint_unitid)
        else:  # 连接失败
            if callable(inst.onConnectFail):
                inst.onConnectFail(accesspoint_unitid, ack)

    @classmethod
    def __disconnect_cb(cls, param, local_clientid):
        inst = cls.__instance
        if callable(inst.onDisconnect):
            inst.onDisconnect()

    @classmethod
    def __recvdata_cb(cls, param, local_clientid, head, data, size):
        inst = cls.__instance
        if callable(inst.onReceiveText):
            packInfo = PackInfo(head)
            txt = None
            if data:
                bytestr = string_at(data, size)
                bytestr = bytestr.strip(b'\x00')
                txt = to_str(bytestr, inst.encoding)
                inst.onReceiveText(packInfo, txt)

    @classmethod
    def __invokeflow_ret_cb(cls, arg, local_clientid, head, projectid, invoke_id, ret, param):
        inst = cls.__instance
        if ret == 1:
            if callable(inst.onInvokeFlowRespond):
                packInfo = PackInfo(head)
                txt_projectid = to_str(projectid.strip('b\x00'), inst.encoding)
                txt_param = to_str(param.strip('b\x00').strip(), inst.encoding)
                if txt_param:
                    py_param = json.loads(txt_param, encoding=inst.encoding)
                else:
                    py_param = None
                inst.onInvokeFlowRespond(packInfo, txt_projectid, invoke_id, py_param)
        elif ret == -1:
            if callable(inst.onInvokeFlowTimeout):
                txt_projectid = to_str(projectid.strip('b\x00'), inst.encoding)
                packInfo = PackInfo(head)
                inst.onInvokeFlowTimeout(packInfo, txt_projectid, invoke_id)
                
    @classmethod
    def __invokeflow_ack_cb(cls, arg, local_clientid, head, projectid, invoke_id, ack, msg):
        inst = cls.__instance
        if inst is not None:
            if hasattr(inst, 'onInvokeFlowAcknowledge'):
                packInfo = PackInfo(head)
                txt_projectid = to_str(projectid.strip('b\x00'), inst.encoding)
                txt_msg = to_str(msg.strip('b\x00'), inst.encoding)
                inst.onInvokeFlowAcknowledge(packInfo, txt_projectid, invoke_id, ack, txt_msg)

    @classmethod
    def __global_connect_cb(cls, arg, unitid, clientid, clienttype, status, ext_info):
        if callable(cls.__onglobalconnect):
            if sys.version_info[0] < 3:
                if len(cls.__instances) > 0:
                    for v in cls.__instances.values():
                        inst = v
                        break
                    cls.__onglobalconnect(inst, ord(unitid), ord(clientid), ord(clienttype), ord(status), to_str(ext_info))
            else:
                cls.__onglobalconnect(ord(unitid), ord(clientid), ord(clienttype), ord(status), to_str(ext_info))
                
    @classmethod
    def __trace_cb(cls, msg):
        cls.__logger.log(cls.__logging_option[1], to_str(msg))
    
    @classmethod
    def __traceerr_cb(cls, msg):
        cls.__logger.log(cls.__logging_option[2], to_str(msg))
        
    @property
    def library(self):
        return self.__lib
    
    def get_unitid(self):
        return self._unitid
    unitid = property(get_unitid)
    
    def get_clientid(self):
        return self._clientid
    clientid = property(get_clientid)
    
    def get_clienttype(self):
        return self._clienttype
    clienttype = property(get_clienttype)
    
    def get_addr_expr(self):
        return '{} {} {}'.format(self.unitid, self.clientid, self.clienttype)
    addr_expr = property(get_addr_expr)

    # # @name 事件
    # # @{

    # # 连接成功事件
    # @param self
    # @param unitId 单元ID
    def onConnectSuccess(self, unitId):
        pass

    # # 连接失败事件
    # @param self
    # @param unitId 单元ID
    # @param errno 错误编码
    def onConnectFail(self, unitId, errno):
        pass

    # # 连接中断事件
    # @param self
    # @param unitId 单元ID
    # @param errno 错误编码
    def onDisconnect(self):
        pass

    # # 收到文本事件
    # @param self
    # @param packInfo 数据包信息
    # @param txt 收到的文本
    # @see PackInfo
    def onReceiveText(self, packInfo, txt):
        pass
    
    def onInvokeFlowAcknowledge(self, packInfo, project, invokeId, ack, msg):
        pass

    # # 收到流程返回数据事件
    # @param self
    # @param packInfo 数据包信息。
    # @param project 流程所在的项目
    # @param invokeId 调用ID。它对应于 @ref invokeFlow "invokeFlow 方法"返回的ID
    # @param result 返回的数据。JSON数组格式
    # @see PackInfo
    def onInvokeFlowRespond(self, packInfo, project, invokeId, result):
        pass

    # # 流程返回超时事件
    # @param self
    # @param packInfo 数据包信息。
    # @param project 流程所在的项目
    # @param invokeId 调用ID。它对应于该对象的 @ref invokeFlow "invokeFlow() 方法"返回值
    # @see PackInfo
    def onInvokeFlowTimeout(self, packInfo, project, invokeId):
        pass

    # # @}

    # # 连接服务器
    #
    # 如果连接失败，则抛出 @ref ConnectError 异常。
    # @param self
    # @param username
    # @param password
    # @param info
    def connect(self, username=None, password=None):
        result = sbicif._c_fn_CreateConnect(self._c_username, self._c_password, self.__c_extInfo)
        errors.check_restval(result)

    # # 发送数据
    # @param self
    # @param cmd 命令
    # @param cmdType 命令类型
    # @param dstUnitId 目标节点ID
    # @param dstClientId 目标客户端ID
    # @param dstClientType 目标客户端类型
    # @param data 待发送数据，可以是文本或者字节数组
    # @param encoding 文本的编码。默认为该对象的 @ref encoding "编码"属性。
    def send(self, cmd, cmdType, dstUnitId, dstClientId, dstClientType, data, encoding=None):
        data = to_bytes(data, encoding if encoding else self.encoding)
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
        errors.check_restval(result)

    # # 调用流程
    #
    # 如果连接失败，则抛出 @ref SendDataError 异常
    # @param self
    # @param server IPSC流程服务所在节点
    # @param process IPSC进程索引值
    # @param project 流程项目名称
    # @param flow 流程名称
    # @param parameters 流程传入参数
    # @param isNeedReturn 是否需要流程返回值
    # @param timeout 等待流程返回超时值，单位为秒。
    # @param encoding 文本的编码。默认为该对象的 @ref encoding 属性。
    # @return 当需要等待流程返回值时，该返回值是@ref onInvokeFlowRespond "流程返回事件"中对应的ID.
    def invokeFlow(self, server, process, project, flow, parameters=[], isNeedReturn=True, timeout=30, encoding=None):
        if not encoding:
            encoding = self.encoding
        c_server_unitid = c_int(server)
        c_processindex = c_int(process)
        c_project_id = c_char_p(to_bytes(project, encoding))
        c_flowid = c_char_p(to_bytes(flow, encoding))
        c_invoke_mode = c_int(0) if isNeedReturn else c_int(1)
        c_timeout = c_int(int(timeout * 1000))
        if parameters is None:
            parameters = []
        else:
            if isinstance(parameters, (int, float, str, bool , dict)):
                parameters = [parameters]
            else:
                parameters = list(parameters)
        c_in_valuelist = c_char_p(to_bytes(str(parameters), encoding))
        result = sbicif._c_fn_RemoteInvokeFlow(
            c_server_unitid,
            c_processindex,
            c_project_id,
            c_flowid,
            c_invoke_mode,
            c_timeout,
            c_in_valuelist
        )
        if result < 0:
            errors.check_restval(result)
        elif result == 0:
            raise errors.InvokeFlowIdError()
        return result

    def ping(self, dstUnitId, dstClientId, dstClientType, data, encoding=None):
        data = to_bytes(data, encoding if encoding else self.encoding)
        data_pc = create_string_buffer(data) if data else None
        data_sz = len(data_pc) if data_pc else 0
        result = sbicif._c_fn_SendPing(
            self.__c_localClientId,
            c_int(dstUnitId),
            c_int(dstClientId),
            c_int(dstClientType),
            byref(data_pc),
            c_int(data_sz)
        )
        errors.check_restval(result)
