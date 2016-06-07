# -*- coding: utf-8 -*-

"""
面向对象样式的 NET 客户端 API 的 Python 封装
"""

from __future__ import absolute_import

from ctypes import CDLL, byref, create_string_buffer, string_at, c_void_p, c_char_p, c_int, c_byte, c_size_t
from ctypes.util import find_library
from concurrent.futures import ThreadPoolExecutor
import json

from ._c.net import *
from .errors import check
from .head import *
from .utils import *

__all__ = ['Client']


class Client(LoggerMixin):
    """NET 客户端

    .. note:: 使用 :meth:`create` 建立实例，不要直接使用构造函数！

    .. warning:: 实例一旦建立，无法释放！
    """

    _lib = None
    _unit_id = None
    _instances = {}
    _c_cbs = {}
    _global_connect_callback = None

    def __init__(self, client_id, client_type, master_ip, master_port, slave_ip=None, slave_port=None, user=None,
                 password=None, info=None, event_executor=None):
        """
        :param int client_id: 本地 client id, >= 0 and <= 255
        :param int client_type: 本地 client type
        :param str master_ip: 主服务器IP地址
        :param int master_port: 主服务器端口
        :param str slave_ip: 从服务器IP地址。没有从地址的，填写0，或者""
        :param int slave_port: 从服务器端口。没有从端口的，填写0xFFFF
        :param str user: 用户名
        :param int password: 密码
        :param str info: 附加信息
        :param ThreadPoolExecutor event_executor: 事件执行器。在此执行器中回调事件执行函数。默认执行器的线程池数量是 `1`
        """
        if not self._lib:
            raise RuntimeError('Library not been loaded')
        client_id = int(client_id)
        if not (0 <= client_id <= 255):
            raise ValueError('argument "local_client_id" must between 0 and 255')
        if client_id in self._instances:
            raise KeyError('Duplicated local client id "{}"'.format(client_id))
        self._client_id = client_id
        self._instances[self._client_id] = self
        self._unit_id = self.__class__._unit_id
        self._client_type = client_type
        self._master_ip = str(master_ip)
        self._master_port = int(master_port)
        self._slave_ip = slave_ip if slave_ip is None else str(slave_ip)
        self._slave_port = int(slave_port or 0xffff)
        self._user = user if user is None else str(user)
        self._password = password if password is None else str(password)
        self._info = info if info is None else str(info)
        if not event_executor:
            event_executor = ThreadPoolExecutor(max_workers=1)
        self._event_executor = event_executor

    @classmethod
    def initialize(cls, unit_id, global_connect_callback=None, lib_path=''):
        """初始化

        :param int unit_id: 在连接到 `Smartbus` 后，本节点的单元ID。
        :param callable global_connect_callback: 全局连接事件回调函数
        :param str lib_path: SO/DLL 文件路径名。
            默认值是 `None` : 将按照 :data:`DLL_NAME` 查找库文件，需确保库文件在 Python 运行时的搜索路径中。

        .. warning:: `unit_id >= 16` ，且全局唯一，不得重复

        全局节点客户端连接、断开事件，当smartbus上某个节点发生连接或者断开时触发。
        其函数形如：

        .. function:: global_connect_callback(unit_id, client_id, client_type, access_unit_id, status_code, info)

            :param int unit_id: 发生连接或断开事件的Smartbus节点单元ID
            :param int client_id: 发生连接或断开事件的Smartbus节点单元中的客户端ID
            :param int client_type: 发生连接或断开事件的Smartbus节点单元中的客户端类型
            :param int access_unit_id: 连接点的UnitID
            :param int status_code: 连接状态码： 0 断开连接、1 新建连接、2 已有的连接
            :param str info: 连接附加信息


        """
        # Load DLL/SO
        logger = cls.get_logger()
        logger.info('initialize: >>> lib_path=%s', lib_path)
        if cls._lib:
            raise RuntimeError('Library already loaded')
        if not lib_path:
            logger.debug('initialize: find_library "%s"', DLL_NAME)
            lib_path = find_library(DLL_NAME)
            if not lib_path:
                raise RuntimeError('Failed to find library {}'.format(DLL_NAME))
        logger.debug('initialize: CDLL %s', lib_path)
        cls._lib = CDLL(lib_path)
        if not cls._lib:
            raise RuntimeError('Failed to load library {}'.format(lib_path))
        logger.debug('initialize: %s', cls._lib)
        # Bind C API function to static API Class
        for func_cls in get_function_declarations():
            logger.debug('initialize: bind function %s', func_cls)
            func_cls.bind(cls._lib)
        # C API: init
        logger.debug('initialize: Init')
        ret = Init.c_func(c_byte(unit_id))
        check(ret)
        cls._unit_id = unit_id
        # C API: SetCallBackFn
        logger.debug('initialize: SetCallBackFn')
        cls._c_cbs['connection'] = fntyp_connection_cb(cls._cb_cnx)
        cls._c_cbs['recvdata'] = fntyp_recvdata_cb(cls._cb_rcv)
        cls._c_cbs['disconnect'] = fntyp_disconnect_cb(cls._cb_dnx)
        cls._c_cbs['invokeflow_ret'] = fntyp_invokeflow_ret_cb(cls._cb_dnx)
        cls._c_cbs['global_connect'] = fntyp_global_connect_cb(cls._cb_g_cnx)
        SetCallBackFn.c_func(
            cls._c_cbs['connection'],
            cls._c_cbs['recvdata'],
            cls._c_cbs['disconnect'],
            cls._c_cbs['invokeflow_ret'],
            cls._c_cbs['global_connect'],
            None
        )
        # C API: SetCallBackFnEx
        logger.debug('initialize: SetCallBackFnEx')
        SetCallBackFnEx.c_func(c_char_p(b'smartbus_invokeflow_ack_cb'), fntyp_invokeflow_ack_cb(cls._cb_flow_ack))
        # others
        cls._global_connect_callback = global_connect_callback
        # Load and init OK!!!
        logger.info('initialize: <<<')

    @classmethod
    def _cb_cnx(cls, arg, local_client_id, access_point_unit_id, ack):
        """客户端连接成功回调函数类型

        :param c_void_p arg: 自定义数据
        :param c_byte local_client_id: 连接成功的本地 ClientId
        :param c_int access_point_unit_id: int 连接点的 UnitID
        :param c_int ack: int 连接注册结果： 0 建立连接成功、< 0 连接失败
        """
        cls.get_logger().debug(
            'connect: '
            'arg=%s, local_client_id=%s, access_point_unit_id=%s, ack=%s',
            arg, local_client_id, access_point_unit_id, ack
        )
        inst = cls.find(local_client_id)
        if inst:
            if ack == 0:  # 建立连接成功
                inst._unit_id = access_point_unit_id
                inst._event_executor.submit(inst.on_connect)
            else:  # 连接失败
                inst._event_executor.submit(inst.on_connect_fail, ack)

    @classmethod
    def _cb_rcv(cls, param, local_client_id, head, data, size):
        """接收数据回调函数类型

        :param c_void_p param: 自定义数据
        :param c_byte local_client_id: 收到数据的的本地 ClientId
        :param PPacketHeader head: 数据包头
        :param c_void_p data: 数据包体
        :param c_size_t size: 包体字节长度
        """
        cls.get_logger().debug(
            'receive-data: '
            'param=%s, local_client_id=%s, head=%s, data=%s, size=%s',
            param, local_client_id, head, data, size
        )
        inst = cls.find(local_client_id)
        if inst:
            inst._event_executor.submit(inst.on_data, Head(head), string_at(data, size) if data else None)

    @classmethod
    def _cb_dnx(cls, param, local_client_id):
        """客户端连接断开回调函数类型

        :param c_void_p param: 自定义数据
        :param c_byte local_client_id: 连接断开的本地 ClientId
        """
        cls.get_logger().debug(
            'disconnect: '
            'param=%s, local_client_id=%s',
            param, local_client_id
        )
        inst = cls.find(local_client_id)
        if inst:
            inst._event_executor.submit(inst.on_disconnect)

    @classmethod
    def _cb_flow_ack(cls, arg, local_client_id, head, project_id, invoke_id, ack, msg):
        """调用流程是否成功回调函数类型

        :param c_void_p arg: 自定义数据
        :param c_byte local_client_id: 本地 ClientId
        :param PPacketHeader head: 消息头
        :param c_char_p project_id: project id
        :param c_int invoke_id: 调用ID
        :param c_int ack: 流程调用是否成功。1表示成功，其它请参靠考误码
        :param c_char_p msg: 调用失败时的信息描述

        在调用流程之后，通过该回调函数类型获知流程调用是否成功
        """
        cls.get_logger().debug(
            'flow-ack: '
            'arg=%s, local_client_id=%s, head=%s, project_id=%s, invoke_id=%s, ack=%s, msg=%s',
            arg, local_client_id, head, project_id, invoke_id, ack, msg
        )
        _head = Head(head)
        inst = cls.find(local_client_id)
        if inst:
            inst._event_executor.submit(
                inst.on_flow_ack,
                _head,
                b2s_recode(string_at(project_id).strip(b'\x00'), 'cp936', 'utf-8').strip(),
                invoke_id,
                ack,
                b2s_recode(string_at(msg).strip(b'\x00'), 'cp936', 'utf-8').strip() if msg else ''
            )

    @classmethod
    def _cb_flow_ret(cls, arg, local_client_id, head, project_id, invoke_id, ret, param):
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
        cls.get_logger().debug(
            'flow-ret: '
            'arg=%s, local_client_id=%s, head=%s, project_id=%s, invoke_id=%s, ret=%s, param=%s',
            arg, local_client_id, head, project_id, invoke_id, ret, param
        )
        _head = Head(head)
        inst = cls.find(local_client_id)
        if inst:
            _project_id = to_str(string_at(project_id).strip(b'\x00')).strip()
            _invoke_id = invoke_id
            _status_code = ret
            if _status_code == 1:
                py_params = []
                if param:
                    _params = b2s_recode(string_at(param).strip(b'\x00'), 'cp936', 'utf-8').strip()
                    if _params:
                        py_params = json.loads(_params)
                inst._event_executor.submit(inst.on_flow_resp, _head, _project_id, _invoke_id, py_params)
            elif _status_code == SMARTBUS_ERR_TIMEOUT:
                inst._event_executor.submit(inst.on_flow_timeout, _head, _project_id, _invoke_id)
            else:
                inst._event_executor.submit(inst.on_flow_error, _head, _project_id, _invoke_id, _status_code)

    @classmethod
    def _cb_g_cnx(cls, arg, unit_id, client_id, client_type, access_unit, status, add_info):
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
        cls.get_logger().debug(
            'global-connection: '
            'arg=%s, unit_id=%s, client_id=%s, client_type=%s, access_unit=%s, status=%s, add_info=%s',
            arg, unit_id, client_id, client_type, access_unit, status, add_info
        )
        if callable(cls._global_connect_callback):
            cls._global_connect_callback(
                ord(unit_id),
                ord(client_id),
                ord(client_type),
                ord(access_unit),
                ord(status),
                to_str(string_at(add_info)) if add_info else ''
            )

    @classmethod
    def _cb_trace(cls, msg):
        """
        :param c_char_p msg:
        """
        cls.get_logger().info(to_str(string_at(msg))) if msg else ''

    @classmethod
    def _cb_trace_err(cls, msg):
        """
        :param c_char_p msg:
        """
        cls.get_logger().error(to_str(string_at(msg))) if msg else ''

    @classmethod
    def create(cls, *args, **kwargs):
        """建立实例

        参数见构造函数
        """
        return cls(*args, **kwargs)

    @classmethod
    def find(cls, client_id, default=None):
        """查找并返回实例

        :param client_id: 要查找的实例的 :attr:`client_id`
        :param default: 如果找不到，返回这个值
        :return: 找到的实例
        :rtype: Client
        """
        return cls._instances.get(client_id, default)

    @property
    def unit_id(self):
        return self._unit_id

    @property
    def client_id(self):
        return self._client_id

    @property
    def client_type(self):
        return self._client_type

    @property
    def master_ip(self):
        return self._master_ip

    @property
    def master_port(self):
        return self._master_port

    @property
    def slave_ip(self):
        return self._slave_ip

    @property
    def slave_port(self):
        return self._slave_port

    @property
    def user(self):
        return self._user

    @property
    def password(self):
        return self._password

    @property
    def info(self):
        return self._info

    def activate(self):
        """激活客户端

        将建立连接。连接一旦建立，就可以接受/发送数据，

        .. attention::
            该函数立即返回，无论连接成功与否。
            如该函数没有直接返回失败，客户端会自动尝试连接 `smartbus` 服务器，并在连接断开/失败时自动尝试重连
        """
        self.logger.info('<%s> connect', self._client_id)
        error_code = CreateConnect.c_func(
            c_byte(self._client_id),
            c_int(self._client_type),
            c_char_p(to_bytes(self._master_ip)) if self._master_ip else None,
            c_ushort(self._master_port),
            c_char_p(to_bytes(self._slave_ip)) if self._slave_ip else None,
            c_ushort(self._slave_port),
            c_char_p(to_bytes(self._user)) if self._user else None,
            c_char_p(to_bytes(self._password)) if self._password else None,
            c_char_p(to_bytes(self._info)) if self._info else None
        )
        check(error_code)

    def send_data(self, cmd, cmd_type, dst_unit_id, dst_client_id, dst_client_type, data):
        """发送数据

        :param int cmd: 命令
        :param int cmd_type: 命令类型
        :param int dst_unit_id: 目标节点ID
        :param int dst_client_id: 目标客户端ID
        :param int dst_client_type: 目标客户端类型
        :param bytes data: 待发送数据，类型必须是 :class:`bytes`
        """
        self.logger.debug(
            'send_data: '
            'cmd=%s, cmd_type=%s, dst_unit_id=%s, dst_client_id=%s, dst_client_type=%s, data=%s',
            cmd, cmd_type, dst_unit_id, dst_client_id, dst_client_type, data
        )
        length = len(data) if data else 0
        buff = create_string_buffer(data, length) if data else None
        error_code = SendData.c_func(
            c_byte(self._client_id),
            c_byte(cmd),
            c_byte(cmd_type),
            c_int(dst_unit_id),
            c_int(dst_client_id),
            c_int(dst_client_type),
            byref(buff),
            c_int(length)
        )
        check(error_code)

    def ping(self, dst_unit_id, dst_client_id, dst_client_type, data=None):
        """发送PING命令

        :param int dst_unit_id: 目标的smartbus单元ID
        :param int dst_client_id: 目标的smartbus客户端ID
        :param int dst_client_type: 目标的smartbus客户端类型
        :param bytes data: 待发送数据，类型必须是 :class:`bytes`
        """
        self.logger.debug(
            'ping: '
            'dst_unit_id=%s, dst_client_id=%s, dst_client_type=%s, data=%s',
            dst_unit_id, dst_client_id, dst_client_type, data
        )
        length = len(data) if data else 0
        buff = create_string_buffer(data, length) if data else None
        error_code = SendPing.c_func(
            c_byte(self._client_id),
            c_int(dst_unit_id),
            c_int(dst_client_id),
            c_int(dst_client_type),
            byref(buff),
            c_int(length)
        )
        check(error_code)

    def notify(self, server_unit_id, process_index, project_id, title, mode, expires, txt):
        """发送通知消息

        :param int server_unit_id: 目标IPSC服务器 `smartbus` 单元ID
        :param int process_index:  IPSC 进程ID，同时也是该IPSC进程的 smartbus client-id
        :param str project_id:     流程项目ID
        :param str title:          通知的标题
        :param int mode:           调用模式。目前无意义，一律使用0
        :param float expires:      消息有效期。单位秒
        :param str txt:            消息文本（对于 Python2 bytes string, **必须** 使用 `utf-8` 编码）
        :return:                   调用任务的ID。
        :rtype:                    int
        :except:                   API返回错误
        """
        self.logger.debug(
            'notify: '
            'server_unit_id=%s, process_index=%s, project_id=%s, title=%s, mode=%s, expires=%s, txt=%s',
            server_unit_id, process_index, project_id, title, mode, expires, txt
        )
        result = SendNotify.c_func(
            c_byte(self._client_id),
            c_int(server_unit_id),
            c_int(process_index),
            c_char_p(to_bytes(project_id)),
            c_char_p(to_bytes(title)) if title else None,
            c_int(mode),
            c_int(int(expires * 1000)),
            c_char_p(s2b_recode(txt, 'utf-8', 'cp936')) if txt else None
        )
        iid = result.value
        if iid < 0:
            check(iid)
        return iid

    def launch_flow(self, server_unit_id, process_index, project_id, flow_id, mode, timeout, params):
        """调用流程

        :param int server_unit_id: 目标 `IPSC` 服务器 `smartbus` 单元ID
        :param int process_index: `IPSC` 进程 `ID` ，同时也是该 `IPSC` 进程的 `smartbus` Client ID
        :param str project_id: 流程项目ID
        :param str flow_id: 流程ID
        :param int mode: 调用模式：0 有流程返回、1 无流程返回
        :param float timeout: 有流程返回时的等待超时值（秒）
        :param list params: 流程输入参数里表。简单数据类型JSON数组。
            子流程开始节点的传人参数自动变换为list类型数据。
            对应的字符串内容最大长度不超过32K字节。
        :return: invoke_id，调用ID，用于流程结果返回匹配用途。
        :rtype: int
        """
        self.logger.debug(
            'launch-flow: '
            'server_unit_id=%s, process_index=%s, project_id=%s, flow_id=%s, mode=%s, timeout=%s, params=%s',
            server_unit_id, process_index, project_id, flow_id, mode, timeout, params
        )
        value_string_list = c_char_p(to_bytes(str(params)))
        result = RemoteInvokeFlow.c_func(
            c_byte(self._client_id),
            c_int(server_unit_id),
            c_int(process_index),
            c_char_p(to_bytes(project_id)),
            c_char_p(to_bytes(flow_id)),
            c_int(mode),
            c_int(int(timeout * 1000)),
            value_string_list
        )
        iid = result.value
        if iid < 0:
            check(iid)
        return iid

    def on_connect(self):
        """连接成功"""
        pass

    def on_connect_fail(self, error_code):
        """连接失败"""
        pass

    def on_disconnect(self):
        """连接断开"""
        pass

    def on_data(self, head, data):
        """接收到了数据

        :param Head head: 消息头
        :param bytes data: :class:`bytes` 二进制数据
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
