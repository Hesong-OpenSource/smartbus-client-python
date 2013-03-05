# -*- coding: utf-8 -*-

##@package _c_smartbus_netcli_interface
#smartbus 网络通信客户端C-API ctypes 对照翻译
#
#使用ctypes将C-API的函数与基本数据结构做一对一的翻译，没有进行更进一步的包装。
#
#@date 2013-2-3
#@author lxy@heosng.net

import sys
    
from ctypes import CDLL, RTLD_GLOBAL, c_byte, c_int, c_void_p, CFUNCTYPE, c_char_p, c_ushort, c_long
if sys.version_info[0] < 3:
    from smartbus import  _c_fntyp_connection_cb, _c_fntyp_disconnect_cb, _c_fntyp_recvdata_cb, _c_fntyp_invokeflow_ret_cb
else:
    from .. import _c_fntyp_connection_cb, _c_fntyp_disconnect_cb, _c_fntyp_recvdata_cb, _c_fntyp_invokeflow_ret_cb


lib_filename = None
if 'posix' in sys.builtin_module_names:
    lib_filename = 'libbusipccli.so'
elif 'nt' in sys.builtin_module_names:
    lib_filename = 'smartbus_net_cli.dll'

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
# function type and param flags
#===============================================================================
_c_fntyp_Init = CFUNCTYPE(c_int, c_byte)
_paramflags_Init = (1, 'unitid', 0),

_c_fntyp_Release = CFUNCTYPE(None)
_paramflags_Release = ()

_c_fntyp_SetCallBackFn = CFUNCTYPE(None, _c_fntyp_connection_cb, _c_fntyp_recvdata_cb, _c_fntyp_disconnect_cb, _c_fntyp_invokeflow_ret_cb, c_void_p)
_paramflags_SetCallBackFn = (1, 'client_conn_cb', _c_fntyp_connection_cb), (1, 'recv_cb', _c_fntyp_recvdata_cb), (1, 'disconnect_cb', _c_fntyp_disconnect_cb), (1, 'invokeflow_ret_cb', _c_fntyp_invokeflow_ret_cb), (1, 'arg', c_void_p)

_c_fntyp_CreateConnect = CFUNCTYPE(c_int, c_byte , c_long, c_char_p, c_ushort, c_char_p, c_ushort, c_char_p, c_char_p, c_char_p)
_paramflags_CreateConnect = (1, 'local_clientid', c_byte), (1, 'local_clienttype', c_long), (1, 'masterip', c_char_p), (1, 'masterport', c_ushort), (1, 'slaveip', c_char_p), (1, 'slaveport', c_ushort), (1, 'author_username', c_char_p), (1, 'author_pwd', c_char_p), (1, 'add_info', c_char_p)

_c_fntyp_SendData = CFUNCTYPE(c_int, c_byte, c_byte, c_byte, c_int, c_int, c_int, c_void_p, c_int)
_paramflags_SendData = (1, 'local_clientid', c_byte), (1, 'cmd', c_byte), (1, 'cmdtype', c_byte), (1, 'dst_unitid', c_int), (1, 'dst_clientid', c_int), (1, 'dst_clienttype', c_int), (1, 'data', c_void_p), (1, 'size', c_int)

_c_fntyp_RemoteInvokeFlow = CFUNCTYPE(c_int, c_byte, c_int, c_int, c_char_p, c_char_p, c_int, c_int, c_char_p)
_paramflags_RemoteInvokeFlow = (1, 'local_clientid', c_byte), (1, 'server_unitid', c_int), (1, 'processindex', c_int), (1, 'projectid', c_char_p), (1, 'flowid', c_char_p), (1, 'mode', c_int), (1, 'timeout', c_int), (1, 'in_valuelist', c_char_p)

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
        _c_fn_Init = _c_fntyp_Init(('SmartBusNetCli_Init', _lib), _paramflags_Init)
        global _c_fn_Release
        _c_fn_Release = _c_fntyp_Release(('SmartBusNetCli_Release', _lib), _paramflags_Release)
        global _c_fn_SetCallBackFn
        _c_fn_SetCallBackFn = _c_fntyp_SetCallBackFn(('SmartBusNetCli_SetCallBackFn', _lib), _paramflags_SetCallBackFn)
        global _c_fn_CreateConnect
        _c_fn_CreateConnect = _c_fntyp_CreateConnect(('SmartBusNetCli_CreateConnect', _lib), _paramflags_CreateConnect)
        global _c_fn_SendData
        _c_fn_SendData = _c_fntyp_SendData(('SmartBusNetCli_SendData', _lib), _paramflags_SendData)
        global _c_fn_RemoteInvokeFlow
        _c_fn_RemoteInvokeFlow = _c_fntyp_RemoteInvokeFlow(('SmartBusNetCli_RemoteInvokeFlow', _lib), _paramflags_RemoteInvokeFlow)

    return _lib

