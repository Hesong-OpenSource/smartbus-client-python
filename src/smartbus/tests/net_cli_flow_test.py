#!/usr/bin/env python
# encoding: utf-8

"""
Created on 2013-3-5

author: tanbro
"""
import sys
import logging

logging.root.addHandler(logging.StreamHandler())
logging.root.setLevel(logging.DEBUG)

if sys.version_info[0] == 2:
    readln = raw_input
elif sys.version_info[0] == 3:
    readln = input

if __name__ == '__main__':
    import smartbus.netclient
    import smartbus.netclient._c_smartbus_netcli_interface


    def onReceiveText(self, packInfo, txt):
        """
        收到了文本消息。
        :param packInfo:
        :param txt:
        """
        print(txt)


    def flow_response(pack_info, project, invoke_id, result):
        print('response:', invoke_id, result)


    def flow_timeout(pack_info, project, invoke_id):
        print('timeout:', invoke_id)


    def connect_succeed(unit_id):
        print('smartbus connect_succeed: %s' % (unit_id))


    def connect_failed(unit_id, errno):
        print('smartbus connect_failed: %s, %s' % (unit_id, errno))


    def disconnected():
        print('disconnected')


    smartbus.netclient.Client.initialize(26)
    print('library file = {}'.format(smartbus.netclient._c_smartbus_netcli_interface._lib))
    cli = smartbus.netclient.Client(localClientId=0, local_client_type=25, master_host='10.4.62.45', master_port=8089,
                                    encoding='utf-8')

    cli.on_connect_success = connect_succeed
    cli.on_connect_fail = connect_failed
    cli.on_disconnect = disconnected
    cli.on_flow_resp = flow_response
    cli.on_flow_timeout = flow_timeout

    cli.connect()

    cli.on_receive_text = onReceiveText

    while True:
        s = readln()
        # cli.sendText(cmd=1, cmdType=1, dstUnitId=0, dstClientId=15, dstClientType=15, txt=s)
        cli.startup_flow(0, 0, 'Project2', '_webchat_rpc', {'method': 'RobotConnected', 'params': ['robot-001']}, True, 5)
