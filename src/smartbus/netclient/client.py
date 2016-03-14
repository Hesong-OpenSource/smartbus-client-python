# -*- coding: utf-8 -*-

"""smartbus 网络通信客户端的Python接口类客户端类型

:author: 刘雪彦
:date: 2013-6-8
"""

from __future__ import absolute_import

import logging
from ctypes import create_string_buffer, string_at, byref, c_byte, c_int, c_long, c_ushort, c_void_p, c_char_p
import json

from . import _c_smartbus_netcli_interface as sbncif
from .._c_smartbus import PackInfo, SMARTBUS_ERR_OK, SMARTBUS_NODECLI_TYPE_IPSC, SMARTBUS_ERR_TIMEOUT
from ..utils import default_encoding, to_str, to_bytes
from .. import errors

__all__ = ['Client']


class Client:
    """SmartBus Network 客户端类

    这个类封装了 SmartBus Network 客户端的一系列方法与事件
    """
    _instances = {}
    _lib = None
    _unit_id = None
    _logger = None
    _logging_option = True, logging.DEBUG, logging.ERROR
    _on_global_connect = None
    _c_fn_trace_cb = None
    _c_fn_trace_err_cb = None
    _c_fn_connection_cb = None
    _c_fn_receive_data_cb = None
    _c_fn_disconnect_cb = None
    _c_fn_invoke_flow_ret_cb = None
    _c_fn_global_connect_cb = None

    def __init__(self, local_client_id, local_client_type, master_host, master_port, slaver_host=None,
                 slaver_port=0xffff, author_usr=None, author_pwd=None, ext_info=None, encoding=default_encoding):
        """构造函数

        :param local_client_id:客户端的ID
        :param local_client_type:客户端的类型标志
        :param master_host:客户端所要连接的主服务器
        :param master_port:客户端所要连接的主服务器端口
        :param slaver_host:客户端所要连接的从服务器
        :param slaver_port:客户端所要连接的从服务器端口
        :param author_usr:登录名
        :param author_pwd:密码
        :param ext_info:附加信息
        :param encoding:收/发字符串时使用的编码。默认为 :data:`smartbus.utils.default_encoding`
        """
        if not Client.is_initialized():
            raise errors.NotInitializedError()
        if local_client_id in Client._instances:
            raise errors.AlreadyExistsError()
        Client._instances[local_client_id] = self
        self._local_client_id = local_client_id
        self._local_client_type = local_client_type
        self._master_host = master_host
        self._master_port = master_port
        self._slaver_host = slaver_host
        self._slaver_port = slaver_port
        self._author_usr = author_usr
        self._author_pwd = author_pwd
        self._ext_info = ext_info
        self._encoding = encoding
        self._c_local_client_id = c_byte(self._local_client_id)
        self._c_local_client_type = c_long(self._local_client_type)
        self._c_master_host = c_char_p(
            to_bytes(self._master_host, self.encoding))
        self._c_master_port = c_ushort(self._master_port)
        self._c_slaver_host = c_char_p(
            to_bytes(self._slaver_host, self.encoding))
        self._c_slaver_port = c_ushort(self._slaver_port)
        self._c_author_usr = c_char_p(
            to_bytes(self._author_usr, self.encoding))
        self._c_author_pwd = c_char_p(
            to_bytes(self._author_pwd, self.encoding))
        self._c_ext_info = c_char_p(to_bytes(self._ext_info, self.encoding))

    @classmethod
    def initialize(cls, unit_id, on_global_connect=None, library_file='', logging_option=None):
        """初始化

        调用其他方法前，必须首先初始化库

        :param unit_id:单元ID。在所连接到的SmartBus服务器上，每个客户端进程的单元ID都必须是全局唯一的。
        :param on_global_connect:全局连接事件回调函数
        :param library_file:库文件。如果不指定该参数，则加载时，会搜索库文件。请保证so/dll在搜索路径中！
        :param logging_option:
        """
        if cls._unit_id is not None:
            raise errors.AlreadyInitializedError()
        # if not isinstance(unit_id, int):
        #            raise TypeError('The argument "unit" should be an integer')
        cls._logging_option = logging_option or cls._logging_option
        cls._logger = logging.getLogger(
            '{}.{}'.format(cls.__module__, cls.__qualname__ if hasattr(cls, '__qualname__') else cls.__name__))
        cls._logger.info('initialize')
        if not library_file:
            library_file = sbncif.lib_filename
        cls._logger.warn(u'load %s', library_file)
        cls._lib = sbncif.load_lib(library_file)
        errors.check_restval(sbncif._c_fn_Init(unit_id))
        cls._unit_id = unit_id
        cls._on_global_connect = on_global_connect
        cls._c_fn_connection_cb = sbncif._c_fntyp_connection_cb(cls._connection_cb)
        cls._c_fn_receive_data_cb = sbncif._c_fntyp_recvdata_cb(cls._receive_data_cb)
        cls._c_fn_disconnect_cb = sbncif._c_fntyp_disconnect_cb(cls._disconnect_cb)
        cls._c_fn_invoke_flow_ret_cb = sbncif._c_fntyp_invokeflow_ret_cb(cls._invoke_flow_ret_cb)
        cls._c_fn_invoke_flow_ack_cb = sbncif._c_fntyp_invokeflow_ret_cb(cls._invoke_flow_ack_cb)
        cls._c_fn_global_connect_cb = sbncif._c_fntyp_global_connect_cb(cls._global_connect_cb)
        sbncif._c_fn_SetCallBackFn(
            cls._c_fn_connection_cb,
            cls._c_fn_receive_data_cb,
            cls._c_fn_disconnect_cb,
            cls._c_fn_invoke_flow_ret_cb,
            cls._c_fn_global_connect_cb,
            c_void_p(None)
        )
        sbncif._c_fn_SetCallBackFnEx(c_char_p(b'smartbus_invokeflow_ack_cb'), cls._c_fn_invoke_flow_ack_cb)
        if logging_option[0]:
            cls._c_fn_trace_cb = sbncif._c_fntyp_trace_str_cb(cls._trace_cb)
            cls._c_fn_trace_err_cb = sbncif._c_fntyp_trace_str_cb(cls._trace_err_cb)
            sbncif._c_fn_SetTraceStr(cls._c_fn_trace_cb, cls._c_fn_trace_err_cb)

    @classmethod
    def finalize(cls):
        """释放库
        """
        cls._instances.clear()
        if cls._unit_id is not None:
            sbncif._c_fn_Release()
            cls._unit_id = None

    @classmethod
    def is_initialized(cls):
        return cls._unit_id is not None

    @classmethod
    def get_unit_id(cls):
        return cls._unit_id

    @classmethod
    def _connection_cb(cls, arg, local_client_id, access_point_unit_id, ack):
        inst = cls._instances.get(local_client_id, None)
        if inst is not None:
            inst._unit_id = access_point_unit_id
            if ack == SMARTBUS_ERR_OK:  # 连接成功
                if hasattr(inst, 'on_connect_success'):
                    inst.on_connect_success(access_point_unit_id)
            else:  # 连接失败
                if hasattr(inst, 'on_connect_fail'):
                    inst.on_connect_fail(access_point_unit_id, ack)

    @classmethod
    def _disconnect_cb(cls, param, local_client_id):
        inst = cls._instances.get(local_client_id, None)
        if inst is not None:
            if hasattr(inst, 'on_disconnect'):
                inst.onDisconnect()

    # TODO: 广播的处理
    @classmethod
    def _receive_data_cb(cls, param, local_client_id, head, data, size):
        inst = cls._instances.get(local_client_id, None)
        if inst is not None:
            if hasattr(inst, 'on_receive_text'):
                pack_info = PackInfo(head)
                txt = None
                if data:
                    byte_str = string_at(data, size)
                    byte_str = byte_str.strip(b'\x00')
                    if pack_info.src_unit_client_type == SMARTBUS_NODECLI_TYPE_IPSC:
                        try:
                            txt = to_str(byte_str, 'cp936')
                        except UnicodeDecodeError:
                            txt = to_str(byte_str, 'utf8')
                    else:
                        txt = to_str(byte_str, inst.encoding)
                inst.onReceiveText(pack_info, txt)

    @classmethod
    def _invoke_flow_ret_cb(cls, arg, local_client_id, head, project_id, invoke_id, ret, param):
        inst = cls._instances.get(local_client_id, None)
        if inst is not None:
            if ret == 1:
                if hasattr(inst, 'on_flow_resp'):
                    pack_info = PackInfo(head)
                    txt_project_id = to_str(project_id, 'cp936').strip('\x00')
                    txt_param = to_str(param, 'cp936').strip('\x00').strip()
                    if txt_param:
                        py_param = json.loads(txt_param)
                    else:
                        py_param = None
                    inst.on_flow_resp(pack_info, txt_project_id, invoke_id, py_param)
            elif ret == SMARTBUS_ERR_TIMEOUT:
                if hasattr(inst, 'on_flow_timeout'):
                    pack_info = PackInfo(head)
                    txt_project_id = to_str(project_id, 'cp936').strip('\x00')
                    inst.on_flow_timeout(pack_info, txt_project_id, invoke_id)
            else:
                if hasattr(inst, 'on_flow_error'):
                    pack_info = PackInfo(head)
                    txt_project_id = to_str(project_id, 'cp936').strip('\x00')
                    inst.on_flow_error(pack_info, txt_project_id, invoke_id, ret)

    @classmethod
    def _invoke_flow_ack_cb(cls, arg, local_client_id, head, project_id, invoke_id, ack, msg):
        inst = cls._instances.get(local_client_id, None)
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
    def local_client_id(self):
        """客户端ID"""
        return self._local_client_id

    @property
    def local_client_type(self):
        """客户端类型"""
        return self._local_client_type

    @property
    def unit_id(self):
        """客户端的单元ID"""
        return self._unit_id

    @property
    def addr_expr(self):
        return '{} {} {}'.format(self._unit_id, self._local_client_id, self._local_client_type)

    @property
    def master_host(self):
        """SmartBus 服务主机名
        """
        return self._master_host

    @property
    def master_port(self):
        """SmartBus 服务端口"""
        return self._master_port

    @property
    def slaver_host(self):
        """SmartBus 从服务主机名"""
        return self._slaver_host

    @property
    def slaver_port(self):
        """SmartBus 从服务端口"""
        return self._slaver_port

    @property
    def author_usr(self):
        """登录名
        """
        return self._author_usr

    @property
    def author_pwd(self):
        """密码
        """
        return self._author_pwd

    @property
    def ext_info(self):
        """连接附加信息"""
        return self._ext_info

    @property
    def encoding(self):
        """收/发字符串时使用的编码。默认为 utils.default_encoding。
        """
        return self._encoding

    def on_connect_success(self, unitId):
        """连接成功事件

        :param int unitId: 单元ID
        """
        pass

    def on_connect_fail(self, unitId, errno):
        """连接失败事件

       :param int unitId: 单元ID
       :param int errno: 错误码
       """
        pass

    def on_disconnect(self):
        """连接中断事件
        """
        pass

    def on_receive_text(self, pack_info, txt):
        """收到文本事件

        :param pack_info: 数据包信息
        :type pack_info: smartbus.PackInfo
        :param str txt: 收到的文本
        """
        pass

    def on_flow_ack(self, pack_info, project, invoke_id, ack, msg):
        """收到流程执行回执事件

        在调用流程之后，通过该回调函数类型获知流程调用是否成功

        :param pack_info: 数据包信息
        :type pack_info: smartbus.PackInfo
        :param str project: 流程项目ID
        :param int invoke_id: 调用ID
        :param int ack: 流程调用是否成功。1表示成功，其它请参靠考误码
        :param str msg: 调用失败时的信息描述
        """
        pass

    def on_flow_resp(self, pack_info, project, invoke_id, result):
        """收到流程返回数据事件

        通过类类型的回调函数，获取被调用流程的“子项目结束”节点的返回值列表

        :param pack_info: 数据包信息
        :type pack_info: smartbus.PackInfo
        :param str project: 流程项目ID
        :param int invoke_id: 调用ID
        :param int result: 返回的数据。JSON数组格式
        """
        pass

    def on_flow_timeout(self, pack_info, project, invoke_id):
        """流程返回超时事件

        :param pack_info: 数据包信息
        :type pack_info: smartbus.PackInfo
        :param str project: 流程项目ID
        :param int invoke_id: 调用ID
        """
        pass

    def on_flow_error(self, pack_info, project, invoke_id, error_code):
        """流程调用错误事件

        :param pack_info: 数据包信息
        :type pack_info: smartbus.PackInfo
        :param str project: 流程项目ID
        :param int invoke_id: 调用ID
        :param int error_code: 错误码
        """
        pass

    def dispose(self):
        """释放客户端
        """
        cls = type(self)
        cls._instances.pop(self._local_client_id, None)

    def connect(self):
        """连接到服务器

        :exc: 如果连接失败，则抛出 :exc:`ConnectError` 异常
        """
        result = sbncif._c_fn_CreateConnect(
            self._c_local_client_id,
            self._c_local_client_type,
            self._c_master_host,
            self._c_master_port,
            self._c_slaver_host,
            self._c_slaver_port,
            self._c_author_usr,
            self._c_author_pwd,
            self._c_ext_info
        )
        errors.check_restval(result)

    def send(self, cmd, cmd_type, dst_unit_id, dst_client_id, dst_client_type, data, encoding=None):
        """发送数据

        :param cmd: 命令
        :param cmd_type: 命令类型
        :param dst_unit_id: 目标节点ID
        :param dst_client_id: 目标客户端ID
        :param dst_client_type: 目标客户端类型
        :param data: 待发送数据，可以是文本或者字节数组
        :param encoding: 文本的编码。默认为该对象的 :attr:`encoding` 属性
        """
        data = to_bytes(data, encoding if encoding else self.encoding)
        data_pc = create_string_buffer(data) if data else None
        data_sz = len(data_pc) if data_pc else 0
        result = sbncif._c_fn_SendData(
            self._c_local_client_id,
            c_byte(cmd),
            c_byte(cmd_type),
            c_int(dst_unit_id),
            c_int(dst_client_id),
            c_int(dst_client_type),
            byref(data_pc),
            c_int(data_sz)
        )
        errors.check_restval(result)

    def startup_flow(self, server, process, project, flow, parameters=[], is_resp=True, timeout=30):
        """启动流程

        :param int server: IPSC流程服务所在节点
        :param int process: IPSC进程索引值，同时也是该IPSC进程的 smartbus client-id
        :param str project: 流程项目名称
        :param str flow: 流程名称
        :param parameters: 流程传入参数
        :type parameters: 简单数据或者由简单数据组合成的int, float, str, bool , dict，或者它们的再组合数据类型。
        :param bool is_resp: 是否需要流程返回值。如需要，将再返回后触发回调函数 :meth:`on_flow_resp`
        :param timeout: 等待流程返回超时值，单位为秒。
        :type timeout: int or float
        :return: 当需要等待流程返回值时，该返回值是 :meth:`on_flow_resp` "流程返回事件"中对应的ID.
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
        result = sbncif._c_fn_RemoteInvokeFlow(
            self._c_local_client_id,
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
        :param str encoding: 数据的编码。 默认值为None，表示使用 :attr:`smartbus.netlient.client.Client.encoding`
        """
        data = to_bytes(data, encoding if encoding else self.encoding)
        data_pc = create_string_buffer(data) if data else None
        data_sz = len(data_pc) if data_pc else 0
        result = sbncif._c_fn_SendPing(
            self._c_local_client_id,
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
        :param str project: 流程项目ID。None或者空表示不指明特定流程
        :param str title:   通知的标示
        :param int mode:    调用模式。目前无意义，一律使用0
        :param expires: 消息有效期。单位秒
        :type expires: int, float
        :param str param:   消息数据
        :return: > 0 invoke_id，调用ID。< 0 表示错误。
        :rtype: int
        """
        c_server_unitid = c_int(server)
        c_processindex = c_int(process)
        c_project_id = c_char_p(to_bytes(project, 'cp936'))
        c_title = c_char_p(to_bytes(title, 'cp936'))
        c_mode = c_int(0) if mode else c_int(1)
        c_expires = c_int(int(expires * 1000))
        c_param = c_char_p(to_bytes(param, 'cp936'))
        result = sbncif._c_fn_SendNotify(
            self._c_local_client_id,
            c_server_unitid,
            c_processindex,
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
