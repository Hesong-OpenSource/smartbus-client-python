
# 概述

smartbus-client-python 是和声(广州)的实时媒体流程服务器IPSC专用的消息总线客户端的Python包装。

它用于向Python开发者提供SmartBus的客户端功能。

# 特点

* 直接封装SmartBus的C语言实现客户端
* 采用Python标准库的ctypes进行C语言动态/共享库的封装。所以安装时不需要进行编译，可同时支持多种Python运行时（只要目标Python运行时支持ctypes）
* 完整的SmartBus客户端功能包装。其功能基本上与C语言实现客户端一对一。

# API 手册
http://smartbus-client-python.readthedocs.org/

# 参考
## SmartBus C语言实现客户端
https://github.com/Hesong-OpenSource/smartbus-client-sdk

# 安装

## 通过 PYPI 在线安装

```sh
pip install smartbus-client-python
```

## 下载后离线安装
下载程序包，解压，然后执行:

    python setup.py

