#-*- coding: utf-8 -*-

## @package smartbus._c_smartbus
# smartbus.h 的Python封装

import os
from ctypes import CFUNCTYPE, Structure, POINTER, c_byte, c_char, c_ushort, c_int, c_long, c_void_p, c_char_p

if os.name in ("nt", "ce"):
    from ctypes import WINFUNCTYPE as CALLBACKFUNCTYPE
else:
    CALLBACKFUNCTYPE = CFUNCTYPE
    
## @name 最大值常量
## @{

MAX_GLOBAL_SMART_NODE = 16

## 最小net客户端unitid值为16。Net客户端的unitid不能小于16
MIN_SMARTBUS_NETCLI_UNITID = 16

## net客户端值范围就是：16 － 47
MAX_SMARTBUS_NETCLI_UNITID_NUM = 32

## 16 + 32 = 48 最大节点数
MAX_SMARTBUS_NODE_NUM = MAX_GLOBAL_SMART_NODE + MAX_SMARTBUS_NETCLI_UNITID_NUM

##  最大节点内的客户端数
MAX_SMARTBUS_NODE_CLI_NUM = 8

## @}

## @name 命令类型常量
## @{

#
SMARTBUS_CMDTYPE_INTERNAL = 0

##
SMARTBUS_CMDTYPE_SYSTEM = 1

##  文件
SMARTBUS_CMDTYPE_FILE = 2

## 用户数据
SMARTBUS_CMDTYPE_USER = 3

## 守候实例命令
SMARTBUS_CMDTYPE_GUARD_CMD = 4

##  守候实例文件传送
SMARTBUS_CMDTYPE_GUARD_FILE = 5

## Ping应答包的cmdtype
SMARTBUS_SYSCMD_PING_ACK = 8

## @}

## @name 节点类型
## @{
##
SMARTBUS_NODECLI_TYPE_NULL = 0
##
SMARTBUS_NODECLI_TYPE_NODE = 1
##
SMARTBUS_NODECLI_TYPE_IPSC = 2
##
SMARTBUS_NODECLI_TYPE_MONITOR = 3
##
SMARTBUS_NODECLI_TYPE_AGENT = 4
## @}

## @name 错误码定义
## @{

##
SMARTBUS_ERR_OK = 0

##无效参数
SMARTBUS_ERR_ARGUMENT = -1

##连接尚未建立    Connection is not established        -2
SMARTBUS_ERR_CONN_NOT_ESTAB = -2

##
SMARTBUS_ERR_CONNECT_BREAK = -3

##验证失败
SMARTBUS_ERR_AUTHOR = -4

##
SMARTBUS_ERR_USER = -5

##
SMARTBUS_ERR_PWD = -6

##缓冲区满
SMARTBUS_ERR_BUFF_FULL = -7

##节点不存在
SMARTBUS_ERR_NODE_NOTEXIST = -8

##客户端不存在
SMARTBUS_ERR_CLI_NOTEXIST = -9

##重复连接
SMARTBUS_ERR_CONNECTED = -10

##发送给自己
SMARTBUS_ERR_SEND_OWN = -11

##无效的unitid
SMARTBUS_ERR_UNITID_INVALID = -12

##无效的clientid
SMARTBUS_ERR_CLIENTID_INVALID = -13

##尚未初始化
SMARTBUS_ERR_NON_INIT = -14

##发送的数据太大
SMARTBUS_ERR_MAX_DATASIZE = -15

##无效的命令类型
SMARTBUS_ERR_CMDTYPE_INVALID = -16

##无效的客户端类型
SMARTBUS_ERR_CLIENTTYPE_INVALID = -17

##其它错误
SMARTBUS_ERR_OTHER = -99

## @}

##
MAX_SMARTBUS_IPADDR_SIZE = 64

## @name CONNECTED_STATUS
## @{

CONNECTED_STATUS_INIT = 0
CONNECTED_STATUS_CONNECTING = 1
CONNECTED_STATUS_READY = 2
CONNECTED_STATUS_FAIL = 3
CONNECTED_STATUS_BLOCK = 4
CONNECTED_STATUS_CLOSE = 5
CONNECTED_STATUS_CONNECTED = 6
CONNECTED_STATUS_OK = 7

## @}

## @name 结构体
## @{

## 接收数据包结构体的 pyton ctypes 封装类
# @see PackInfo
class _PACKET_HEAD(Structure):
    _pack_ = 1  # 设定为1字节对齐
    _fields_ = [
        ('head_flag', c_ushort),  #头标识    : 0x5b15
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

## @}

## @name 回调函数类型
## @{

_c_fntyp_connection_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, c_int, c_int)
_c_fntyp_disconnect_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte)
_c_fntyp_recvdata_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, POINTER(_PACKET_HEAD), c_void_p, c_int)
_c_fntyp_global_connect_cb = CALLBACKFUNCTYPE(None, c_void_p, c_char, c_char, c_char, c_char, c_char_p)
_c_fntyp_invokeflow_ret_cb = CALLBACKFUNCTYPE(None, c_void_p, c_byte, POINTER(_PACKET_HEAD), c_char_p, c_int, c_int, c_char_p)
_c_fntyp_unitdata_cb = CALLBACKFUNCTYPE(None, c_byte, c_byte, c_void_p, c_int)

## @}


## 接收数据包信息
#
# 每当接收到数据时，所触发的事件中，都包含该类型的参数，记录了一些数据包的相关信息。
# 它是结构体封装类 @ref _PACKET_HEAD 的再次封装类。使用它可以安全的从 @ref _PACKET_HEAD 读取数据。
# @see _PACKET_HEAD
class PackInfo(object):
    ## 构造函数
    # @param self
    # @param lp_head_struct @ref _PACKET_HEAD 结构体指针
    # @see _PACKET_HEAD
    def __init__(self, lp_head_struct):
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
    
    ## 命令
    @property
    def cmd(self):
        return self.__cmd
    
    ## 命令类型
    @property
    def cmdType(self):
        return self.__cmdType
    
    ## 发送者客户端类型
    @property
    def srcUnitClientType(self):
        return self.__srcUnitClientType
    
    ## 发送者节点ID
    @property
    def srcUnitId(self):
        return self.__srcUnitId
    
    ## 发送者客户端ID
    @property
    def srcUnitClientId(self):
        return self.__srcUnitClientId
    
    ## 接收者客户端类型
    @property
    def dstUnitClientType(self):
        return self.__dstUnitClientType
    
    ## 接收者节点ID
    @property
    def dstUnitId(self):
        return self.__dstUnitId
    
    ## 接收者客户端ID
    @property
    def dstUnitClientId(self):
        return self.__dstUnitClientId
    
    ## 包长度
    @property
    def packetSize(self):
        return self.__packetSize
    
    ## 数据长度
    @property
    def dataLen(self):
        return self.__dataLen
