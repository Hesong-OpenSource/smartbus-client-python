# -*- coding: utf-8 -*-

'''smartbus 进程间通信客户端的Python接口类客户端类型

:author: lxy@hesong.net
:date: 2013-6-8
'''

from __future__ import absolute_import

import os
import platform
import logging
from ctypes import create_string_buffer, string_at, byref, c_byte, c_int, c_void_p, c_char_p

import json

from . import _c_smartbus_ipccli_interface as sbicif
from .._c_smartbus import PackInfo, SMARTBUS_NODECLI_TYPE_IPSC, SMARTBUS_ERR_TIMEOUT
from ..utils import default_encoding, to_str, to_bytes
from .. import errors


class Client(object):
    '''SmartBus IPC 客户端类

    这个类封装了 SmartBus IPC 客户端的一系列方法与事件
    '''
    __lib = None
    __instance = None


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

    @classmethod
    def initialize(cls, clientid, clienttype, onglobalconnect=None, libraryfile=sbicif.lib_filename, logging_option=(True, logging.DEBUG, logging.ERROR)):
        '''初始化

        这是一个类方法。调用其他方法前，必须首先使用这个方法初始化库。

        :param clientid: 客户端ID。在同一个节点中，ID必须唯一。不得小于等于16
        :param clienttype: 客户端类型。
        :param onglobalconnect:
        :param libraryfile:

        ..note:: 其搜索的目录次序为：
                 系统目录、../cdll/${system}/${machine}、 运行目录、当前目录、本文件目录
        '''
        cls._clientid = clientid
        cls._clienttype = clienttype
        cls.__logging_option = logging_option
        cls.__logger = logging.getLogger('{}.{}'.format(cls.__module__, cls.__qualname__ if hasattr(cls, '__qualname__') else cls.__name__))
        cls.__logger.info('initialize')
        if cls.__lib:
            raise errors.AlreadyInitializedError()
        if not libraryfile:
            libraryfile = sbicif.lib_filename
        try:
            fpath = libraryfile
            cls.__logger.warn(u'load %s', fpath)
            cls.__lib = sbicif.load_lib(fpath)
        except:
            try:
                fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cdll', platform.system(), platform.machine(), libraryfile)
                cls.__logger.warn(u'load %s', fpath)
                cls.__lib = sbicif.load_lib(fpath)
            except:
                try:
                    fpath = os.path.join(os.getcwd(), libraryfile)
                    cls.__logger.warn(u'load %s', fpath)
                    cls.__lib = sbicif.load_lib(fpath)
                except:
                    try:
                        fpath = os.path.join(os.path.curdir, libraryfile)
                        cls.__logger.warn(u'load %s', fpath)
                        cls.__lib = sbicif.load_lib(fpath)
                    except:
                        fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), libraryfile)
                        cls.__logger.warn(u'load %s', fpath)
                        cls.__lib = sbicif.load_lib(fpath)
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

    @classmethod
    def finalize(cls):
        '''释放库
        '''
        if cls.__instance:
            del cls.__instance
            cls.__instance = None
        if cls.__lib:
            sbicif._c_fn_Release()
            cls.__lib = None

    @classmethod
    def isInitialized(cls):
        '''判断是否初始化

        :return: 是否已经初始化
        :rtype: bool
        '''
        return cls.__lib is not None

    @classmethod
    def instance(cls, username=None, password=None, extInfo=None):
        '''返回该类型的实例

        .. note:: 由于一个进程只能有一个实例，所以可用该方法返回目前的实例。
        '''
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
                if packInfo.srcUnitClientType == SMARTBUS_NODECLI_TYPE_IPSC:
                    try:
                        txt = to_str(bytestr, 'cp936')
                    except UnicodeDecodeError:
                        txt = to_str(bytestr, 'utf8')
                else:
                    txt = to_str(bytestr, inst.encoding)
                inst.onReceiveText(packInfo, txt)

    @classmethod
    def __invokeflow_ret_cb(cls, arg, local_clientid, head, projectid, invoke_id, ret, param):
        inst = cls.__instance
        if ret == 1:
            if callable(inst.onInvokeFlowRespond):
                packInfo = PackInfo(head)
                txt_projectid = to_str(projectid, 'cp936').strip('\x00')
                txt_param = to_str(param, 'cp936').strip('\x00').strip()
                if txt_param:
                    py_param = json.loads(txt_param)
                else:
                    py_param = None
                inst.onInvokeFlowRespond(packInfo, txt_projectid, invoke_id, py_param)
        elif ret == SMARTBUS_ERR_TIMEOUT:
            if callable(inst.onInvokeFlowTimeout):
                packInfo = PackInfo(head)
                txt_projectid = to_str(projectid, 'cp936').strip('\x00')
                inst.onInvokeFlowTimeout(packInfo, txt_projectid, invoke_id)
        else:
            if callable(inst.onInvokeFlowError):
                packInfo = PackInfo(head)
                txt_projectid = to_str(projectid, 'cp936').strip('\x00')
                inst.onInvokeFlowError(packInfo, txt_projectid, invoke_id, ret)

    @classmethod
    def __invokeflow_ack_cb(cls, arg, local_clientid, head, projectid, invoke_id, ack, msg):
        inst = cls.__instance
        if inst is not None:
            if hasattr(inst, 'onInvokeFlowAcknowledge'):
                packInfo = PackInfo(head)
                txt_projectid = to_str(projectid, 'cp936').strip('\x00')
                txt_msg = to_str(msg, 'cp936').strip('\x00')
                inst.onInvokeFlowAcknowledge(packInfo, txt_projectid, invoke_id, ack, txt_msg)

    @classmethod
    def __global_connect_cb(cls, arg, unitid, clientid, clienttype, accessunit, status, ext_info):
        if callable(cls.__onglobalconnect):
