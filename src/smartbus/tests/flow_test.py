# encoding: utf-8

"""
Created on 2013-3-5

author: tanbro
"""

from __future__ import print_function, absolute_import, with_statement

import sys

if sys.version_info[0] == 2:
    readln = raw_input
elif sys.version_info[0] == 3:
    readln = input

import smartbus.netclient
from smartbus.utils import to_bytes, to_unicode, to_str

if __name__ == '__main__':

    def onConnectSuccess(unitId):
        print('connected! {}'.format(unitId))


    def onReceiveText(packInfo, txt):
        """
        收到了文本消息。
        :param packInfo:
        :param txt:
        """
        print(txt)


    def onInvokeFlowRespond(packInfo, project, invokeId, result):
        print('FlowRespond:', packInfo, project, invokeId, result)


    def onInvokeFlowAcknowledge(packInfo, project, invokeId, ack, msg):
        print('FlowAcknowledge:\n packInfo={}\n project={}\n invokeId={}\n ack={}\n msg={}'.format(packInfo, project,
                                                                                                   invokeId, ack, msg))


    print('init...')
    smartbus.netclient.Client.initialize(17)
    print('init OK! Connecting...')

    cli = smartbus.netclient.Client(0, 13, '10.4.62.45', 8089, encoding='utf-8')

    cli.on_connect_success = onConnectSuccess
    cli.on_receive_text = onReceiveText
    cli.on_flow_resp = onInvokeFlowRespond
    cli.on_flow_ack = onInvokeFlowAcknowledge

    cli.connect()

    while True:
        s = readln()
        #  'mbcs'
        # cli.send(cmd=1, cmd_type=1, dst_unit_id=0, dstClientId=15, dstClientType=15, txt=s)
        s = to_unicode(s)
        data = dict(
            jsonrpc='2.0',
            method='test.Echo',
            params=[s]
        )
        cli.startup_flow(0, 0, "Project1", "_agent_rpc", data);
