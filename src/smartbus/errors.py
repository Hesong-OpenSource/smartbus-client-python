# -*- coding: utf-8 -*-

'''错误信息定义
:date: 2013-6-8
:author: lxy@hesong.ent

'''

from ._c_smartbus import SMARTBUS_ERR_OK, SMARTBUS_ERR_ARGUMENT, SMARTBUS_ERR_CONN_NOT_ESTAB, SMARTBUS_ERR_CONNECT_BREAK, SMARTBUS_ERR_AUTHOR, \
SMARTBUS_ERR_USER, SMARTBUS_ERR_PWD, SMARTBUS_ERR_BUFF_FULL, SMARTBUS_ERR_NODE_NOTEXIST, SMARTBUS_ERR_CLI_NOTEXIST, SMARTBUS_ERR_CONNECTED, \
SMARTBUS_ERR_SEND_OWN, SMARTBUS_ERR_UNITID_INVALID, SMARTBUS_ERR_CLIENTID_INVALID, SMARTBUS_ERR_NON_INIT, SMARTBUS_ERR_MAX_DATASIZE, \
SMARTBUS_ERR_CMDTYPE_INVALID, SMARTBUS_ERR_CLIENTTYPE_INVALID, SMARTBUS_ERR_OTHER


error_code_message = {
    SMARTBUS_ERR_ARGUMENT:'SMARTBUS_ERR_ARGUMENT',
    SMARTBUS_ERR_CONN_NOT_ESTAB:'SMARTBUS_ERR_CONN_NOT_ESTAB',
    SMARTBUS_ERR_CONNECT_BREAK:'SMARTBUS_ERR_CONNECT_BREAK',
    SMARTBUS_ERR_AUTHOR:'SMARTBUS_ERR_AUTHOR',
    SMARTBUS_ERR_USER:'SMARTBUS_ERR_USER',
    SMARTBUS_ERR_PWD:'SMARTBUS_ERR_PWD',
    SMARTBUS_ERR_BUFF_FULL:'SMARTBUS_ERR_BUFF_FULL',
    SMARTBUS_ERR_NODE_NOTEXIST:'SMARTBUS_ERR_NODE_NOTEXIST',
    SMARTBUS_ERR_CLI_NOTEXIST:'SMARTBUS_ERR_CLI_NOTEXIST',
    SMARTBUS_ERR_CONNECTED:'SMARTBUS_ERR_CONNECTED',
    SMARTBUS_ERR_SEND_OWN:'SMARTBUS_ERR_SEND_OWN',
    SMARTBUS_ERR_UNITID_INVALID:'SMARTBUS_ERR_UNITID_INVALID',
    SMARTBUS_ERR_CLIENTID_INVALID:'SMARTBUS_ERR_CLIENTID_INVALID',
    SMARTBUS_ERR_NON_INIT:'SMARTBUS_ERR_NON_INIT',
    SMARTBUS_ERR_MAX_DATASIZE:'SMARTBUS_ERR_MAX_DATASIZE',
    SMARTBUS_ERR_CMDTYPE_INVALID:'SMARTBUS_ERR_CMDTYPE_INVALID',
    SMARTBUS_ERR_CLIENTTYPE_INVALID:'SMARTBUS_ERR_CLIENTTYPE_INVALID',
    #// 发送数据错误
    SMARTBUS_ERR_SEND_DATA:'SMARTBUS_ERR_SEND_DATA',
    #// 分配内存错误
    SMARTBUS_ERR_MEM_ALLOC:'SMARTBUS_ERR_MEM_ALLOC',
    #// 建立连接失败
    SMARTBUS_ERR_ESTABLI_CONNECT:'SMARTBUS_ERR_ESTABLI_CONNECT',
    #// 客户端太多
    SMARTBUS_ERR_CLI_TOOMANY:'SMARTBUS_ERR_CLI_TOOMANY',
    #// 客户端已存在
    SMARTBUS_ERR_CLI_EXIST:'SMARTBUS_ERR_CLI_EXIST',
    #// 目标不存在
    SMARTBUS_ERR_DEST_NONEXIST:'SMARTBUS_ERR_DEST_NONEXIST',
    #// 重复注册
    SMARTBUS_ERR_REGISTERED_REPEAT:'SMARTBUS_ERR_REGISTERED_REPEAT',
    #// 超时
    SMARTBUS_ERR_TIMEOUT:'SMARTBUS_ERR_TIMEOUT',
    #
    SMARTBUS_ERR_OTHER:'SMARTBUS_ERR_OTHER',
}

class AlreadyInitializedError(Exception):
    '''已经初始化，无法重复的初始化
    '''
    pass

class NotInitializedError(Exception):
    '''尚未初始化，无法使用
    '''
    pass

class AlreadyExistsError(Exception):
    '''对象已经存在，无法再次新建
    '''
    pass

class InvokeFlowIdError(Exception):
    '''收到调用流程的返回结果时，ID无法匹配
    '''
    pass

class SmartBusError(Exception):
    '''SmartBus 通信错误
    '''
    def __init__(self, code, message):
        Exception.__init__(self, code, message)
        self._code = code
        self._message = message
        
    @property
    def code(self):
        '''SmartBus错误码
        '''
        return self._code
    
    @property
    def message(self):
        '''错误信息
        '''
        return self._message

def check_restval(code, raise_if_err=True):
    '''检查 SmartBus 客户端 C-API 的返回结果是否正确
    
    :param code: 要检查的返回结果编码
    :type code: int
    :param raise_if_err: 是否在发现错误时抛出异常。默认为真。
    :type raise_if_err: bool
    :return: 
        当 `raise_if_err` 为 True 时，无错误则返回 None，有错误则抛出错误异常；
        当 `raise_if_err` 为 False 时，无错误则返回 None，有错误则返回错误异常实例。
    '''
    if code != SMARTBUS_ERR_OK:
        try:
            msg = error_code_message[code]
        except KeyError:
            msg = 'UNDEFINED_ERROR'
        smartbus_err = SmartBusError(code, msg)
        if raise_if_err:
            raise smartbus_err
        else:
            return smartbus_err
