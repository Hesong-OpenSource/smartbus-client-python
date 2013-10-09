#-*- coding: utf-8 -*-

## \package smartbus.errors
# \date 2013-6-8
# \author lxy@hesong.ent

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
    SMARTBUS_ERR_OTHER:'SMARTBUS_ERR_OTHER',
}

## @name 异常类
## @{

## 已经初始化，无法重复的初始化
class AlreadyInitializedError(Exception):
    pass

## 尚未初始化，无法使用
class NotInitializedError(Exception):
    pass

## 对象已经存在，无法再次新建
class AlreadyExistsError(Exception):
    pass

class InvokeFlowIdError(Exception):
    pass

## @}

class SmartBusError(Exception):
    def __init__(self, code, message):
        Exception.__init__(self, code, message)
        self.code = code
        self.message = message

def check_restval(code, raise_if_err=True):
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
