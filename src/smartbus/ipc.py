# -*- coding: utf-8 -*-

"""
Python functions for IPC client API.
"""

from __future__ import absolute_import

from ctypes import CDLL, c_void_p, c_char_p, c_int, c_byte, c_size_t
from ctypes.util import find_library

from ._c.mutual import *
from ._c.ipc import *
from .errors import check
from .utils import *

__all__ = ['Client']


class AbstractClient:
    pass


class Client(AbstractClient, LoggerMixin):
    """IPC Client"""

    __instance__ = None  #: Singleton Client instance

    def __init__(self, client_id, client_type, file=''):
        """
        :param int client_id:
        :param int client_type:
        :param str file: SO/DLL file, `default` is `None`.
            When `None` or empty string, the function will try to find and load so/dll by :data:`DLL_NAME`

        Load `Smartbus IPC client` so/dll into this Python package, then some initializations.
        """
        # Load DLL/SO
        self.logger.info('__init__: >>> file=%s', file)
        if Client.__instance__:
            raise RuntimeError('Client already constructed.')
        if self._lib:
            raise RuntimeError('library already loaded')
        if not file:
            self.logger.debug('__init__: find_library "%s"', DLL_NAME)
            file = find_library(DLL_NAME)
            if not file:
                raise RuntimeError('Failed to find library {}'.format(DLL_NAME))
        self.logger.debug('__init__: CDLL %s', file)
        self._lib = CDLL(file)
        if not self._lib:
            raise RuntimeError('Failed to load library {}'.format(file))
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
        # All OK!!!
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
        pass

    def _cb_rcv(self, param, local_client_id, head, data, size):
        """接收数据回调函数类型

        :param c_void_p param: 自定义数据
        :param c_byte local_client_id: 收到数据的的本地 ClientId
        :param PPacketHeader head: 数据包头
        :param c_void_p data: 数据包体
        :param c_size_t size: 包体字节长度
        """
        pass

    def _cb_dnx(self, param, local_client_id):
        """客户端连接断开回调函数类型

        :param c_void_p param: 自定义数据
        :param c_byte local_client_id: 连接断开的本地 ClientId
        """
        pass

    def _cb_flow_ret(self, arg, local_client_id, head, project_id, invoke_id, ret, param):
        """调用流程结果返回回调函数类型

        :param c_void_p arg: 自定义数据
        :param c_byte local_client_id: 本地 ClientId
        :param PPacketHeader head: 消息头
        :param c_char_p project_id: projectid
        :param c_int invoke_id: 调用ID
        :param c_int ret: 返回值。1表示正常返回，-25表示超时，小于1表示错误,其它请见错误码
        :param c_char_p param: 结果参数串, 采用 JSON Array 格式

        通过类类型的回调函数，获取被调用流程的“子项目结束”节点的返回值列表
        """
        pass

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
        pass

    def _cb_g_cnx(self, arg, unit_id, client_id, client_type, access_unit, status, add_info):
        """全局节点客户端连接、断开通知回调函数类型

        :param c_void_p arg: 自定义数据
        :param c_byte unit_id: 发生连接或断开事件的Smartbus节点单元ID
        :param c_byte client_id: 发生连接或断开事件的Smartbus节点单元中的客户端ID
        :param c_byte client_type: 发生连接或断开事件的Smartbus节点单元中的客户端类型
        :param c_byte access_unit: ?
        :param status: 连接状态： 0 断开连接、1 新建连接、2 已有的连接
        :param c_char_p add_info: 连接附加信息

        当smartbus上某个节点发生连接或者断开时，该类型回调函数被调用。
        """
        pass

    def _cb_trace(self, msg):
        """
        :param c_char_p msg:
        """
        pass

    def _cb_trace_err(self, msg):
        """
        :param c_char_p msg:
        """
        pass

    @classmethod
    def create(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def get_instance(cls):
        return Client.__instance__

    @classmethod
    def get_or_create(cls, *args, **kwargs):
        return Client.__instance__ if Client.__instance__ else cls.create(*args, **kwargs)

    @classmethod
    def destroy(cls):
        Client.__instance__.dispose()

    @property
    def client_id(self):
        return self._client_id

    @property
    def client_type(self):
        return self._client_type

    def dispose(self):
        self.logger.warning('dispose')
        if self._lib:
            self._lib.Release.c_func()
            self._lib = None
        Client.__instance__ = None

    def on_connect(self):
        pass

    def on_connect_fail(self):
        pass

    def on_disconnect(self):
        pass
