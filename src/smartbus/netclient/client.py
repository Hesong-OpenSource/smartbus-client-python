# -*- coding: utf-8 -*-

'''smartbus 网络通信客户端的Python接口类客户端类型

:author: 刘雪彦
:date: 2013-6-8
'''

from __future__ import absolute_import

import os
import platform
import logging
from ctypes import create_string_buffer, string_at, byref, c_byte, c_int, c_long, c_ushort, c_void_p, c_char_p

import json

from . import _c_smartbus_netcli_interface as sbncif
from .._c_smartbus import PackInfo, SMARTBUS_ERR_OK, SMARTBUS_NODECLI_TYPE_IPSC, SMARTBUS_ERR_TIMEOUT
from ..utils import default_encoding, to_str, to_bytes
from .. import errors

class Client(object):
    '''SmartBus Network 客户端类

    这个类封装了 SmartBus Network 客户端的一系列方法与事件
    '''
    __lib = None
    __unitid = None
    __instances = {}
    __onglobalconnect = None

    def __init__(self, localClientId, localClientType, masterHost, masterPort, slaverHost=None, slaverPort=0xffff, authorUsr=None, authorPwd=None, extInfo=None, encoding=default_encoding):
        '''构造函数

        :param localClientId:客户端的ID
        :param localClientType:客户端的类型标志
        :param masterHost:客户端所要连接的主服务器
        :param masterPort:客户端所要连接的主服务器端口
        :param slaverHost:客户端所要连接的从服务器
        :param slaverPort:客户端所要连接的从服务器端口
        :param authorUsr:登录名
        :param authorPwd:密码
        :param extInfo:附加信息
        :param encoding:收/发字符串时使用的编码。默认为 :data:`smartbus.utils.default_encoding`
        '''
        if not Client.isInitialized():
            raise errors.NotInitializedError()
        cls = type(self)
        if localClientId in cls.__instances:
            raise errors.AlreadyExistsError()
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


    @classmethod
    def initialize(cls, unitid, onglobalconnect=None, libraryfile=sbncif.lib_filename, logging_option=(True, logging.DEBUG, logging.ERROR)):
        '''初始化

        调用其他方法前，必须首先初始化库

        :param unitid:单元ID。在所连接到的SmartBus服务器上，每个客户端进程的单元ID都必须是全局唯一的。
        :param onglobalconnect:全局连接事件回调函数
        :param libraryfile:库文件。如果不指定该参数，则加载时，会自动搜索库文件，其搜索的目录次序为：系统目录、../cdll/${system}/${machine}、 运行目录、当前目录、本文件目录。见 :data:`_c_smartbus_netcli_interface.lib_filename`
        :param logging_option:
        '''
        if cls.__unitid is not None:
            raise errors.AlreadyInitializedError()
