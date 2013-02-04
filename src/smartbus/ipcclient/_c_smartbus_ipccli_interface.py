#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on 2013-1-28

@author: lxy@hesong.net
'''

import sys

from ctypes import CDLL, RTLD_GLOBAL, Structure, \
    c_byte, c_char, c_ushort, c_int, c_long, c_void_p, \
    CFUNCTYPE, POINTER, c_char_p

from types import FunctionType, MethodType


#------------------------------------------------------------------------------ 
lib_filename = None
if 'posix' in sys.builtin_module_names:
    lib_filename = 'libbusipccli.so'
elif 'nt' in sys.builtin_module_names:
    lib_filename = 'busipccli.dll'

#===============================================================================
# library
#===============================================================================
_lib = None

#===============================================================================
# function
#===============================================================================
_c_fn_Init = None
_c_fn_Release = None
_c_fn_SetCallBackFn = None
_c_fn_CreateConnect = None
_c_fn_SendData = None
_c_fn_RemoteInvokeFlow = None

#===============================================================================
# structure
#===============================================================================

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


#===============================================================================
# call-back function type
#===============================================================================
_c_fntyp_connection_cb = CFUNCTYPE(c_int, c_void_p, c_int, c_int)
_c_fntyp_disconnect_cb = CFUNCTYPE(None, c_void_p)
_c_fntyp_recvdata_cb = CFUNCTYPE(None, c_void_p, POINTER(_struct_PACKET_HEAD), c_void_p, c_int)
_c_fntyp_invokeflow_ret_cb = CFUNCTYPE(None, c_void_p, c_byte, POINTER(_struct_PACKET_HEAD), c_char_p, c_int, c_int, c_char_p)

#===============================================================================
# function type and param flags
#===============================================================================
_c_fntyp_Init = CFUNCTYPE(c_int, c_int, c_int)
_paramflags_Init = (1, 'clienttype', 0), (1, 'clientid', 0)

_c_fntyp_Release = CFUNCTYPE(None)
_paramflags_Release = ()

_c_fntyp_SetCallBackFn = CFUNCTYPE(None, _c_fntyp_connection_cb, _c_fntyp_recvdata_cb, _c_fntyp_disconnect_cb, _c_fntyp_invokeflow_ret_cb, c_void_p)
_paramflags_SetCallBackFn = (1, 'client_conn_cb', _c_fntyp_connection_cb), (1, 'recv_cb', _c_fntyp_recvdata_cb), (1, 'disconnect_cb', _c_fntyp_disconnect_cb), (1, 'invokeflow_ret_cb', _c_fntyp_invokeflow_ret_cb), (1, 'arg', c_void_p)

_c_fntyp_CreateConnect = CFUNCTYPE(c_int , c_char_p, c_char_p, c_char_p)
_paramflags_CreateConnect = (1, 'author_username', c_char_p), (1, 'author_pwd', c_char_p), (1, 'add_info', c_char_p)

_c_fntyp_SendData = CFUNCTYPE(c_int, c_byte, c_byte, c_int, c_int, c_int, c_void_p, c_int)
_paramflags_SendData = (1, 'cmd', c_byte), (1, 'cmdtype', c_byte), (1, 'dst_unitid', c_int), (1, 'dst_clientid', c_int), (1, 'dst_clienttype', c_int), (1, 'data', c_void_p), (1, 'size', c_int)

_c_fntyp_RemoteInvokeFlow = CFUNCTYPE(c_int, c_int, c_int, c_char_p, c_char_p, c_int, c_int, c_char_p)
_paramflags_RemoteInvokeFlow = (1, 'server_unitid', c_int), (1, 'processindex', c_int), (1, 'projectid', c_char_p), (1, 'flowid', c_char_p), (1, 'mode', c_int), (1, 'timeout', c_int), (1, 'in_valuelist', c_char_p)


#===============================================================================
# load library function
#===============================================================================
def load_lib(filepath=lib_filename):
    if not filepath:
        filepath = lib_filename
    global _lib
    if not _lib:
        _lib = CDLL(filepath, mode=RTLD_GLOBAL)
        global _c_fn_Init
        _c_fn_Init = _c_fntyp_Init(('SmartBusIpcCli_Init', _lib), _paramflags_Init)
        global _c_fn_Release
        _c_fn_Release = _c_fntyp_Release(('SmartBusIpcCli_Release', _lib), _paramflags_Release)
        global _c_fn_SetCallBackFn
        _c_fn_SetCallBackFn = _c_fntyp_SetCallBackFn(('SmartBusIpcCli_SetCallBackFn', _lib), _paramflags_SetCallBackFn)
        global _c_fn_CreateConnect
        _c_fn_CreateConnect = _c_fntyp_CreateConnect(('SmartBusIpcCli_CreateConnect', _lib), _paramflags_CreateConnect)
        global _c_fn_SendData
        _c_fn_SendData = _c_fntyp_SendData(('SmartBusIpcCli_SendData', _lib), _paramflags_SendData)
        global _c_fn_RemoteInvokeFlow
        _c_fn_RemoteInvokeFlow = _c_fntyp_RemoteInvokeFlow(('SmartBusIpcCli_RemoteInvokeFlow', _lib), _paramflags_RemoteInvokeFlow)

    return _lib
