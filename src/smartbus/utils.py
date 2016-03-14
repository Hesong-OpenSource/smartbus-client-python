# -*- coding: utf-8 -*-

"""辅助功能
:date: 2013-3-4
:author: tanbro
"""

import sys

if sys.version_info[0] < 3:
    __all__ = ['default_encoding', 'ifnone', 'to_bytes', 'to_unicode', 'to_str']
else:
    __all__ = ['default_encoding', 'ifnone', 'unicode', 'to_bytes', 'to_unicode', 'to_str']

default_encoding = sys.getfilesystemencoding()
#: 默认编码
#:
#: :func:`sys.getfilesystemencoding` 的返回值

ifnone = lambda a, b: b if a is None else a
#: 如果第一个参数为None，则返回第二个参数，否则返回第一个参数
#: :param a: 第一个参数
#: :param b: 第二个参数
#: :return: 如果 a 为 None，则返回 b，否则返回 a。
#:
#: 相当于：
#:
#: .. code::
#:
#:     def ifnone(a, b):
#:        if a is None:
#:            return b
#:        else:
#:            return a
#:
#: 例如：
#:
#: .. code::
#:
#:     v1 = 1
#:     v2 = 2
#:     ifnone(v1, v2)
#:
#: 那么，返回值为1。
#:
#: 如果：
#:
#: .. code::
#:
#:     v1 = None
#:     v2 = 2
#:     ifnone(v1, v2)
#:
#: 那么，返回值为2。

if sys.version_info[0] < 3:
    def to_bytes(s, encoding=default_encoding):
        """将 `str` 转为 `bytes`

        :param s: 要转换的字符串
        :type s: str, unicode, bytes, None
        :param encoding: 编码，默认为系统编码。
        """
        if isinstance(s, (str, type(None))):
            return s
        elif isinstance(s, unicode):
            return s.encode(encoding)
        else:
            raise TypeError()


    def to_unicode(s, encoding=default_encoding):
        """将 `str` 转为 `unicode`

        :param s: 要转换的字符串
        :type s: str, unicode, bytes, None
        :param encoding: 编码，默认为系统编码。
        """
        if isinstance(s, (unicode, type(None))):
            return s
        elif isinstance(s, str):
            return s.decode(encoding)
        else:
            raise TypeError()


    to_str = to_bytes
    #: 将 `unicode` 或者 `bytes` 转为系统 `str`
else:
    unicode = str


    def to_bytes(s, encoding=default_encoding):
        """将 `str` 转为 `bytes`

        :param s: 要转换的字符串
        :type s: str, unicode, bytes, None
        :param encoding: 编码，默认为系统编码。
        """
        if isinstance(s, (bytes, type(None))):
            return s
        elif isinstance(s, str):
            return s.encode(encoding)
        else:
            raise TypeError()


    def to_unicode(s, encoding=default_encoding):
        """将 `str` 转为 `unicode`

        :param s: 要转换的字符串
        :type s: str, unicode, bytes, None
        :param encoding: 编码，默认为系统编码。
        """
        if isinstance(s, (str, type(None))):
            return s
        elif isinstance(s, bytes):
            return s.decode(encoding)
        else:
            raise TypeError()


    to_str = to_unicode
    #: 将 `unicode` 或者 `bytes` 转为系统 `str`