#        if not isinstance(unitid, int):
#            raise TypeError('The argument "unit" should be an integer')
        cls.__logging_option = logging_option
        cls.__logger = logging.getLogger('{}.{}'.format(cls.__module__, cls.__qualname__ if hasattr(cls, '__qualname__') else cls.__name__))
        cls.__logger.info('initialize')
        if not libraryfile:
            libraryfile = sbncif.lib_filename
        try:
            fpath = libraryfile
            cls.__logger.warn(u'load %s', fpath)
            cls.__lib = sbncif.load_lib(fpath)
        except:
            try:
                fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cdll', platform.system(), platform.machine(), libraryfile)
                cls.__logger.warn(u'load %s', fpath)
                cls.__lib = sbncif.load_lib(fpath)
            except:
                try:
                    fpath = os.path.join(os.getcwd(), libraryfile)
                    cls.__logger.warn(u'load %s', fpath)
                    cls.__lib = sbncif.load_lib(fpath)
                except:
                    try:
                        fpath = os.path.join(os.path.curdir, libraryfile)
                        cls.__logger.warn(u'load %s', fpath)
                        cls.__lib = sbncif.load_lib(fpath)
                    except:
                        fpath = os.path.join(os.path.dirname(os.path.abspath(__file__)), libraryfile)
                        cls.__logger.warn(u'load %s', fpath)
                        cls.__lib = sbncif.load_lib(fpath)
        errors.check_restval(sbncif._c_fn_Init(unitid))
        cls.__unitid = unitid
        cls.__onglobalconnect = onglobalconnect
        cls.__c_fn_connection_cb = sbncif._c_fntyp_connection_cb(cls.__connection_cb)
        cls.__c_fn_recvdata_cb = sbncif._c_fntyp_recvdata_cb(cls.__recvdata_cb)
        cls.__c_fn_disconnect_cb = sbncif._c_fntyp_disconnect_cb(cls.__disconnect_cb)
        cls.__c_fn_invokeflow_ret_cb = sbncif._c_fntyp_invokeflow_ret_cb(cls.__invokeflow_ret_cb)
        cls.__c_fn_invokeflow_ack_cb = sbncif._c_fntyp_invokeflow_ret_cb(cls.__invokeflow_ack_cb)
        cls.__c_fn_global_connect_cb = sbncif._c_fntyp_global_connect_cb(cls.__global_connect_cb)
        sbncif._c_fn_SetCallBackFn(
            cls.__c_fn_connection_cb,
            cls.__c_fn_recvdata_cb,
            cls.__c_fn_disconnect_cb,
            cls.__c_fn_invokeflow_ret_cb,
            cls.__c_fn_global_connect_cb,
            c_void_p(None)
        )
        sbncif._c_fn_SetCallBackFnEx(c_char_p(b"smartbus_invokeflow_ack_cb"), cls.__c_fn_invokeflow_ack_cb)
        if logging_option[0]:
            cls.__c_fn_trace_cb = sbncif._c_fntyp_trace_str_cb(cls.__trace_cb)
            cls.__c_fn_traceerr_cb = sbncif._c_fntyp_trace_str_cb(cls.__traceerr_cb)
            sbncif._c_fn_SetTraceStr(cls.__c_fn_trace_cb, cls.__c_fn_traceerr_cb)

    @classmethod
    def finalize(cls):
        '''释放库
        '''
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
            inst._unitid = accesspoint_unitid
            if ack == SMARTBUS_ERR_OK:  # 连接成功
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

    # # @todo: TODO: 广播的处理
    @classmethod
    def __recvdata_cb(cls, param, local_clientid, head, data, size):
        inst = cls.__instances.get(local_clientid, None)
        if inst is not None:
            if hasattr(inst, 'onReceiveText'):
                packInfo = PackInfo(head)
                txt = None
                if data:
                    bytestr = string_at(data, size)
                    bytestr = bytestr.strip(b'\x00')
                    if packInfo.srcUnitClientType == SMARTBUS_NODECLI_TYPE_IPSC:
                        try:
                            txt = to_str(bytestr, 'cp936')
                        except UnicodeDecodeError:
                            txt = to_str(bytestr, 'utf8')
                    else:
                        txt = to_str(bytestr, inst.encoding)
                inst.onReceiveText(packInfo, txt)

    @classmethod
    def __invokeflow_ret_cb(cls, arg, local_clientid, head, projectid, invoke_id, ret, param):
        inst = cls.__instances.get(local_clientid, None)
        if inst is not None:
            if ret == 1:
                if hasattr(inst, 'onInvokeFlowRespond'):
                    packInfo = PackInfo(head)
                    txt_projectid = to_str(projectid, 'cp936').strip('\x00')
                    txt_param = to_str(param, 'cp936').strip('\x00').strip()
                    if txt_param:
                        py_param = json.loads(txt_param)
                    else:
                        py_param = None
                    inst.onInvokeFlowRespond(packInfo, txt_projectid, invoke_id, py_param)
            elif ret == SMARTBUS_ERR_TIMEOUT:
                if hasattr(inst, 'onInvokeFlowTimeout'):
                    packInfo = PackInfo(head)
                    txt_projectid = to_str(projectid, 'cp936').strip('\x00')
                    inst.onInvokeFlowTimeout(packInfo, txt_projectid, invoke_id)
            else:
                if hasattr(inst, 'onInvokeFlowError'):
                    packInfo = PackInfo(head)
                    txt_projectid = to_str(projectid, 'cp936').strip('\x00')
                    inst.onInvokeFlowError(packInfo, txt_projectid, invoke_id, ret)

    @classmethod
    def __invokeflow_ack_cb(cls, arg, local_clientid, head, projectid, invoke_id, ack, msg):
        inst = cls.__instances.get(local_clientid, None)
        if inst is not None:
            if hasattr(inst, 'onInvokeFlowAcknowledge'):
                packInfo = PackInfo(head)
                txt_projectid = to_str(projectid, 'cp936').strip('\x00')
                txt_msg = to_str(msg, 'cp936').strip('\x00')
                inst.onInvokeFlowAcknowledge(packInfo, txt_projectid, invoke_id, ack, txt_msg)

    @classmethod
    def __global_connect_cb(cls, arg, unitid, clientid, clienttype, accessunit, status, ext_info):
        if callable(cls.__onglobalconnect):
