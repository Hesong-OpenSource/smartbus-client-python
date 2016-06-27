yunhuni.cti.busnetcli
#######################
`yunhuni.cti.busnetcli` 是实时媒体流程服务器IPSC专用的消息总线客户端的Python包装。

它用于向Python开发者提供SmartBus的客户端功能。

这个库最初的开源项目是 https://github.com/Hesong-OpenSource/smartbus-client-python

特点
****

* 直接封装SmartBus的C语言实现客户端
* 采用Python标准库的ctypes进行C语言动态/共享库的封装。所以安装时不需要进行编译，理论上同时支持多种Python（如pypy,ironpython,jython）运行时（只要目标Python运行时支持ctypes）
* 完整的SmartBus客户端功能包装。其功能基本上与C语言实现客户端一对一。

.. attention::

    在安装好 Python 程序包之后，还需要下载目标平台的动态/共享库，并将DLL或者SO文件复制到运行目录。
    访问 https://github.com/Hesong-OpenSource/smartbus-client-sdk 可下载库文件

修改
******
本项目在原基础上，加上了针对 http://git.liushuixingyun.com/projects/YHN/repos/yunhuni-peer-comm-cti-flow/ 所实现接口的修改。

作用
******
开发人员可以使用这个库，快速的构建 http://git.liushuixingyun.com/projects/YHN/repos/yunhuni-peer-comm-cti-flow/ 的：

* 交互式控制台调试程序
* 自动化单元测试
* 性能测试脚本
