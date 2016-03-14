# -*- coding: utf-8 -*-

"""smartbus.h 的Python封装

该模块大致实现了与 `smartbus.h` 一对一的 :mod:`ctypes` 封装。
请参考 `smartbus.h`

:date: 2013-06-01
:author: lxy@hesong.ent
"""

import os
from ctypes import CFUNCTYPE, Structure, POINTER, c_byte, c_char, c_ushort, c_int, c_long, c_void_p, c_char_p

if os.name in ("nt", "ce"):
    from ctypes import WINFUNCTYPE as CALLBACKFUNCTYPE
else:
    CALLBACKFUNCTYPE = CFUNCTYPE

MAX_GLOBAL_SMART_NODE = 16
#: 全局起始单元（节点）编号


MIN_SMARTBUS_NETCLI_UNITID = 16
#: 最小net客户端unitid值为16
#: 
#: Net客户端的unitid不能小于16


MAX_SMARTBUS_NETCLI_UNITID_NUM = 32
#: net客户端值范围是16-47，全局最多32个。

MAX_SMARTBUS_NODE_NUM = MAX_GLOBAL_SMART_NODE + MAX_SMARTBUS_NETCLI_UNITID_NUM
#: 最大节点数
#:
#:16 + 32 = 48 最大节点数

MAX_SMARTBUS_NODE_CLI_NUM = 8
#: 最大节点内的客户端数

SMARTBUS_CMDTYPE_INTERNAL = 0
#: 内部

SMARTBUS_CMDTYPE_SYSTEM = 1
#: 系统

SMARTBUS_CMDTYPE_FILE = 2
#: 文件

SMARTBUS_CMDTYPE_USER = 3
#: 用户数据

SMARTBUS_CMDTYPE_GUARD_CMD = 4
#: 守候实例命令

SMARTBUS_CMDTYPE_GUARD_FILE = 5
#: 守候实例文件传送

SMARTBUS_SYSCMD_PING_ACK = 8
#: Ping应答包的 cmd_type

SMARTBUS_NODECLI_TYPE_NULL = 0
SMARTBUS_NODECLI_TYPE_NODE = 1
SMARTBUS_NODECLI_TYPE_IPSC = 2
SMARTBUS_NODECLI_TYPE_MONITOR = 3
SMARTBUS_NODECLI_TYPE_AGENT = 4

SMARTBUS_ERR_OK = 0

SMARTBUS_ERR_ARGUMENT = -1
#: 无效参数

SMARTBUS_ERR_CONN_NOT_ESTAB = -2
#: 连接尚未建立

SMARTBUS_ERR_CONNECT_BREAK = -3

SMARTBUS_ERR_AUTHOR = -4
#: 验证失败

SMARTBUS_ERR_USER = -5
#: 错误的用户名

SMARTBUS_ERR_PWD = -6
#: 错误的密码

SMARTBUS_ERR_BUFF_FULL = -7
#: 缓冲区满

SMARTBUS_ERR_NODE_NOTEXIST = -8
#: 节点不存在

SMARTBUS_ERR_CLI_NOTEXIST = -9
#: 客户端不存在

SMARTBUS_ERR_CONNECTED = -10
#: 重复连接

SMARTBUS_ERR_SEND_OWN = -11
#: 发送给自己

SMARTBUS_ERR_UNITID_INVALID = -12
#: 无效的unitid

SMARTBUS_ERR_CLIENTID_INVALID = -13
#: 无效的clientid

SMARTBUS_ERR_NON_INIT = -14
#: 尚未初始化

SMARTBUS_ERR_MAX_DATASIZE = -15
#: 发送的数据太大

SMARTBUS_ERR_CMDTYPE_INVALID = -16

SMARTBUS_ERR_CLIENTTYPE_INVALID = -17
#: 无效的客户端类型

SMARTBUS_ERR_SEND_DATA = -18
#: 发送数据错误

SMARTBUS_ERR_MEM_ALLOC = -19
#: 分配内存错误

SMARTBUS_ERR_ESTABLI_CONNECT = -20
#: 建立连接失败

SMARTBUS_ERR_CLI_TOOMANY = -21
#: 客户端太多

SMARTBUS_ERR_CLI_EXIST = -22
#: 客户端已存在

SMARTBUS_ERR_DEST_NONEXIST = -23
#: 目标不存在

SMARTBUS_ERR_REGISTERED_REPEAT = -24
#: 重复注册

SMARTBUS_ERR_TIMEOUT = -25
#: 超时

SMARTBUS_ERR_OTHER = -99
#: 其它错误

MAX_SMARTBUS_IPADDR_SIZE = 64

CONNECTED_STATUS_INIT = 0
CONNECTED_STATUS_CONNECTING = 1
CONNECTED_STATUS_READY = 2
CONNECTED_STATUS_FAIL = 3
CONNECTED_STATUS_BLOCK = 4
CONNECTED_STATUS_CLOSE = 5
CONNECTED_STATUS_CONNECTED = 6
CONNECTED_STATUS_OK = 7


