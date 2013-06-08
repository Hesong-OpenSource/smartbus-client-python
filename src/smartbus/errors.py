#-*- coding: utf-8 -*-

## \package smartbus.errors
# \date 2013-6-8
# \author lxy@hesong.ent



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

## 连接服务器错误
class ConnectError(Exception):
    pass

## 发送数据错误
class SendError(Exception):
    pass

## @}