#-*- coding: utf-8 -*-

## @package smartbus
# smartbus.h 的Python封装

from ctypes import CDLL, RTLD_GLOBAL, CFUNCTYPE, Structure, POINTER, c_byte, c_char, c_ushort, c_int, c_long, c_void_p, c_char_p

## @name 结构体
## @{

## 接收数据包结构体的 pyton ctypes 封装类
# @see PackInfo
class _struct_PACKET_HEAD(Structure):
    _pack_ = 1  # 设定为1字节对齐
    _fields_ = [
        ('head_flag', c_ushort),  # // 头标识    : 0x5b15
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

_c_fntyp_connection_cb = CFUNCTYPE(None, c_void_p, c_byte, c_int, c_int)
_c_fntyp_disconnect_cb = CFUNCTYPE(None, c_void_p, c_byte)
_c_fntyp_recvdata_cb = CFUNCTYPE(None, c_void_p, c_byte, POINTER(_struct_PACKET_HEAD), c_void_p, c_int)
_c_fntyp_invokeflow_ret_cb = CFUNCTYPE(None, c_void_p, c_byte, POINTER(_struct_PACKET_HEAD), c_char_p, c_int, c_int, c_char_p)

## @}


## 接收数据包信息
#
# 每当接收到数据时，所触发的事件中，都包含该类型的参数，记录了一些数据包的相关信息。
# 它是结构体封装类 @ref _struct_PACKET_HEAD 的再次封装类。使用它可以安全的从 @ref _struct_PACKET_HEAD 读取数据。
# @see _struct_PACKET_HEAD
class PackInfo(object):
    ## 构造函数
    # @param self
    # @param lp_head_struct @ref _struct_PACKET_HEAD 结构体指针
    # @see _struct_PACKET_HEAD
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
