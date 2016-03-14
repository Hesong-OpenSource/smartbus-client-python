#!/usr/bin/env python
# encoding: utf-8

"""
Created on 2013-3-5

author: tanbro
"""

import logging

logging.root.setLevel(logging.DEBUG)

if __name__ == '__main__':
    import smartbus.netclient

    unit_id = None


    def onConnectSuccess(unitId):
        print('onConnectSuccess', unitId)
        global unit_id
        unit_id = unitId


    def onReceiveText(self, packInfo, txt):
        print('onReceiveText', packInfo, txt)


    def onConnectFail(unitId, errno):
        print('onConnectFail', unitId, errno)


    smartbus.netclient.Client.initialize(17)
    cli = smartbus.netclient.Client(localClientId=0, localClientType=20, masterHost='10.4.62.45', masterPort=8089,
                                    encoding='utf-8')
    cli.onConnectSuccess = onConnectSuccess
    cli.onReceiveText = onReceiveText
    cli.onConnectFail = onConnectFail

    print('connecting...')
    cli.connect()

    while True:
        s = input('>')
        cli.sendText(cmd=1, cmdType=1, dstUnitId=unit_id, dstClientId=10, dstClientType=15, txt=s)
