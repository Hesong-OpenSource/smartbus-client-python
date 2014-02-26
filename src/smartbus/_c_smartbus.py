# -*- coding: utf-8 -*-

'''smartbus.h 的Python封装

该模块大致实现了与 smartbus.h 一对一的 ctyps 封装。
请参考 smartbus.h

:date: 2013-6-1
:author: lxy@hesong.ent
'''

import os
from ctypes import CFUNCTYPE, Structure, POINTER, c_byte, c_char, c_ushort, c_int, c_long, c_void_p, c_char_p

if os.name in ("nt", "ce"):
    from ctypes import WINFUNCTYPE as CALLBACKFUNCTYPE
else:
    CALLBACKFUNCTYPE = CFUNCTYPE
    
MAX_GLOBAL_SMART_NODE = 16
'''全局起始单元（节点）编号
'''

MIN_SMARTBUS_NETCLI_UNITID = 16
'''最小net客户端unitid值为16

Net客户端的unitid不能小于16
'''

MAX_SMARTBUS_NETCLI_UNITID_NUM = 32
'''net客户端值范围是16-47，全局最多32个。
'''

MAX_SMARTBUS_NODE_NUM = MAX_GLOBAL_SMART_NODE + MAX_SMARTBUS_NETCLI_UNITID_NUM
'''最大节点数

16 + 32 = 48 最大节点数
'''

MAX_SMARTBUS_NODE_CLI_NUM = 8
'''最大节点内的客户端数
'''

SMARTBUS_CMDTYPE_INTERNAL = 0

# #
SMARTBUS_CMDTYPE_SYSTEM = 1

# #  文件
SMARTBUS_CMDTYPE_FILE = 2

# # 用户数据
SMARTBUS_CMDTYPE_USER = 3

# # 守候实例命令
SMARTBUS_CMDTYPE_GUARD_CMD = 4

# #  守候实例文件传送
SMARTBUS_CMDTYPE_GUARD_FILE = 5

# # Ping应答包的cmdtype
SMARTBUS_SYSCMD_PING_ACK = 8



SMARTBUS_NODECLI_TYPE_NULL = 0
# #
SMARTBUS_NODECLI_TYPE_NODE = 1
# #
SMARTBUS_NODECLI_TYPE_IPSC = 2
# #
SMARTBUS_NODECLI_TYPE_MONITOR = 3
# #
SMARTBUS_NODECLI_TYPE_AGENT = 4



SMARTBUS_ERR_OK = 0

# #无效参数
SMARTBUS_ERR_ARGUMENT = -1

# #连接尚未建立    Connection is not established        -2
SMARTBUS_ERR_CONN_NOT_ESTAB = -2

# #
SMARTBUS_ERR_CONNECT_BREAK = -3

# #验证失败
SMARTBUS_ERR_AUTHOR = -4

# #
SMARTBUS_ERR_USER = -5

# #
SMARTBUS_ERR_PWD = -6

# #缓冲区满
SMARTBUS_ERR_BUFF_FULL = -7

# #节点不存在
SMARTBUS_ERR_NODE_NOTEXIST = -8

# #客户端不存在
SMARTBUS_ERR_CLI_NOTEXIST = -9

# #重复连接
SMARTBUS_ERR_CONNECTED = -10

# #发送给自己
SMARTBUS_ERR_SEND_OWN = -11

# #无效的unitid
SMARTBUS_ERR_UNITID_INVALID = -12

# #无效的clientid
SMARTBUS_ERR_CLIENTID_INVALID = -13

# #尚未初始化
SMARTBUS_ERR_NON_INIT = -14

# #发送的数据太大
SMARTBUS_ERR_MAX_DATASIZE = -15

# #无效的命令类型
SMARTBUS_ERR_CMDTYPE_INVALID = -16

# #无效的客户端类型
SMARTBUS_ERR_CLIENTTYPE_INVALID = -17

# #其它错误
SMARTBUS_ERR_OTHER = -99




MAX_SMARTBUS_IPADDR_SIZE = 64




CONNECTED_STATUS_INIT = 0
CONNECTED_STATUS_CONNECTING = 1
CONNECTED_STATUS_READY = 2
CONNECTED_STATUS_FAIL = 3
CONNECTED_STATUS_BLOCK = 4
CONNECTED_STATUS_CLOSE = 5
CONNECTED_STATUS_CONNECTED = 6
CONNECTED_STATUS_OK = 7