#             if sys.version_info[0] < 3:
#                 inst = None
#                 if len(cls.__instances) > 0:
#                     for v in cls.__instances.values():
#                         inst = v
#                         break
#                     if inst:
#                         cls.__onglobalconnect(inst, ord(unitid), ord(clientid), ord(clienttype), ord(accessunit), ord(status), to_str(ext_info, 'cp936'))
#             else:
#                 cls.__onglobalconnect(ord(unitid), ord(clientid), ord(clienttype), ord(accessunit), ord(status), to_str(ext_info, 'cp936'))
            cls.__onglobalconnect(ord(unitid), ord(clientid), ord(clienttype), ord(accessunit), ord(status), to_str(ext_info, 'cp936'))

    @classmethod
    def __trace_cb(cls, msg):
        cls.__logger.log(cls.__logging_option[1], to_str(msg, 'cp936'))

    @classmethod
    def __traceerr_cb(cls, msg):
        cls.__logger.log(cls.__logging_option[2], to_str(msg, 'cp936'))

    @property
    def localClientId(self):
        '''客户端ID'''
        return self.__localClientId

    @property
    def localClientType(self):
        '''客户端类型'''
        return self.__localClientType

    @property
    def unitid(self):
        '''客户端的单元ID'''
        return self._unitid

    @property
    def addr_expr(self):
        return '{} {} {}'.format(self._unitid, self.__localClientId, self.__localClientType)

    @property
    def masterHost(self):
        '''SmartBus 服务主机名
        '''
        return self.__masterHost

    @property
    def masterPort(self):
        '''SmartBus 服务端口'''
        return self.__masterPort

    @property
    def slaverHost(self):
        '''SmartBus 从服务主机名'''
        return self.__slaverHost

    @property
    def slaverPort(self):
        '''SmartBus 从服务端口'''
        return self.__slaverPort

    @property
    def authorUsr(self):
        '''登录名
        '''
        return self.__authorUsr

    @property
    def authorPwd(self):
        '''密码
        '''
        return self.__authorPwd

    @property
    def extInfo(self):
        '''连接附加信息'''
        return self.__extInfo

    @property
    def encoding(self):
        '''收/发字符串时使用的编码。默认为 utils.default_encoding。
        '''
        return self.__encoding

    def onConnectSuccess(self, unitId):
        '''连接成功事件

        :param int unitId: 单元ID
        '''
        pass

    def onConnectFail(self, unitId, errno):
        '''连接失败事件

       :param int unitId: 单元ID
       :param int errno: 错误码
       '''
        pass

    def onDisconnect(self):
        '''连接中断事件
        '''
        pass

    def onReceiveText(self, packInfo, txt):
        '''收到文本事件

        :param packInfo: 数据包信息
        :type packInfo: smartbus.PackInfo
        :param str txt: 收到的文本
        '''
        pass

    def onInvokeFlowAcknowledge(self, packInfo, project, invokeId, ack, msg):
        '''收到流程执行回执事件

        在调用流程之后，通过该回调函数类型获知流程调用是否成功

        :param packInfo: 数据包信息
        :type packInfo: smartbus.PackInfo
        :param str project: 流程项目ID
        :param int invokeId: 调用ID
        :param int ack: 流程调用是否成功。1表示成功，其它请参靠考误码
        :param str msg: 调用失败时的信息描述
        '''
        pass

    def onInvokeFlowRespond(self, packInfo, project, invokeId, result):
        '''收到流程返回数据事件

        通过类类型的回调函数，获取被调用流程的“子项目结束”节点的返回值列表

        :param packInfo: 数据包信息
        :type packInfo: smartbus.PackInfo
        :param str project: 流程项目ID
        :param int invokeId: 调用ID
        :param int result: 返回的数据。JSON数组格式
        '''
        pass

    def onInvokeFlowTimeout(self, packInfo, project, invokeId):
        '''流程返回超时事件

        :param packInfo: 数据包信息
        :type packInfo: smartbus.PackInfo
        :param str project: 流程项目ID
        :param int invokeId: 调用ID
        '''
        pass

    def onInvokeFlowError(self, packInfo, project, invokeId, errno):
        '''流程调用错误事件

        :param packInfo: 数据包信息
        :type packInfo: smartbus.PackInfo
        :param str project: 流程项目ID
        :param int invokeId: 调用ID
        :param int errno: 错误码
        '''
        pass

    def dispose(self):
        '''释放客户端
        '''
        cls = type(self)
        cls.__instances.pop(self.__localClientId, None)

    def connect(self):
        '''连接到服务器

        :exc: 如果连接失败，则抛出 :exc:`ConnectError` 异常
        '''
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
        errors.check_restval(result)

    def send(self, cmd, cmdType, dstUnitId, dstClientId, dstClientType, data, encoding=None):
        '''发送数据

        :param cmd: 命令
        :param cmdType: 命令类型
        :param dstUnitId: 目标节点ID
        :param dstClientId: 目标客户端ID
        :param dstClientType: 目标客户端类型
        :param data: 待发送数据，可以是文本或者字节数组
        :param encoding: 文本的编码。默认为该对象的 :attr:`encoding` 属性
        '''
        data = to_bytes(data, encoding if encoding else self.encoding)
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
        errors.check_restval(result)

    def invokeFlow(self, server, process, project, flow, parameters=[], isNeedReturn=True, timeout=30):
        '''调用流程

        :param int server: IPSC流程服务所在节点
        :param int process: IPSC进程索引值，同时也是该IPSC进程的 smartbus client-id
        :param str project: 流程项目名称
        :param str flow: 流程名称
        :param parameters: 流程传入参数
        :type parameters: 简单数据或者由简单数据组合成的int, float, str, bool , dict，或者它们的再组合数据类型。
        :param bool isNeedReturn: 是否需要流程返回值
        :param timeout: 等待流程返回超时值，单位为秒。
        :type timeout: int or float
        :return: 当需要等待流程返回值时，该返回值是 :func:`onInvokeFlowRespond` "流程返回事件"中对应的ID.
        :rtype: int
        '''
        c_server_unitid = c_int(server)
        c_processindex = c_int(process)
        c_project_id = c_char_p(to_bytes(project, 'cp936'))
        c_flowid = c_char_p(to_bytes(flow, 'cp936'))
        c_invoke_mode = c_int(0) if isNeedReturn else c_int(1)
        c_timeout = c_int(int(timeout * 1000))
        if parameters is None:
            parameters = []
        else:
            if isinstance(parameters, (int, float, str, bool , dict)):
                parameters = [parameters]
            else:
                parameters = list(parameters)
        c_in_valuelist = c_char_p(to_bytes(str(parameters), 'cp936'))
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
        if result < 0:
            errors.check_restval(result)
        elif result == 0:
            raise errors.InvokeFlowIdError()
        return result

    def ping(self, dstUnitId, dstClientId, dstClientType, data, encoding=None):
        '''发送PING命令
        
        :param int dstUnitId: 目标的smartbus单元ID
        :param int dstClientId: 目标的smartbus客户端ID
        :param int dstClientType: 目标的smartbus客户端类型
        :param str data: 要发送的数据
        :param str encoding: 数据的编码。 默认值为None，表示使用 :attr:`smartbus.netlient.client.Client.encoding`
        '''
        data = to_bytes(data, encoding if encoding else self.encoding)
        data_pc = create_string_buffer(data) if data else None
        data_sz = len(data_pc) if data_pc else 0
        result = sbncif._c_fn_SendPing(
            self.__c_localClientId,
            c_int(dstUnitId),
            c_int(dstClientId),
            c_int(dstClientType),
            byref(data_pc),
            c_int(data_sz)
        )
        errors.check_restval(result)

    def sendNotify(self, server, process, project, title, mode, expires, param):
        '''发送通知消息
        
        :param int server:  目标IPSC服务器smartbus单元ID
        :param int process: IPSC进程ID，同时也是该IPSC进程的 smartbus client-id
        :param str project: 流程项目ID
        :param str title:   通知的标示
        :param int mode:    调用模式
        :param int expires: 消息有效期。单位ms
        :param str param:   消息数据
        :return: > 0 invoke_id，调用ID。< 0 表示错误。
        :rtype: int
        '''
        c_server_unitid = c_int(server)
        c_processindex = c_int(process)
        c_project_id = c_char_p(to_bytes(project, 'cp936'))
        c_title = c_char_p(to_bytes(title, 'cp936'))
        c_mode = c_int(0) if mode else c_int(1)
        c_expires = c_int(int(expires * 1000))
        c_param = c_char_p(to_bytes(param, 'cp936'))
        result = sbncif._c_fn_SendNotify(
            self.__c_localClientId,
            c_server_unitid,
            c_processindex,
            c_project_id,
            c_title,
            c_mode,
            c_expires,
            c_param
        )
        errors.check_restval(result)
