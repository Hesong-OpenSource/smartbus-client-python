# encoding: utf-8

'''
Created on 2013-3-5

author: tanbro
'''

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
        '''
        收到了文本消息。
        :param packInfo:
        :param txt:
        '''
        print(txt)


    def onInvokeFlowRespond(packInfo, project, invokeId, result):
        print(result)
        print(result[0]['result'])

    print ('init...')
    smartbus.netclient.Client.initialize(15)
    print ('init OK! Connecting...')

    cli = smartbus.netclient.Client(0, -1, '192.168.3.20', 8089, encoding='utf-8')

    cli.onConnectSuccess = onConnectSuccess
    cli.onReceiveText = onReceiveText
    cli.onInvokeFlowRespond = onInvokeFlowRespond
    
    cli.connect()
    

    while True:
        s = readln()
        #  'mbcs'
        #cli.send(cmd=1, cmdType=1, dstUnitId=0, dstClientId=15, dstClientType=15, txt=s)
        s = to_unicode(s)
        data = dict(
            jsonrpc = '2.0',
            method = 'test',
            params = [s]
        )
        cli.invokeFlow(0,0,"Project1", "WebChatRpc", data);
