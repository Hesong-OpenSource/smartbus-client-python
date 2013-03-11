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
# 相当于：
## @code
#def ifnone(a, b):
#    if a is None:
#        return b
#    else:
#        return a
## @endcode
# @param a 第一个参数
# @param b 第二个参数
# @return 返回值
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

## 将unicode文本转为字节数组
# @param txt 要转换的文本
# @param encoding 转化所使用的编码
# @return 转换后的字节数组
def text_to_bytes(txt, encoding=default_encoding):
    data = None
    if txt is not None:
        if sys.version_info[0] < 3:
            import types
            if type(txt) == types.StringType:
                data = txt
            elif type(txt) == types.UnicodeType:
                data = txt.encode(encoding)
            else:
                raise TypeError('argument "text" must be StringType or UnicodeType')
        else:
            data = txt.encode(encoding)
    return data

## 将字节数组转为unicode文本
# @param data 要转换的字节数组
# @param encoding 转化所使用的编码
# @return 转换后的unicode文本
def bytes_to_text(data, encoding=default_encoding):
    txt = None
    if data is not None:
        txt = data.decode(encoding)
    return txt
