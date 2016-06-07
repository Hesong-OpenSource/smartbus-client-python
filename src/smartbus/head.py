# -*- coding: utf-8 -*-

from __future__ import absolute_import

__all__ = ['Head']


class Head:
    """Smartbus通信包头信息

    每当接收到数据时，所触发的事件中，都包含该类型的参数，记录了一些数据包的相关信息

    对应 `SMARTBUS_PACKET_HEAD` 结构体的 :mod:`ctypes` 数据类型 :class:`PacketHeader` 的再次封装
    """

    def __init__(self, ptr):
        """
        :param smartbus._c.mutual.PPacketHeader ptr: 结构体指针
        """
        self._prt = ptr
        self._cmd = 0
        self._cmd_type = 0
        self._src_unit_client_type = 0
        self._src_unit_id = 0
        self._src_unit_clientId = 0
        self._dst_unit_client_type = 0
        self._dst_unit_id = 0
        self._dst_unit_client_id = 0
        self._packet_size = 0
        self._data_length = 0
        self._cmd = ptr.contents.cmd
        self._cmd_type = ptr.contents.cmdtype
        self._src_unit_client_type = ord(ptr.contents.src_unit_client_type)
        self._src_unit_id = ord(ptr.contents.src_unit_id)
        self._src_unit_clientId = ord(ptr.contents.src_unit_client_id)
        self._dst_unit_client_type = ord(ptr.contents.dest_unit_client_type)
        self._dst_unit_id = ord(ptr.contents.dest_unit_id)
        self._dst_unit_client_id = ord(ptr.contents.dest_unit_client_id)
        self._packet_size = ptr.contents.packet_size
        self._data_length = ptr.contents.datalen

    def __repr__(self):
        s = '<%s.%s object at %s. ' + \
            'cmd=%s, ' + \
            'cmd_type=%s, ' + \
            'src_unit_client_type=%s,' + \
            'src_unit_id=%s, ' + \
            'src_unit_client_id=%s, ' + \
            'dst_unit_client_type=%s, ' + \
            'dst_unit_id=%s, ' + \
            'dst_unit_client_id=%s, ' + \
            'packet_size=%s, ' + \
            'data_length=%s>'
        return s % (
            self.__class__.__module__,
            self.__class__.__name__,
            hex(id(self)),
            self._cmd,
            self._cmd_type,
            self._src_unit_client_type,
            self._src_unit_id,
            self._src_unit_clientId,
            self._dst_unit_client_type,
            self._dst_unit_id,
            self._dst_unit_client_id,
            self._packet_size,
            self._data_length
        )

    @property
    def cmd(self):
        """ 命令

        一条 SmartBus 数据的命令关键字
        """
        return self._cmd

    @property
    def cmd_type(self):
        """ 命令类型

        一条 SmartBus 数据的命令类型
        """
        return self._cmd_type

    @property
    def src_unit_client_type(self):
        """发送者客户端类型
        """
        return self._src_unit_client_type

    @property
    def src_unit_id(self):
        """ 发送者节点ID
        """
        return self._src_unit_id

    @property
    def src_unit_client_id(self):
        """ 发送者客户端ID
        """
        return self._src_unit_clientId

    @property
    def dst_unit_client_type(self):
        """ 接收者客户端类型
        """
        return self._dst_unit_client_type

    @property
    def dst_unit_id(self):
        """ 接收者节点ID
        """
        return self._dst_unit_id

    @property
    def dst_unit_client_id(self):
        """ 接收者客户端ID
        """
        return self._dst_unit_client_id

    @property
    def packet_size(self):
        """ 包长度
        """
        return self._packet_size

    @property
    def data_length(self):
        """ 正文数据长度
        """
        return self._data_length
