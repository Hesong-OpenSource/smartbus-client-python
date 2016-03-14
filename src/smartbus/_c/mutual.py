import platform
import ctypes
from ctypes import POINTER, Structure, c_void_p, c_int, c_char_p, c_byte, c_char, c_long, c_ushort

__all__ = ['PacketHeader', 'PPacketHeader',
           'fntyp_connection_cb', 'fntyp_disconnect_cb', 'fntyp_recvdata_cb', 'fntyp_global_connect_cb',
           'fntyp_invokeflow_ack_cb', 'fntyp_invokeflow_ret_cb',
           'fntyp_unitdata_cb', 'fntyp_trace_str_cb'
           ]

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


class PacketHeader(Structure):
    #: 设定为1字节对齐
    _pack_ = 1
    _fields_ = [
        #: 头标识    : 0x5b15
        ('head_flag', c_ushort),
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


PPacketHeader = POINTER(PacketHeader)

#: Callback function call convert in the library
CALLBACKFUNCTYPE = None
if platform.system() == 'Windows':
    CALLBACKFUNCTYPE = ctypes.WINFUNCTYPE
else:
    CALLBACKFUNCTYPE = ctypes.CFUNCTYPE

fntyp_connection_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, c_int, c_int)
fntyp_disconnect_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte)
fntyp_recvdata_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, PPacketHeader, c_void_p, c_int)
fntyp_global_connect_cb = CALLBACKFUNCTYPE(None, c_void_p, c_char, c_char, c_char, c_char, c_char, c_char_p)
fntyp_invokeflow_ack_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, PPacketHeader, c_char_p, c_int, c_int, c_char_p)
fntyp_invokeflow_ret_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, PPacketHeader, c_char_p, c_int, c_int, c_char_p)
fntyp_unitdata_cb = CALLBACKFUNCTYPE(None, c_byte, c_byte, c_void_p, c_int)
fntyp_trace_str_cb = CALLBACKFUNCTYPE(None, c_char_p)
