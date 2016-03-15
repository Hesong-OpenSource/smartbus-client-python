# -*- coding: utf-8 -*-

"""
面向对象样式的 IPC 客户端 API 的 Python 封装
"""

from __future__ import absolute_import

from ctypes import CDLL, string_at, c_void_p, c_char_p, c_int, c_byte, c_size_t
from ctypes.util import find_library
from concurrent.futures import ThreadPoolExecutor
import json

from ._c.ipc import *
from .errors import check
from .head import *
from .utils import *

__all__ = ['Client']


class Client(LoggerMixin):
    """IPC 客户端"""

    _instance = None  #: Singleton Client instance

    def __init__(self, client_id, client_type, lib_path='', event_executor=None):
        """
        :param int client_id:
        :param int client_type:
        :param str lib_path: SO/DLL 文件路径名。
            默认值是 `None` : 将按照 :data:`DLL_NAME` 查找库文件，需确保库文件在 Python 运行时的搜索路径中。
        :param ThreadPoolExecutor event_executor: 事件执行器。在此执行器中回调事件执行函数。
            默认执行器的线程池数量是 `1`

        加载 `Smartbus IPC` 客户端 so/dll 到这个 Python 包, 并进行初始化。
        """
        # Load DLL/SO
        self.logger.info('__init__: >>> lib_path=%s', lib_path)
        if Client._instance:
            raise RuntimeError('Client already constructed.')
        if self._lib:
            raise RuntimeError('library already loaded')
        if not lib_path:
            self.logger.debug('__init__: find_library "%s"', DLL_NAME)
            lib_path = find_library(DLL_NAME)
            if not lib_path:
                raise RuntimeError('Failed to find library {}'.format(DLL_NAME))
        self.logger.debug('__init__: CDLL %s', lib_path)
        self._lib = CDLL(lib_path)
        if not self._lib:
            raise RuntimeError('Failed to load library {}'.format(lib_path))
        self.logger.debug('__init__: %s', self._lib)
        # Bind C API function to static API Class
        for func_cls in get_function_declarations():
            self.logger.debug('__init__: bind function %s', func_cls)
            func_cls.bind(self._lib)
        # C API: init
        self.logger.debug('__init__: Init')
        ret = Init.c_func(int(client_type), int(client_id))
        check(ret)
        self._client_id = client_id
        self._client_type = client_type
        # C API: SetCallBackFn
        self.logger.debug('__init__: SetCallBackFn')
        SetCallBackFn.c_func(
            fntyp_connection_cb(self._cb_cnx),
            fntyp_recvdata_cb(self._cb_rcv),
            fntyp_disconnect_cb(self._cb_dnx),
            fntyp_invokeflow_ret_cb(self._cb_flow_ret),
            fntyp_global_connect_cb(self._cb_g_cnx),
            None
        )
        # C API: SetCallBackFnEx
        self.logger.debug('__init__: SetTraceStr')
        SetTraceStr.c_func(
            fntyp_trace_str_cb(self._cb_trace),
            fntyp_trace_str_cb(self._cb_trace_err)
        )
        # C API: SetCallBackFnEx
        self.logger.debug('__init__: SetCallBackFnEx')
        SetCallBackFnEx.c_func(c_char_p(b'smartbus_invokeflow_ack_cb'), fntyp_invokeflow_ack_cb(self._cb_flow_ack))
        # Load and init OK!!!
        # Other field
        self._unit_id = None
        self._connected = False
        if not event_executor:
            event_executor = ThreadPoolExecutor(max_workers=1)
        self._event_executor = event_executor
        # Over
        self.logger.info('__init__: <<<')

    def __del__(self):
        self.dispose()

    def _cb_cnx(self, arg, local_client_id, access_point_unit_id, ack):
        """客户端连接成功回调函数类型

        :param c_void_p arg: 自定义数据
        :param c_byte local_client_id: 连接成功的本地 ClientId
        :param c_int access_point_unit_id: int 连接点的 UnitID
        :param c_int ack: int 连接注册结果： 0 建立连接成功、< 0 连接失败
        """
        self._connected = int(ack) == 0
        if self._connected:
            # 连接成功
            self._client_id = int(local_client_id)
            self._unit_id = int(access_point_unit_id)
            self._event_executor.submit(self.on_connect)
        else:
            # 连接失败
            self._client_id = int(local_client_id)
            self._event_executor.submit(self.on_connect_fail)

    def _cb_rcv(self, param, local_client_id, head, data, size):
        """接收数据回调函数类型

        :param c_void_p param: 自定义数据
        :param c_byte local_client_id: 收到数据的的本地 ClientId
        :param PPacketHeader head: 数据包头
        :param c_void_p data: 数据包体
        :param c_size_t size: 包体字节长度
        """
        self.logger.debug('_cb_rcv: param=%s, local_client_id=%s, head=%s, data=%s, size=%s',
                          param, local_client_id, head, data, size)
        self._event_executor.submit(self.on_data, Head(head), string_at(data, size.value) if data else None)

    def _cb_dnx(self, param, local_client_id):
        """客户端连接断开回调函数类型

        :param c_void_p param: 自定义数据
        :param c_byte local_client_id: 连接断开的本地 ClientId
        """
        self.logger.debug('_cb_dnx: param=%s, local_client_id=%s',
                          param, local_client_id)
        self._connected = False
        self._client_id = int(local_client_id)
        self._event_executor.submit(self.on_disconnect)

    def _cb_flow_ret(self, arg, local_client_id, head, project_id, invoke_id, ret, param):
        """调用流程结果返回回调函数类型

        :param c_void_p arg: 自定义数据
        :param c_byte local_client_id: 本地 Client ID
        :param PPacketHeader head: 消息头
        :param c_char_p project_id: Project ID
        :param c_int invoke_id: 调用ID
        :param c_int ret: 返回值。1表示正常返回，-25表示超时，小于1表示错误,其它请见错误码
        :param c_char_p param: 结果参数串, 采用 JSON Array 格式

        通过类类型的回调函数，获取被调用流程的“子项目结束”节点的返回值列表
        """
        self.logger.debug(
            '_cb_flow_ret: arg=%s, local_client_id=%s, head=%s, project_id=%s, invoke_id=%s, ret=%s, param=%s',
            arg, local_client_id, head, project_id, invoke_id, ret, param)
        _head = Head(head)
        _project_id = b2s(string_at(project_id).strip(b'\x00'), 'cp936').strip()
        _invoke_id = invoke_id.value
        _status_code = ret.value
        if _status_code == 1:
            py_params = []
            if param:
                _params = b2s(string_at(param).strip(b'\x00'), 'cp936').strip()
                if _params:
                    py_params = json.loads(_params)
            self._event_executor.submit(self.on_flow_resp, _head, _project_id, _invoke_id, py_params)
        elif _status_code == SMARTBUS_ERR_TIMEOUT:
            self._event_executor.submit(self.on_flow_timeout, _head, _project_id, _invoke_id)
        else:
            self._event_executor.submit(self.on_flow_error, _head, _project_id, _invoke_id, _status_code)

    def _cb_flow_ack(self, arg, local_client_id, head, project_id, invoke_id, ack, msg):
        """调用流程是否成功回调函数类型

        :param c_void_p arg: 自定义数据
        :param c_byte local_client_id: 本地 ClientId
        :param PPacketHeader head: 消息头
        :param c_char_p project_id: projectid
        :param c_int invoke_id: 调用ID
        :param c_int ack: 流程调用是否成功。1表示成功，其它请参靠考误码
        :param c_char_p msg: 调用失败时的信息描述

        在调用流程之后，通过该回调函数类型获知流程调用是否成功
        """
        self.logger.debug(
            '_cb_flow_ack: arg=%s, local_client_id=%s, head=%s, project_id=%s, invoke_id=%s, ack=%s, msg=%s',
            arg, local_client_id, head, project_id, invoke_id, ack, msg)
        self._event_executor.submit(
            self.on_flow_ack,
            Head(head),
            b2s(string_at(project_id).strip(b'\x00'), 'cp936').strip(),
            invoke_id.value,
            ack.value,
            b2s(string_at(msg).strip(b'\x00'), 'cp936').strip() if msg else ''
        )

    def _cb_g_cnx(self, arg, unit_id, client_id, client_type, access_unit, status, add_info):
        """全局节点客户端连接、断开通知回调函数类型

        :param c_void_p arg: 自定义数据
        :param c_byte unit_id: 发生连接或断开事件的Smartbus节点单元ID
        :param c_byte client_id: 发生连接或断开事件的Smartbus节点单元中的客户端ID
        :param c_byte client_type: 发生连接或断开事件的Smartbus节点单元中的客户端类型
        :param c_byte access_unit: 连接点的UnitID
        :param c_byte status: 连接状态： 0 断开连接、1 新建连接、2 已有的连接
        :param c_char_p add_info: 连接附加信息

        当smartbus上某个节点发生连接或者断开时，该类型回调函数被调用。
        """
        self.logger.debug(
            '_cb_g_cnx: arg=%s, unit_id=%s, client_id=%s, client_type=%s, access_unit=%s, status=%s, add_info=%s',
            arg, unit_id, client_id, client_type, access_unit, status, add_info)
        self._event_executor.submit(
            self.on_global_connect_state_changed,
            unit_id.value,
            client_id.value,
            client_type.value,
            access_unit.value,
            status.value,
            b2s(string_at(add_info).strip(b'\x00'), 'cp936').strip() if add_info else ''
        )

    def _cb_trace(self, msg):
        """
        :param c_char_p msg:
        """
        self.logger.info(b2s(msg, 'cp936'))

    def _cb_trace_err(self, msg):
        """
        :param c_char_p msg:
        """
        self.logger.error(b2s(msg, 'cp936'))

    @classmethod
    def get(cls):
        return Client._instance

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def get_or_create(cls, *args, **kwargs):
        return Client._instance if Client._instance else cls.create(*args, **kwargs)

    @classmethod
    def destroy(cls):
        Client._instance.dispose()

    @property
    def client_id(self):
        return self._client_id

    @property
    def client_type(self):
        return self._client_type

    @property
    def connected(self):
        return self._connected

    def dispose(self):
        self.logger.warning('dispose')
        if self._lib:
            self._lib.Release.c_func()
            self._lib = None
        Client._instance = None

    def on_connect(self):
        """连接成功"""
        pass

    def on_connect_fail(self):
        """连接失败"""
        pass

    def on_disconnect(self):
        """连接断开"""
        pass

    def on_flow_resp(self, head, project_id, invoke_id, params):
        """调用流程结果返回

        :param Head head: 消息头
        :param str project_id: 流程项目ID
        :param int invoke_id: 流程调用ID
        :param list params: 流程返回值结果串, 采用 JSON Array 格式，对应于被调用流程的“子项目结束”节点的返回值列表
        """
        pass

    def on_flow_timeout(self, head, project_id, invoke_id):
        """流程执行超时

        :param Head head: 消息头
        :param str project_id: 流程项目ID
        :param int invoke_id: 流程调用ID
        """
        pass

    def on_flow_error(self, head, project_id, invoke_id, error_code):
        """流程执行错误

        :param Head head: 消息头
        :param str project_id: 流程项目ID
        :param int invoke_id: 流程调用ID
        :param int error_code: 错误码
        """
        pass

    def on_flow_ack(self, head, project_id, invoke_id, status_code, msg):
        """流程启动确认

        :param Head head: 消息头
        :param str project_id: 流程项目ID
        :param int invoke_id: 流程调用ID
        :param int status_code: 状态码. 1表示正确.
        :param str msg: 错误信息
        """
        pass

    def on_global_connect_state_changed(self, unit_id, client_id, client_type, access_unit_id, status_code, info):
        """全局节点客户端连接、断开事件

        :param int unit_id: 发生连接或断开事件的Smartbus节点单元ID
        :param int client_id: 发生连接或断开事件的Smartbus节点单元中的客户端ID
        :param int client_type: 发生连接或断开事件的Smartbus节点单元中的客户端类型
        :param int access_unit_id: 连接点的UnitID
        :param int status_code: 连接状态码： 0 断开连接、1 新建连接、2 已有的连接
        :param str info: 连接附加信息

        当smartbus上某个节点发生连接或者断开时触发。
        """
        pass

    def on_data(self, head, data):
        """接收到了数据

        :param Head head: 消息头
        :param bytes data: 二进制数据
        """
        pass
