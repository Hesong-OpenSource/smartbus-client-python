# -*- coding: utf-8 -*-

"""smartbus 的Python封装

包括 net 与 ipc 客户端的Python类型封装

:date: 2013-7-14
:author: 刘雪彦
"""

from __future__ import absolute_import

from .ipc import Client as IpcClient
from .net import Client as NetClient

__all__ = ['IpcClient', 'NetClient']

__version__ = '2.0.0'
