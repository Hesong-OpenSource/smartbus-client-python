#!/usr/bin/env python
# encoding: utf-8

'''
Created on 2013-3-5

author: tanbro
'''

if __name__ == '__main__':
    import smartbus.netclient
    
    def onReceiveText(self, packInfo, txt):
        '''
        收到了文本消息。
        :param packInfo:
        :param txt:
        '''
        print(txt)
    
    smartbus.netclient.Client.initialize(13, '''/media/08CAB087CAB07314/My Projects/TK ClientsServiceSystem/smartbus/lib/linux-gcc4.1.2-x86/libbusnetcli.so''')
    cli = smartbus.netclient.Client(localClientId=0, localClientType=9, masterHost='192.168.3.20', masterPort=8089, encoding='utf-8')
    cli.connect()
    
    cli.onReceiveText = onReceiveText

    while True:
        s = input()
        cli.sendText(cmd=1, cmdType=1, dstUnitId=0, dstClientId=15, dstClientType=15, txt=s)
