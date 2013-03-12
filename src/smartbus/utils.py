#-*- coding: utf-8 -*-

## @package smartbus.utils
# 辅助功能
#@date 2013-3-4
#
#@author tanbro

import sys

## 默认编码。默认为操作系统的编码
default_encoding = sys.getfilesystemencoding()

## 如果第一个参数为None，则返回第二个参数，否则返回第一个参数
#
# @param a 第一个参数
# @param b 第二个参数
# @return 如果 a 为 None，则返回 b，否则返回 a。
#
# 相当于：
## @code
#def ifnone(a, b):
#    if a is None:
#        return b
#    else:
#        return a
## @endcode
#
# 例如：
## @code
#v1 = 1
#v2 = 2
#ifnone(v1, v2)
## @endcode
#那么，返回值为1。
#\n如果：
## @code
#v1 = None
#v2 = 2
#ifnone(v1, v2)
## @endcode
#那么，返回值为2。
ifnone = lambda a, b: b if a is None else a

def to_str(data, encoding=default_encoding):
    if data is None:
        return data
    if sys.version_info[0] < 3:
        if isinstance(data, str):
            return data
        elif isinstance(data, unicode):
            return data.encode(encoding)
        else:
            raise TypeError()
    else:
        if isinstance(data, str):
            return data
        elif isinstance(data, bytes):
            return data.decode(encoding)
        else:
            raise TypeError()

def to_bytes(data, encoding=default_encoding):
    if data is None:
        return data
    if sys.version_info[0] < 3:
        if isinstance(data, str):
            return data
        elif isinstance(data, unicode):
            return data.encode(encoding)
        else:
            raise TypeError()
    else:
        if isinstance(data, str):
            return data.encode(encoding)
        elif isinstance(data, bytes):
            return data
        else:
            raise TypeError()

