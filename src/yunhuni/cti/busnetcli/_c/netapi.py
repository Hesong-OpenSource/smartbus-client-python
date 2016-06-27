# -*- coding: utf-8 -*-

"""
ctypes for network client API.
"""

from __future__ import absolute_import

from ctypes import c_int, c_void_p, c_char_p, c_byte, c_ushort

from .helper import NetFunc as ApiFunc, declare
from .mutual import *

#: Default so/dll name
DLL_NAME = 'busnetcli'

#: global C-API function wrapper class list
funcs = []


def get_function_declarations():
    return funcs


@declare(funcs)
class Init(ApiFunc):
    argtypes = [c_byte]
    restype = c_int


@declare(funcs)
class Release(ApiFunc):
    pass


@declare(funcs)
class SetCallBackFn(ApiFunc):
    argtypes = [fntyp_connection_cb, fntyp_recvdata_cb, fntyp_disconnect_cb, fntyp_invokeflow_ret_cb,
                fntyp_global_connect_cb, c_void_p]


@declare(funcs)
class SetCallBackFnArg(ApiFunc):
    argtypes = [c_void_p]


@declare(funcs)
class SetCallBackFnEx(ApiFunc):
    argtypes = [c_char_p, c_void_p]


@declare(funcs)
class CreateConnect(ApiFunc):
    argtypes = [c_byte, c_int, c_char_p, c_ushort, c_char_p, c_ushort, c_char_p, c_char_p, c_char_p]
    restype = c_int


@declare(funcs)
class SendData(ApiFunc):
    argtypes = [c_byte, c_byte, c_byte, c_int, c_int, c_int, c_void_p, c_int]
    restype = c_int


@declare(funcs)
class RemoteInvokeFlow(ApiFunc):
    argtypes = [c_byte, c_int, c_int, c_char_p, c_char_p, c_int, c_int, c_char_p]
    restype = c_int


@declare(funcs)
class SendPing(ApiFunc):
    argtypes = [c_byte, c_int, c_int, c_int, c_void_p, c_int]
    restype = c_int


@declare(funcs)
class SendNotify(ApiFunc):
    argtypes = [c_byte, c_int, c_int, c_char_p, c_char_p, c_int, c_int, c_char_p]
    restype = c_int