# # 接收数据包结构体的 pyton ctypes 封装类
class _PACKET_HEAD(Structure):
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
_c_fntyp_global_connect_cb = CALLBACKFUNCTYPE(None, c_void_p, c_char, c_char, c_char, c_char, c_char_p)
_c_fntyp_invokeflow_ack_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, POINTER(_PACKET_HEAD), c_char_p, c_int, c_int, c_char_p)
_c_fntyp_invokeflow_ret_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, POINTER(_PACKET_HEAD), c_char_p, c_int, c_int, c_char_p)
_c_fntyp_unitdata_cb = CALLBACKFUNCTYPE(None, c_byte, c_byte, c_void_p, c_int)
_c_fntyp_trace_str_cb = CALLBACKFUNCTYPE(None, c_char_p)


# # 接收数据包信息
#
# 每当接收到数据时，所触发的事件中，都包含该类型的参数，记录了一些数据包的相关信息。
# 它是结构体封装类 @ref _PACKET_HEAD 的再次封装类。使用它可以安全的从 @ref _PACKET_HEAD 读取数据。
class PackInfo(object):
    '''
    对应 SMARTBUS_PACKET_HEAD 结构体的 ctypes 数据类型 :class:`_PACKET_HEAD` 的再次封装
    '''

    def __init__(self, lp_head_struct):
        '''
        构造函数
        :param lp_head_struct: :class:`_PACKET_HEAD` 结构体指针
        '''
        self.__cmd = 0
        self.__cmdType = 0
        self.__srcUnitClientType = 0
        self.__srcUnitId = 0
        self.__srcUnitClientId = 0
        self.__dstUnitClientType = 0
        self.__dstUnitId = 0
        self.__dstUnitClientId = 0
        self.__packetSize = 0
        self.__dataLen = 0
        if lp_head_struct:
            head_struct = lp_head_struct.contents
            if head_struct:
                self.__cmd = head_struct.cmd
                self.__cmdType = head_struct.cmdtype
                self.__srcUnitClientType = ord(head_struct.src_unit_client_type)
                self.__srcUnitId = ord(head_struct.src_unit_id)
                self.__srcUnitClientId = ord(head_struct.src_unit_client_id)
                self.__dstUnitClientType = ord(head_struct.dest_unit_client_type)
                self.__dstUnitId = ord(head_struct.dest_unit_id)
                self.__dstUnitClientId = ord(head_struct.dest_unit_client_id)
                self.__packetSize = head_struct.packet_size
                self.__dataLen = head_struct.datalen
                
    def __repr__(self):
        return '<%s.%s object at %s. \
cmd=%s, \
cmdType=%s, \
srcUnitClientType=%s, \
srcUnitId=%s, \
srcUnitClientId=%s, \
dstUnitClientType=%s, \
dstUnitId=%s, \
dstUnitClientId=%s, \
packetSize=%s, \
dataLen=%s>' % (
            self.__class__.__module__,
            self.__class__.__name__,
            hex(id(self)),
            self.__cmd,
            self.__cmdType,
            self.__srcUnitClientType,
            self.__srcUnitId,
            self.__srcUnitClientId,
            self.__dstUnitClientType,
            self.__dstUnitId,
            self.__dstUnitClientId,
            self.__packetSize,
            self.__dataLen
        )
    
    @property
    def cmd(self):
        '''命令
        
        一条 SmartBus 数据的命令关键字
        '''
        return self.__cmd
    
    @property
    def cmdType(self):
        '''命令类型
        
        一条 SmartBus 数据的命令类型
        '''
        return self.__cmdType
    
    @property
    def srcUnitClientType(self):
        '''发送者客户端类型        
        '''
        return self.__srcUnitClientType
    
    @property
    def srcUnitId(self):
        '''发送者节点ID
        '''
        return self.__srcUnitId
    
    @property
    def srcUnitClientId(self):
        '''发送者客户端ID
        '''
        return self.__srcUnitClientId
    
    @property
    def dstUnitClientType(self):
        '''接收者客户端类型
        '''
        return self.__dstUnitClientType
    
    @property
    def dstUnitId(self):
        '''接收者节点ID
        '''
        return self.__dstUnitId
    
    @property
    def dstUnitClientId(self):
        '''接收者客户端ID
        '''
        return self.__dstUnitClientId
    
    @property
    def packetSize(self):
        '''包长度
        '''
        return self.__packetSize
    
    @property
    def dataLen(self):
        '''正文数据长度
        '''
        return self.__dataLen