class _PACKET_HEAD(Structure):
    """
    接收数据包结构体的 python :mod:`ctypes` 封装类
    """
    _pack_ = 1  # 设定为1字节对齐
    _fields_ = [
        ('head_flag', c_ushort),  # 头标识    : 0x5b15
        ('cmd', c_byte),
        ('cmdtype', c_byte),
        ('src_unit_client_type', c_char),
        ('src_unit_id', c_char),
        ('src_unit_client_id', c_char),
        ('dest_unit_client_type', c_char),
        ('dest_unit_id', c_char),
        ('dest_unit_client_id', c_char),
        ('reserved', c_char * 2),
        ('packet_size', c_long),
        ('datalen', c_long),
    ]


_c_fntyp_connection_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, c_int, c_int)
_c_fntyp_disconnect_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte)
_c_fntyp_recvdata_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, POINTER(_PACKET_HEAD), c_void_p, c_int)
_c_fntyp_global_connect_cb = CALLBACKFUNCTYPE(None, c_void_p, c_char, c_char, c_char, c_char, c_char, c_char_p)
_c_fntyp_invokeflow_ack_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, POINTER(_PACKET_HEAD), c_char_p, c_int, c_int,
                                              c_char_p)
_c_fntyp_invokeflow_ret_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, POINTER(_PACKET_HEAD), c_char_p, c_int, c_int,
                                              c_char_p)
_c_fntyp_unitdata_cb = CALLBACKFUNCTYPE(None, c_byte, c_byte, c_void_p, c_int)
_c_fntyp_trace_str_cb = CALLBACKFUNCTYPE(None, c_char_p)


class PackInfo:
    """Smartbus通信包信息

    每当接收到数据时，所触发的事件中，都包含该类型的参数，记录了一些数据包的相关信息

    对应 `SMARTBUS_PACKET_HEAD` 结构体的 :mod:`ctypes` 数据类型 :class:`_PACKET_HEAD` 的再次封装

    """

    def __init__(self, ptr):
        """
        :param _PACKET_HEAD ptr: 结构体指针
        """
        self._prt = ptr
        self._cmd = 0
        self._cmd_type = 0
        self._src_unit_client_type = 0
        self._src_unit_id = 0
        self._src_unit_clientId = 0
        self._dst_unit_client_type = 0
        self._dst_unitId = 0
        self._dst_unit_client_id = 0
        self._packet_size = 0
        self._data_length = 0
        self._cmd = ptr.contents.cmd
        self._cmd_type = ptr.contents.cmdtype
        self._src_unit_client_type = ord(ptr.contents.src_unit_client_type)
        self._src_unit_id = ord(ptr.contents.src_unit_id)
        self._src_unit_clientId = ord(ptr.contents.src_unit_client_id)
        self._dst_unit_client_type = ord(ptr.contents.dest_unit_client_type)
        self._dst_unitId = ord(ptr.contents.dest_unit_id)
        self._dst_unit_client_id = ord(ptr.contents.dest_unit_client_id)
        self._packet_size = ptr.contents.packet_size
        self._data_length = ptr.contents.datalen

    def __repr__(self):
        s = '<%s.%s object at %s. ' + \
            'cmd=%s, ' + \
            'cmd_type=%s, ' + \
            'src_unit_client_type=%s,' + \
            'src_unit_id=%s, ' + \
            'src_unit_client_id=%s, ' + \
            'dst_unit_client_type=%s, ' + \
            'dst_unit_id=%s, ' + \
            'dst_unit_client_id=%s, ' + \
            'packet_size=%s, ' + \
            'data_length=%s>'
        return s % (
            self.__class__.__module__,
            self.__class__.__name__,
            hex(id(self)),
            self._cmd,
            self._cmd_type,
            self._src_unit_client_type,
            self._src_unit_id,
            self._src_unit_clientId,
            self._dst_unit_client_type,
            self._dst_unitId,
            self._dst_unit_client_id,
            self._packet_size,
            self._data_length
        )

    @property
    def cmd(self):
        """ 命令

        一条 SmartBus 数据的命令关键字
        """
        return self._cmd

    @property
    def cmd_type(self):
        """ 命令类型

        一条 SmartBus 数据的命令类型
        """
        return self._cmd_type

    @property
    def src_unit_client_type(self):
        """发送者客户端类型
        """
        return self._src_unit_client_type

    @property
    def src_unit_id(self):
        """ 发送者节点ID
        """
        return self._src_unit_id

    @property
    def src_unit_client_id(self):
        """ 发送者客户端ID
        """
        return self._src_unit_clientId

    @property
    def dst_unit_client_type(self):
        """ 接收者客户端类型
        """
        return self._dst_unit_client_type

    @property
    def dst_unit_id(self):
        """ 接收者节点ID
        """
        return self._dst_unitId

    @property
    def dst_unit_client_id(self):
        """ 接收者客户端ID
        """
        return self._dst_unit_client_id

    @property
    def packet_size(self):
        """ 包长度
        """
        return self._packet_size

    @property
    def data_length(self):
        """ 正文数据长度
        """
        return self._data_length
