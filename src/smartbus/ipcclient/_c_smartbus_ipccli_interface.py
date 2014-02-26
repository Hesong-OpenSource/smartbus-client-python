# -*- coding: utf-8 -*-

''''smartbus 进程通信客户端C-API ctypes 对照翻译

使用ctypes将C-API的函数与基本数据结构做一对一的翻译，没有进行更进一步的包装。

:date: 2013-1-28
:author: lxy@heosng.net
'''

from __future__ import absolute_import, print_function

import sys
import os

from ctypes import CDLL, RTLD_GLOBAL, c_byte, c_int, c_void_p, CFUNCTYPE, c_char_p

from .._c_smartbus import _c_fntyp_connection_cb, _c_fntyp_disconnect_cb, _c_fntyp_recvdata_cb, _c_fntyp_invokeflow_ret_cb, _c_fntyp_global_connect_cb, _c_fntyp_trace_str_cb

if os.name in ('posix'):
    lib_filename = 'libbusipccli.so'
    '''smartbus IPC 客户端默认的共享/动态库文件名。在POSIX系统下，默认是 libbusipccli.so。'''
elif os.name in ("nt", "ce"):
    lib_filename = 'smartbus_ipc_cli.dll'
    '''smartbus IPC 客户端默认的共享/动态库文件名。在WINNT系统下，默认是 busipccli.dll。'''
else:
    raise NotImplementedError('Unsupported OS name "{}"'.format(os.name))
    
# # 共享/动态库
_lib = None

# # @name 库函数
# # @{

_c_fn_Init = None
_c_fn_Release = None
_c_fn_SetCallBackFn = None
_c_fn_CreateConnect = None
_c_fn_SendData = None
_c_fn_RemoteInvokeFlow = None
_c_fn_SendPing = None
_c_fn_SetTraceStr = None
_c_fn_SetCallBackFnEx = None

# # @}

# # @name 库函数类型
# # @{

_c_fntyp_Init = CFUNCTYPE(c_int, c_int, c_int)
_paramflags_Init = (1, 'clienttype', 0), (1, 'clientid', 0)

_c_fntyp_Release = CFUNCTYPE(None)
_paramflags_Release = ()

_c_fntyp_SetCallBackFn = CFUNCTYPE(None, _c_fntyp_connection_cb, _c_fntyp_recvdata_cb, _c_fntyp_disconnect_cb, _c_fntyp_invokeflow_ret_cb, _c_fntyp_global_connect_cb, c_void_p)
_paramflags_SetCallBackFn = (1, 'client_conn_cb', _c_fntyp_connection_cb), (1, 'recv_cb', _c_fntyp_recvdata_cb), (1, 'disconnect_cb', _c_fntyp_disconnect_cb), (1, 'invokeflow_ret_cb', _c_fntyp_invokeflow_ret_cb), (1, 'global_connect_cb', _c_fntyp_global_connect_cb), (1, 'arg', c_void_p)

_c_fntyp_CreateConnect = CFUNCTYPE(c_int , c_char_p, c_char_p, c_char_p)
_paramflags_CreateConnect = (1, 'author_username', c_char_p), (1, 'author_pwd', c_char_p), (1, 'add_info', c_char_p)

_c_fntyp_SendData = CFUNCTYPE(c_int, c_byte, c_byte, c_int, c_int, c_int, c_void_p, c_int)
_paramflags_SendData = (1, 'cmd', c_byte), (1, 'cmdtype', c_byte), (1, 'dst_unitid', c_int), (1, 'dst_clientid', c_int), (1, 'dst_clienttype', c_int), (1, 'data', c_void_p), (1, 'size', c_int)

_c_fntyp_RemoteInvokeFlow = CFUNCTYPE(c_int, c_int, c_int, c_char_p, c_char_p, c_int, c_int, c_char_p)
_paramflags_RemoteInvokeFlow = (1, 'server_unitid', c_int), (1, 'processindex', c_int), (1, 'projectid', c_char_p), (1, 'flowid', c_char_p), (1, 'mode', c_int), (1, 'timeout', c_int), (1, 'in_valuelist', c_char_p)

_c_fntyp_SendPing = CFUNCTYPE(c_int, c_byte, c_int, c_int, c_int, c_void_p, c_int)
_paramflags_SendPing = (1, 'local_clientid', c_byte), (1, 'dst_unitid', c_int), (1, 'dst_clientid', c_int), (1, 'dst_clienttype', c_int), (1, 'data', c_void_p), (1, 'size', c_int)

_c_fntyp_SetTraceStr = CFUNCTYPE(None, _c_fntyp_trace_str_cb, _c_fntyp_trace_str_cb)
_paramflags_SetTraceStr = (1, 'tracestr', _c_fntyp_trace_str_cb), (1, 'traceerr', _c_fntyp_trace_str_cb)

_c_fntyp_SetCallBackFnEx = CFUNCTYPE(None, c_char_p, c_void_p)
_paramflags_SetCallBackFnEx = (1, 'callback_name', c_char_p), (1, 'callbackfn', c_void_p)

# # @}

# # 加载共享/动态库
def load_lib(filepath=lib_filename):
    '''加载共享/动态库
    
    :param filepath: 动态/共享库文件名
    '''
    if not filepath:
        filepath = lib_filename
    global _lib
    if not _lib:
        try:
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
            global _c_fn_SendPing
            _c_fn_SendPing = _c_fntyp_SendPing(('SmartBusIpcCli_SendPing', _lib), _paramflags_SendPing)
            global _c_fn_SetTraceStr
            _c_fn_SetTraceStr = _c_fntyp_SetTraceStr(('SmartBusIpcCli_SetTraceStr', _lib), _paramflags_SetTraceStr)
            global _c_fn_SetCallBackFnEx
            _c_fn_SetCallBackFnEx = _c_fntyp_SetCallBackFnEx(('SmartBusIpcCli_SetCallBackFnEx', _lib), _paramflags_SetCallBackFnEx)
        except Exception as e:
            if _lib:
                _lib = None
            print(filepath, e, file=sys.stdout)
            raise
    return _lib
