# -*- coding: utf-8 -*-

"""smartbus 进程间通信客户端的Python接口类客户端类型

:author: 刘雪彦
:date: 2013-6-8
"""

from __future__ import absolute_import

import logging
from ctypes import create_string_buffer, string_at, byref, c_byte, c_int, c_void_p, c_char_p
import json

from . import _c_smartbus_ipccli_interface as sbicif
from .._c_smartbus import PackInfo, SMARTBUS_NODECLI_TYPE_IPSC, SMARTBUS_ERR_TIMEOUT
from ..utils import default_encoding, to_str, to_bytes
from .. import errors


class Client:
    """SmartBus IPC 客户端类

    这个类封装了 SmartBus IPC 客户端的一系列方法与事件
    """
    _lib = None
    _instance = None
    _logger = None
    _logging_option = True, logging.DEBUG, logging.ERROR
    _on_global_connect = None
    _c_fn_connection_cb = None
    _c_fn_receive_data_cb = None
    _c_fn_disconnect_cb = None
    _c_fn_invoke_flow_ret_cb = None
    _c_fn_global_connect_cb = None

    def __init__(self, user_name=None, password=None, ext_info=None, encoding=default_encoding):
        """构造函数

        :param str user_name: 验证用户名
        :param str password: 验证密码
        :param str ext_info: 附加信息
        :param str encoding: 收/发字符串时使用的编码。默认为 :attr:`smartbus.utils.default_encoding`
        """
        self._unit_id = None
        self._client_id = None
        self._user_name = user_name
        self._password = password
        self._ext_info = ext_info
        self.encoding = encoding
        self._c_username = to_bytes(self._user_name, self.encoding)
        self._c_password = to_bytes(self._password, self.encoding)
        self._c_ext_info = c_char_p(to_bytes(self._ext_info, self.encoding))
        if not Client._lib:
            raise errors.NotInitializedError()
        if Client._instance:
            raise errors.AlreadyExistsError()
        Client._instance = self

    def __del__(self):
        Client._instance = None

    @classmethod
    def initialize(cls, client_id, client_type, on_global_connect=None, library_file='', logging_option=None):
        """初始化

        这是一个类方法。调用其他方法前，必须首先使用这个方法初始化库。

        :param client_id: 客户端ID。在同一个节点中，ID必须唯一。不得小于等于16
        :param client_type: 客户端类型。
        :param on_global_connect:
        :param library_file:

        ..note:: 不会自动搜索，要保证so/dll在搜索路径中！
        """
        cls._client_id = client_id
        cls._client_type = client_type
        cls._logging_option = logging_option or cls._logging_option
        cls._logger = logging.getLogger('{}.{}'.format(
            cls.__module__, cls.__qualname__ if hasattr(cls, '__qualname__') else cls.__name__))
        cls._logger.info('initialize')
        if cls._lib:
            raise errors.AlreadyInitializedError()
        if not library_file:
            library_file = sbicif.lib_filename
        cls._logger.warn(u'load %s', library_file)
        cls._lib = sbicif.load_lib(library_file)
        errors.check_restval(sbicif._c_fn_Init(client_type, client_id))
        cls._c_fn_connection_cb = sbicif._c_fntyp_connection_cb(cls._connection_cb)
        cls._c_fn_receive_data_cb = sbicif._c_fntyp_recvdata_cb(cls._receive_data_cb)
        cls._c_fn_disconnect_cb = sbicif._c_fntyp_disconnect_cb(cls._disconnect_cb)
        cls._c_fn_invoke_flow_ret_cb = sbicif._c_fntyp_invokeflow_ret_cb(cls._invoke_flow_ret_cb)
        cls._c_fn_invoke_flow_ack_cb = sbicif._c_fntyp_invokeflow_ret_cb(cls._invoke_flow_ack_cb)
        cls._c_fn_global_connect_cb = sbicif._c_fntyp_global_connect_cb(cls._global_connect_cb)
        cls._on_global_connect = on_global_connect
        sbicif._c_fn_SetCallBackFn(
            cls._c_fn_connection_cb,
            cls._c_fn_receive_data_cb,
            cls._c_fn_disconnect_cb,
            cls._c_fn_invoke_flow_ret_cb,
            cls._c_fn_global_connect_cb,
            c_void_p(None)
        )
        sbicif._c_fn_SetCallBackFnEx(c_char_p(b'smartbus_invokeflow_ack_cb'), cls._c_fn_invoke_flow_ack_cb)
        if logging_option[0]:
            cls._c_fn_trace_cb = sbicif._c_fntyp_trace_str_cb(cls._trace_cb)
            cls._c_fn_trace_err_cb = sbicif._c_fntyp_trace_str_cb(cls._trace_err_cb)
            sbicif._c_fn_SetTraceStr(cls._c_fn_trace_cb, cls._c_fn_trace_err_cb)

    @classmethod
    def finalize(cls):
        """释放库
        """
        if cls._instance:
            del cls._instance
            cls._instance = None
        if cls._lib:
            sbicif._c_fn_Release()
            cls._lib = None

    @classmethod
    def is_initialized(cls):
        """判断是否初始化

        :return: 是否已经初始化
        :rtype: bool
        """
        return cls._lib is not None

    @classmethod
    def instance(cls, user_name=None, password=None, ext_info=None):
        """返回该类型的实例

        .. note:: 由于一个进程只能有一个实例，所以可用该方法返回目前的实例。
        """
        if cls._instance:
            return cls._instance
        else:
            return Client(user_name, password, ext_info)

    @classmethod
    def _connection_cb(cls, arg, local_client_id, access_point_unit_id, ack):
        inst = cls._instance
        inst._unit_id = access_point_unit_id
        inst._client_id = local_client_id
        if ack == 0:  # 连接成功
            if callable(inst.on_connect_success):
                inst.on_connect_success(access_point_unit_id)
        else:  # 连接失败
            if callable(inst.on_connect_fail):
                inst.on_connect_fail(access_point_unit_id, ack)

    @classmethod
    def _disconnect_cb(cls, param, local_client_id):
        inst = cls._instance
        if callable(inst.on_disconnect):
            inst.on_disconnect()

    @classmethod
    def _receive_data_cb(cls, param, local_client_id, head, data, size):
        inst = cls._instance
        if callable(inst.on_receive_text):
            pack_info = PackInfo(head)
            txt = None
            if data:
                bytestr = string_at(data, size)
                bytestr = bytestr.strip(b'\x00')
                if pack_info.src_unit_client_type == SMARTBUS_NODECLI_TYPE_IPSC:
                    try:
                        txt = to_str(bytestr, 'cp936')
                    except UnicodeDecodeError:
                        txt = to_str(bytestr, 'utf8')
                else:
                    txt = to_str(bytestr, inst.encoding)
                inst.on_receive_text(pack_info, txt)

    @classmethod
    def _invoke_flow_ret_cb(cls, arg, local_client_id, head, project_id, invoke_id, ret, param):
        inst = cls._instance
        if ret == 1:
            if callable(inst.on_flow_resp):
                pack_info = PackInfo(head)
                txt_project_id = to_str(project_id, 'cp936').strip('\x00')
                txt_param = to_str(param, 'cp936').strip('\x00').strip()
                if txt_param:
                    py_param = json.loads(txt_param)
                else:
                    py_param = None
                inst.on_flow_resp(pack_info, txt_project_id, invoke_id, py_param)
        elif ret == SMARTBUS_ERR_TIMEOUT:
            if callable(inst.on_flow_timeout):
                pack_info = PackInfo(head)
                txt_project_id = to_str(project_id, 'cp936').strip('\x00')
                inst.on_flow_timeout(pack_info, txt_project_id, invoke_id)
        else:
            if callable(inst.on_flow_error):
                pack_info = PackInfo(head)
                txt_project_id = to_str(project_id, 'cp936').strip('\x00')
                inst.on_flow_error(pack_info, txt_project_id, invoke_id, ret)

    @classmethod
    def _invoke_flow_ack_cb(cls, arg, local_client_id, head, project_id, invoke_id, ack, msg):
        inst = cls._instance
        if inst is not None:
            if hasattr(inst, 'on_flow_ack'):
                pack_info = PackInfo(head)
                txt_project_id = to_str(project_id, 'cp936').strip('\x00')
                txt_msg = to_str(msg, 'cp936').strip('\x00')
                inst.on_flow_ack(pack_info, txt_project_id, invoke_id, ack, txt_msg)

    @classmethod
    def _global_connect_cb(cls, arg, unit_id, client_id, client_type, access_unit, status, ext_info):
        if callable(cls._on_global_connect):
            cls._on_global_connect(
                ord(unit_id), ord(client_id), ord(client_type), ord(access_unit), ord(status),
                to_str(ext_info, 'cp936')
            )

    @classmethod
    def _trace_cb(cls, msg):
        cls._logger.log(cls._logging_option[1], to_str(msg, 'cp936'))

    @classmethod
    def _trace_err_cb(cls, msg):
        cls._logger.log(cls._logging_option[2], to_str(msg, 'cp936'))

    @property
    def library(self):
        return self._lib

    def get_unit_id(self):
        return self._unit_id

    unit_id = property(get_unit_id)

    def get_client_id(self):
        return self._client_id

    client_id = property(get_client_id)

    def get_client_type(self):
        return self._client_type

    client_type = property(get_client_type)

    def get_addr_expr(self):
        return '{} {} {}'.format(self.unit_id, self.client_id, self.client_type)

    addr_expr = property(get_addr_expr)

    def on_connect_success(self, unit_id):
        """连接成功事件

        :param int unit_id: 单元ID
        """
        pass

    def on_connect_fail(self, unitId, errno):
        """连接失败事件

       :param int unitId: 单元ID
       :param int errno: 错误编码
        """
        pass

    def on_disconnect(self):
        """连接中断事件
        """
        pass

    def on_receive_text(self, pack_info, txt):
        """收到文本事件

        :param smartbus.PackInfo pack_info: 数据包信息
        :param str txt: 收到的文本
        """
        pass

    def on_flow_ack(self, pack_info, project, invoke_id, ack, msg):
        """收到流程执行回执事件

        在调用流程之后，通过该回调函数类型获知流程调用是否成功

        :param smartbus.PackInfo pack_info: 数据包信息
        :param str project: 流程项目ID
        :param int invoke_id: 调用ID
        :param int ack: 流程调用是否成功。1表示成功，其它请参靠考误码
        :param str msg: 调用失败时的信息描述
        """
        pass

    def on_flow_resp(self, pack_info, project, invoke_id, result):
        """收到流程返回数据事件

        通过类类型的回调函数，获取被调用流程的“子项目结束”节点的返回值列表

        :param smartbus.PackInfo pack_info: 数据包信息
        :param str project: 流程项目ID
        :param int invoke_id: 调用ID
        :param int result: 返回的数据。JSON数组格式
        """
        pass

    def on_flow_timeout(self, pack_info, project, invoke_id):
        """流程返回超时事件

        :param smartbus.PackInfo pack_info: 数据包信息
        :param str project: 流程项目ID
        :param int invoke_id: 调用ID
        """
        pass

    def on_flow_error(self, pack_info, project, invoke_id, error_code):
        """流程调用错误事件

        :param smartbus.PackInfo pack_info: 数据包信息
        :param str project: 流程项目ID
        :param int invoke_id: 调用ID
        :param int error_code: 错误码
        """
        pass

    def connect(self):
        """连接服务器

        :exc ConnectError: 如果连接失败，则抛出 :exc:`ConnectError` 异常
        """
        result = sbicif._c_fn_CreateConnect(self._c_username, self._c_password, self._c_ext_info)
        errors.check_restval(result)

    def send(self, cmd, cmd_type, dst_unit_id, dst_client_id, dst_client_type, data, encoding=None):
        """发送数据

        :param int cmd: 命令
        :param int cmd_type: 命令类型
        :param int dst_unit_id: 目标节点ID
        :param int dst_client_id: 目标客户端ID
        :param int dst_client_type: 目标客户端类型
        :param str data: 待发送数据，可以是文本或者字节数组
        :param str encoding: 文本的编码。默认为该对象的 :attr:`encoding` 属性
        """
        data = to_bytes(data, encoding if encoding else self.encoding)
        data_pc = create_string_buffer(data) if data else None
        data_sz = len(data_pc) if data_pc else 0
        result = sbicif._c_fn_SendData(
            c_byte(cmd),
            c_byte(cmd_type),
            c_int(dst_unit_id),
            c_int(dst_client_id),
            c_int(dst_client_type),
            byref(data_pc),
            c_int(data_sz)
        )
        errors.check_restval(result)

    def startup_flow(self, server, process, project, flow, parameters=None, is_resp=True, timeout=30):
        """启动流程

        :param int server: IPSC流程服务所在节点
        :param int process: IPSC进程索引值，同时也是该IPSC进程的 smartbus client-id
        :param str project: 流程项目名称
        :param str flow: 流程名称
        :param list parameters: 流程传入参数。
                                简单数据或者由简单数据组合成的int, float, str, bool , dict，或者它们的再组合数据类型。
        :param bool is_resp: 是否需要流程返回值
        :param timeout: 等待流程返回超时值，单位为秒。
        :type timeout: int or float
        :return: 当需要等待流程返回值时，该返回值是 :func:`on_flow_resp` "流程返回事件"中对应的ID.
        :rtype: int
        """
        c_server_unit_id = c_int(server)
        c_process_index = c_int(process)
        c_project_id = c_char_p(to_bytes(project, 'cp936'))
        c_flow_id = c_char_p(to_bytes(flow, 'cp936'))
        c_invoke_mode = c_int(0) if is_resp else c_int(1)
        c_timeout = c_int(int(timeout * 1000))
        if parameters is None:
            parameters = []
        else:
            if isinstance(parameters, (int, float, str, bool, dict)):
                parameters = [parameters]
            else:
                parameters = list(parameters)
        c_in_value_list = c_char_p(to_bytes(str(parameters), 'cp936'))
        result = sbicif._c_fn_RemoteInvokeFlow(
            c_server_unit_id,
            c_process_index,
            c_project_id,
            c_flow_id,
            c_invoke_mode,
            c_timeout,
            c_in_value_list
        )
        if result < 0:
            errors.check_restval(result)
        elif result == 0:
            raise errors.InvokeFlowIdError()
        return result

    def ping(self, dst_unit_id, dst_client_id, dst_client_type, data, encoding=None):
        """发送PING命令

        :param int dst_unit_id: 目标的smartbus单元ID
        :param int dst_client_id: 目标的smartbus客户端ID
        :param int dst_client_type: 目标的smartbus客户端类型
        :param str data: 要发送的数据
        :param str encoding: 数据的编码。 默认值为None，表示使用 :attr:`smartbus.ipcclient.client.Client.encoding`
        """
        data = to_bytes(data, encoding if encoding else self.encoding)
        data_pc = create_string_buffer(data) if data else None
        data_sz = len(data_pc) if data_pc else 0
        result = sbicif._c_fn_SendPing(
            c_int(dst_unit_id),
            c_int(dst_client_id),
            c_int(dst_client_type),
            byref(data_pc),
            c_int(data_sz)
        )
        errors.check_restval(result)

    def send_notify(self, server, process, project, title, mode, expires, param):
        """发送通知消息

        :param int server:  目标IPSC服务器smartbus单元ID
        :param int process: IPSC进程ID，同时也是该IPSC进程的 smartbus client-id
        :param str project: 流程项目ID
        :param str title:   通知的标示
        :param int mode:    调用模式。目前无意义，一律使用0
        :param float expires: 消息有效期。单位秒
        :param str param:   消息数据
        :return: > 0 invoke_id，调用ID。< 0 表示错误。
        :rtype: int
        """
        c_server_unit_id = c_int(server)
        c_process_index = c_int(process)
        c_project_id = c_char_p(to_bytes(project, 'cp936'))
        c_title = c_char_p(to_bytes(title, 'cp936'))
        c_mode = c_int(0) if mode else c_int(1)
        c_expires = c_int(int(expires * 1000))
        c_param = c_char_p(to_bytes(param, 'cp936'))
        result = sbicif._c_fn_SendNotify(
            c_server_unit_id,
            c_process_index,
            c_project_id,
            c_title,
            c_mode,
            c_expires,
            c_param
        )
        if result > 0:
            return result
        elif result < 0:
            errors.check_restval(result)
        else:
            raise ValueError('SendNotify C API returns zero')
