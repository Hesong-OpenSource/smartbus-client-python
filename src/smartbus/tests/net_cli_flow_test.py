#!/usr/bin/env python
# encoding: utf-8

'''
Created on 2013-3-5

author: tanbro
'''
import sys

if sys.version_info[0] == 2:
    readln = raw_input
elif sys.version_info[0] == 3:
    readln = input
    
if __name__ == '__main__':
    import smartbus.netclient
    
    def onReceiveText(self, packInfo, txt):
        '''
        收到了文本消息。
        :param packInfo:
        :param txt:
        '''
        print(txt)

    def flow_response(pack_info, project, invoke_id, result):
        print(invoke_id, result)

    def flow_timeout(pack_info, project, invoke_id):
        print(invoke_id, timeout)

    def connect_succeed(unit_id):
        print('smartbus connect_succeed: %s'%(unit_id))

    def connect_failed(unit_id, errno):
        print('smartbus connect_failed: %s, %s'%(unit_id, errno))

    def disconnected():
        print('disconnected')
    
    #smartbus.netclient.Client.initialize(26, '''/media/08CAB087CAB07314/My Projects/TK ClientsServiceSystem/smartbus/lib/linux-gcc4.1.2-x86/libbusnetcli.so''')
    smartbus.netclient.Client.initialize(14, '''E:\My Projects\TK ClientsServiceSystem\smartbus\lib\windows-msc1600-x86\smartbus_net_cli.dll''')
    cli = smartbus.netclient.Client(localClientId=0, localClientType=-1, masterHost='192.168.3.20', masterPort=8089, encoding='utf-8')

    cli.onConnectSuccess = connect_succeed
    cli.onConnectFail = connect_failed
    cli.onDisconnect = disconnected
    cli.onInvokeFlowRespond = flow_response
    cli.onInvokeFlowTimeout = flow_timeout

    cli.connect()
    
    cli.onReceiveText = onReceiveText

    while True:
        s = readln()
        #cli.sendText(cmd=1, cmdType=1, dstUnitId=0, dstClientId=15, dstClientType=15, txt=s)
        cli.invokeFlow(0, 0, 'Project1', 'WebChatRpc', {'method':'test', 'params':[]}, True, 5)