#             if sys.version_info[0] < 3:
#                 if cls.__instance:
#                     inst = cls.__instance
#                     cls.__onglobalconnect(inst, ord(unitid), ord(clientid), ord(clienttype), ord(accessunit), ord(status), to_str(ext_info, 'cp936'))
#             else:
#                 cls.__onglobalconnect(ord(unitid), ord(clientid), ord(clienttype), ord(accessunit), ord(status), to_str(ext_info, 'cp936'))
            cls.__onglobalconnect(ord(unitid), ord(clientid), ord(clienttype), ord(accessunit), ord(status), to_str(ext_info, 'cp936'))

    @classmethod
    def __trace_cb(cls, msg):
        cls.__logger.log(cls.__logging_option[1], to_str(msg, 'cp936'))

    @classmethod
    def __traceerr_cb(cls, msg):
        cls.__logger.log(cls.__logging_option[2], to_str(msg, 'cp936'))

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

    def onConnectSuccess(self, unitId):
        '''连接成功事件

        :param int unitId: 单元ID
        '''
        pass

    def onConnectFail(self, unitId, errno):
        '''连接失败事件

       :param int unitId: 单元ID
       :param int errno: 错误编码
        '''
        pass

    def onDisconnect(self):
        '''连接中断事件
        '''
        pass

    def onReceiveText(self, packInfo, txt):
        '''收到文本事件

        :param packInfo: 数据包信息
        :type packInfo: smartbus.PackInfo
        :param str txt: 收到的文本
        '''
        pass

    def onInvokeFlowAcknowledge(self, packInfo, project, invokeId, ack, msg):
        '''收到流程执行回执事件

        在调用流程之后，通过该回调函数类型获知流程调用是否成功

        :param packInfo: 数据包信息
        :type packInfo: smartbus.PackInfo
        :param str project: 流程项目ID
        :param int invokeId: 调用ID
        :param int ack: 流程调用是否成功。1表示成功，其它请参靠考误码
        :param str msg: 调用失败时的信息描述
        '''
        pass

    def onInvokeFlowRespond(self, packInfo, project, invokeId, result):
        '''收到流程返回数据事件

        通过类类型的回调函数，获取被调用流程的“子项目结束”节点的返回值列表

        :param packInfo: 数据包信息
        :type packInfo: smartbus.PackInfo
        :param str project: 流程项目ID
        :param int invokeId: 调用ID
        :param int result: 返回的数据。JSON数组格式
        '''
        pass

    def onInvokeFlowTimeout(self, packInfo, project, invokeId):
        '''流程返回超时事件

        :param packInfo: 数据包信息
        :type packInfo: smartbus.PackInfo
        :param str project: 流程项目ID
        :param int invokeId: 调用ID
        '''
        pass

    def onInvokeFlowError(self, packInfo, project, invokeId, errno):
        '''流程调用错误事件

        :param packInfo: 数据包信息
        :type packInfo: smartbus.PackInfo
        :param str project: 流程项目ID
        :param int invokeId: 调用ID
        :param int errno: 错误码
        '''
        pass

    def connect(self, username=None, password=None):
        '''连接服务器

        :param str username: 连接用户名
        :param str password: 连接密码
        :param str info: 自定义连接信息

        :exc: 如果连接失败，则抛出 :exc:`ConnectError` 异常
        '''
        result = sbicif._c_fn_CreateConnect(self._c_username, self._c_password, self.__c_extInfo)
        errors.check_restval(result)

    def send(self, cmd, cmdType, dstUnitId, dstClientId, dstClientType, data, encoding=None):
        '''发送数据

        :param cmd: 命令
        :param cmdType: 命令类型
        :param dstUnitId: 目标节点ID
        :param dstClientId: 目标客户端ID
        :param dstClientType: 目标客户端类型
        :param data: 待发送数据，可以是文本或者字节数组
        :param encoding: 文本的编码。默认为该对象的 :attr:`encoding` 属性
        '''
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

    def invokeFlow(self, server, process, project, flow, parameters=[], isNeedReturn=True, timeout=30):
        '''调用流程

        :param int server: IPSC流程服务所在节点
        :param int process: IPSC进程索引值
        :param str project: 流程项目名称
        :param str flow: 流程名称
        :param parameters: 流程传入参数
        :type parameters: 简单数据或者由简单数据组合成的int, float, str, bool , dict，或者它们的再组合数据类型。
        :param bool isNeedReturn: 是否需要流程返回值
        :param timeout: 等待流程返回超时值，单位为秒。
        :type timeout: int or float
        :return: 当需要等待流程返回值时，该返回值是 :func:`onInvokeFlowRespond` "流程返回事件"中对应的ID.
        :rtype: int
        '''
        c_server_unitid = c_int(server)
        c_processindex = c_int(process)
        c_project_id = c_char_p(to_bytes(project, 'cp936'))
        c_flowid = c_char_p(to_bytes(flow, 'cp936'))
        c_invoke_mode = c_int(0) if isNeedReturn else c_int(1)
        c_timeout = c_int(int(timeout * 1000))
        if parameters is None:
            parameters = []
        else:
            if isinstance(parameters, (int, float, str, bool , dict)):
                parameters = [parameters]
            else:
                parameters = list(parameters)
        c_in_valuelist = c_char_p(to_bytes(str(parameters), 'cp936'))
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
