# -*- coding: utf-8 -*-


__all__ = ['CFunc', 'declare', 'IpcFunc', 'NetFunc']


def declare(funcs):
    """decoration for :class:`CFunc`

    :param list funcs: The to-be-bind functions list

    Add the decorated :class:`CFunc` class into to-be-bind functions list
    """

    def adder(obj):
        funcs.append(obj)

    return adder


class CFunc:
    """C-API function definition

    .. warning:: Can **NOT** be used for callback functions
    """
    c_func = None
    prefix = ''
    func_name = ''
    argtypes = []
    restype = None

    @classmethod
    def bind(cls, dll):
        prefix = str(cls.prefix or '')
        func_name = str(cls.func_name or cls.__name__)
        cls.c_func = getattr(dll, '{0}{1}'.format(prefix, func_name))
        if cls.argtypes:
            cls.c_func.argtypes = cls.argtypes
        if cls.restype:
            cls.c_func.restype = cls.restype


class IpcFunc(CFunc):
    prefix = 'SmartBusIpcCli_'


class NetFunc(CFunc):
    prefix = 'SmartBusNetCli_'
