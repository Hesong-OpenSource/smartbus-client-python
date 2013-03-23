#-*- coding: utf-8 -*-

## @package smartbus.netclient
# smartbus 网络通信客户端的Python接口类
# @date 2013-2-3
#
# @author lxy@hesong.net


import os
import sys
from ctypes import create_string_buffer, string_at, byref, c_char, c_byte, c_int, c_long, c_ushort, c_void_p, c_char_p
from types import FunctionType, MethodType

if sys.version_info[0] < 3:
    import _c_smartbus_netcli_interface as sbncif
    from smartbus import PackInfo
    from smartbus.utils import default_encoding, to_str, to_bytes
else:
    from . import _c_smartbus_netcli_interface as sbncif
    from .. import PackInfo
    from ..utils import default_encoding, to_str, to_bytes

## SmartBus Network 客户端类
#
# 这个类封装了 SmartBus Network 客户端的一系列方法与事件
class Client(object):
    __lib = None
    __unitid = None
    __instances = {}

    ## 构造函数
    #
    # @param localClientId 客户端的ID
    # @param localClientType 客户端的类型标志
    # @param masterHost 客户端所要连接的主服务器
    # @param masterPort 客户端所要连接的主服务器端口
    # @param slaverHost 客户端所要连接的从服务器
    # @param slaverPort 客户端所要连接的从服务器端口
    # @param authorUsr 登录名
    # @param authorPwd 密码
    # @param extInfo 附加信息
    # @param encoding 收/发字符串时使用的编码。默认为 @ref smartbus.utils.default_encoding
    # @see localClientId @see localClientType @see masterHost @see masterPort @see slaverHost @see slaverPort @see authorUsr @see authorPwd @see extInfo @see encoding
    def __init__(self, localClientId, localClientType, masterHost, masterPort, slaverHost=None, slaverPort=0, authorUsr=None, authorPwd=None, extInfo=None, encoding=default_encoding):
        if not Client.isInitialized():
            raise NotInitializedError()
        cls = type(self)
        if localClientId in cls.__instances:
            raise AlreadyExistsError()
        cls.__instances[localClientId] = self
        self.__localClientId = localClientId
        self.__localClientType = localClientType
        self.__masterHost = masterHost
        self.__masterPort = masterPort
        self.__slaverHost = slaverHost
        self.__slaverPort = slaverPort
        self.__authorUsr = authorUsr
        self.__authorPwd = authorPwd
        self.__extInfo = extInfo
        self.__encoding = encoding
        self.__c_localClientId = c_byte(self.__localClientId)
        self.__c_localClientType = c_long(self.__localClientType)
        self.__c_masterHost = c_char_p(to_bytes(self.__masterHost, self.encoding))
        self.__c_masterPort = c_ushort(self.__masterPort)
        self.__c_slaverHost = c_char_p(to_bytes(self.__slaverHost, self.encoding))
        self.__c_slaverPort = c_ushort(self.__slaverPort)
        self.__c_authorUsr = c_char_p(to_bytes(self.__authorUsr, self.encoding))
        self.__c_authorPwd = c_char_p(to_bytes(self.__authorPwd, self.encoding))
        self.__c_extInfo = c_char_p(to_bytes(self.__extInfo, self.encoding))

    ## 初始化
    #
    # 调用其他方法前，必须首先初始化库
    # @param cls
    # @param unitid 单元ID。在所连接到的SmartBus服务器上，每个客户端进程的单元ID都必须是全局唯一的。
    # @param libraryfile 库文件。如果不指定该参数，则加载时，会自动搜索库文件，其搜索的目录次序为：系统目录、当前目录、运行目录、文件目录。@see _c_smartbus_netcli_interface.lib_filename
    @classmethod
    def initialize(cls, unitid, libraryfile=sbncif.lib_filename):
        if cls.__unitid is not None:
            raise AlreadyInitializedError()
        if not libraryfile:
            libraryfile = sbncif.lib_filename
        try:
            cls.__lib = sbncif.load_lib(libraryfile)
        except:
            try:
                cls.__lib = sbncif.load_lib(os.path.join(os.path.curdir, libraryfile))
            except:
                try:
                    cls.__lib = sbncif.load_lib(os.path.join(os.getcwd(), libraryfile))
                except:
                    try:
                        cls.__lib = sbncif.load_lib(os.path.join(os.path.dirname(__file__), libraryfile))
                    except:
                        raise
        sbncif._c_fn_Init(unitid)
        cls.__unitid = unitid
        cls.__c_fn_connection_cb = sbncif._c_fntyp_connection_cb(cls.__connection_cb)
        cls.__c_fn_recvdata_cb = sbncif._c_fntyp_recvdata_cb(cls.__recvdata_cb)
        cls.__c_fn_disconnect_cb = sbncif._c_fntyp_disconnect_cb(cls.__disconnect_cb)
        cls.__c_fn_invokeflow_ret_cb = sbncif._c_fntyp_invokeflow_ret_cb(cls.__invokeflow_ret_cb)
        sbncif._c_fn_SetCallBackFn(
            cls.__c_fn_connection_cb,
            cls.__c_fn_recvdata_cb,
            cls.__c_fn_disconnect_cb,
            cls.__c_fn_invokeflow_ret_cb,
            c_void_p(None)
        )

    ## 释放库
    #
    # @param cls
    @classmethod
    def finalize(cls):
        cls.__instances.clear()
        if cls.__unitid is not None:
            sbncif._c_fn_Release()
            cls.__unitid = None

    @classmethod
    def isInitialized(cls):
        return cls.__unitid is not None

    @classmethod
    def getUnitId(cls):
        return cls.__unitid

    @classmethod
    def __connection_cb(cls, arg, local_clientid, accesspoint_unitid, ack):
        inst = cls.__instances.get(local_clientid, None)
        if inst is not None:
            if ack == 0:  # 连接成功
                if hasattr(inst, 'onConnectSuccess'):
                    inst.onConnectSuccess(accesspoint_unitid)
            else:  # 连接失败
                if hasattr(inst, 'onConnectFail'):
                    inst.onConnectFail(accesspoint_unitid, ack)

    @classmethod
    def __disconnect_cb(cls, param, local_clientid):
        inst = cls.__instances.get(local_clientid, None)
        if inst is not None:
            if hasattr(inst, 'onDisconnect'):
                inst.onDisconnect()

    ## @todo: TODO: 广播的处理
    @classmethod
    def __recvdata_cb(cls, param, local_clientid, head, data, size):
        inst = cls.__instances.get(local_clientid, None)
        if inst is not None:
            if hasattr(inst, 'onReceiveText'):
                packInfo = PackInfo(head)
                txt = None
                if data:
                    txt = to_str(string_at(data, size), inst.encoding)
                    txt = txt.strip('\x00')
                    inst.onReceiveText(packInfo, txt)

    @classmethod
    def __invokeflow_ret_cb(cls, arg, local_clientid, head, projectid, invoke_id, ret, param):
        inst = cls.__instances.get(local_clientid, None)
        if inst is not None:
            if ret == 1:
                if hasattr(inst, 'onInvokeFlowRespond'):
                    packInfo = PackInfo(head)
                    txt_projectid = to_str(projectid, inst.encoding)
                    txt_param = to_str(param, inst.encoding)
                    py_param = eval(txt_param)
                    inst.onInvokeFlowRespond(packInfo, txt_projectid, invoke_id, py_param)
            elif ret == -1:
                if hasattr(inst, 'onInvokeFlowTimeout'):
                    txt_projectid = to_str(projectid, inst.encoding)
                    packInfo = PackInfo(head)
                    inst.onInvokeFlowTimeout(packInfo, txt_projectid, invoke_id)

    ## 客户端ID
    # @param self
    @property
    def localClientId(self):
        return self.__localClientId

    ## 客户端类型
    # @param self
    @property
    def localClientType(self):
        return self.__localClientType

    ## SmartBus 服务主机名
    # @param self
    @property
    def masterHost(self):
        return self.__masterHost

    ## SmartBus 服务端口
    # @param self
    @property
    def masterPort(self):
        return self.__masterPort

    ## SmartBus 从服务主机名
    # @param self
    @property
    def slaverHost(self):
        return self.__slaverHost

    ## SmartBus 从服务端口
    # @param self
    @property
    def slaverPort(self):
        return self.__slaverPort

    ## 登录名
    # @param self
    @property
    def authorUsr(self):
        return self.__authorUsr

    ## 密码
    # @param self
    @property
    def authorPwd(self):
        return self.__authorPwd

    ## 连接附加信息
    # @param self
    @property
    def extInfo(self):
        return self.__extInfo

    ## 收/发字符串时使用的编码。默认为 utils.default_encoding。
    # @param self
    @property
    def encoding(self):
        return self.__encoding

    ## 连接成功事件
    # @param self
    # @param unitId 单元ID
    def onConnectSuccess(self, unitId):
        pass

    ## 连接失败事件
    # @param self
    # @param unitId 单元ID
    # @param errno 错误编码
    def onConnectFail(self, unitId, errno):
        pass

    ## 连接中断事件
    # @param self
    def onDisconnect(self):
        pass

    ## 收到文本事件
    # @param self
    # @param packInfo 数据包信息
    # @param txt 收到的文本
    # @see PackInfo
    def onReceiveText(self, packInfo, txt):
        pass

    ## 收到流程返回数据事件
    # @param self
    # @param packInfo 数据包信息。
    # @param project 流程所在的项目
    # @param invokeId 调用ID。它对应于 @ref invokeFlow "invokeFlow 方法"返回的ID
    # @param result 返回的数据。是一个Python对象。通常是一个list
    # @see PackInfo
    def onInvokeFlowRespond(self, packInfo, project, invokeId, result):
        pass

    ## 流程返回超时事件
    # @param self
    # @param packInfo 数据包信息。
    # @param project 流程所在的项目
    # @param invokeId 调用ID。它对应于该对象的 @ref invokeFlow "invokeFlow() 方法"返回值
    # @see PackInfo
    def onInvokeFlowTimeout(self, packInfo, project, invokeId):
        pass

    ## 释放客户端
    #
    # @param  self
    def dispose(self):
        cls = type(self)
        cls.__instances.pop(self.__localClientId, None)

    ## 连接到服务器
    #
    # 如果连接失败，则抛出 @ref ConnectError 异常。
    def connect(self):
        result = sbncif._c_fn_CreateConnect(
            self.__c_localClientId,
            self.__c_localClientType,
            self.__c_masterHost,
            self.__c_masterPort,
            self.__c_slaverHost,
            self.__c_slaverPort,
            self.__c_authorUsr,
            self.__c_authorPwd,
            self.__c_extInfo
        )
        if result != 0:
            raise ConnectError()

    ## 发送文本
    #
    # 如果连接失败，则抛出 @ref SendDataError 异常
    # @param self
    # @param cmd 命令
    # @param cmdType 命令类型
    # @param dstUnitId 目标节点ID
    # @param dstClientId 目标客户端ID
    # @param dstClientType 目标客户端类型
    # @param txt 待发送文本
    # @param encoding 文本的编码。默认为该对象的 @ref encoding "编码"属性。
    def sendText(self, cmd, cmdType, dstUnitId, dstClientId, dstClientType, txt, encoding=None):
        if not encoding:
            encoding = self.encoding
        data = to_bytes(txt, encoding)
        data_pc = create_string_buffer(data) if data else None
        data_sz = len(data_pc) if data_pc else 0
        result = sbncif._c_fn_SendData(
            self.__c_localClientId,
            c_byte(cmd),
            c_byte(cmdType),
            c_int(dstUnitId),
            c_int(dstClientId),
            c_int(dstClientType),
            byref(data_pc),
            c_int(data_sz)
        )
        if result != 0:
            raise SendDataError('SmartBusNetCli_SendData() returns %d' % (result))

    ## 发送二进制数据
    #
    # 如果连接失败，则抛出 @ref SendDataError 异常
    # @param self
    # @param cmd 命令
    # @param cmdType 命令类型
    # @param dstUnitId 目标节点ID
    # @param dstClientId 目标客户端ID
    # @param dstClientType 目标客户端类型
    # @param data 待发送数据。必须是bytes类型。
    def sendBytes(self, cmd, cmdType, dstUnitId, dstClientId, dstClientType, data):
        result = sbncif._c_fn_SendData(
            c_byte(cmd),
            c_byte(cmdType),
            c_int(dstUnitId),
            c_int(dstClientId),
            c_int(dstClientType),
            c_char_p(data),
            c_int(len(data) if data else 0)
        )
        if result != 0:
            raise SendDataError('SmartBusNetCli_SendData() returns %d' % (result))

    ## 调用流程
    #
    # 如果连接失败，则抛出 @ref SendDataError 异常
    # @param self
    # @param server IPSC流程服务所在节点
    # @param process IPSC进程索引值
    # @param project 流程项目名称
    # @param flow 流程名称
    # @param parameters 流程传入参数
    # @param isNeedReturn 是否需要流程返回值
    # @param timeout 等待流程返回超时值，单位为秒。
    # @param encoding 文本的编码。默认为该对象的 @ref encoding 属性。
    # @return 当需要等待流程返回值时，该返回值是@ref onInvokeFlowRespond "流程返回事件"中对应的ID.
    def invokeFlow(self, server, process, project, flow, parameters=[], isNeedReturn=True, timeout=30, encoding=None):
        if not encoding:
            encoding = self.encoding
        c_server_unitid = c_int(server)
        c_processindex = c_int(process)
        c_project_id = c_char_p(to_bytes(project, encoding))
        c_flowid = c_char_p(to_bytes(flow, encoding))
        c_invoke_mode = c_int(0) if isNeedReturn else c_int(1)
        c_timeout = c_int(int(timeout * 1000))
        if parameters is None:
            parameters = []
        else:
            if isinstance(parameters, (int, float, str, bool , dict)):
                parameters = [parameters]
            else:
                parameters = list(parameters)
        c_in_valuelist = c_char_p(to_bytes(str(parameters), encoding))
        result = sbncif._c_fn_RemoteInvokeFlow(
            self.__c_localClientId,
            c_server_unitid,
            c_processindex,
            c_project_id,
            c_flowid,
            c_invoke_mode,
            c_timeout,
            c_in_valuelist
        )
        if result <= 0:
            raise SendDataError('SmartBusNetCli_RemoteInvokeFlow reutrns %d' % (result))
        return result


## @name 异常类
## @{

## @exception 已经初始化，无法重复的初始化
class AlreadyInitializedError(Exception):
    pass

## @exception 尚未初始化，无法使用
class NotInitializedError(Exception):
    pass

## @exception 对象已经存在，无法再次新建
class AlreadyExistsError(Exception):
    pass

## @exception 连接服务器错误
class ConnectError(Exception):
    pass

## @exception 发送数据错误
class SendDataError(Exception):
    pass

## @}
