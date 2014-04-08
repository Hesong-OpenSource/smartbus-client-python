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

    def onConnectSuccess(unitId):
        print('connected! {}'.format(unitId))
    
    def onReceiveText(packInfo, txt):
        '''
        收到了文本消息。
        :param packInfo:
        :param txt:
        '''
        print(txt)

    print ('init...')
    smartbus.netclient.Client.initialize(29)
    print ('init OK! Connecting...')

    cli = smartbus.netclient.Client(0, 15, '10.4.62.46', 8089)

    cli.onConnectSuccess = onConnectSuccess
    cli.onReceiveText = onReceiveText
    
    cli.connect()
    

    while True:
        s = readln()
        cli.send(cmd=1, cmdType=1, dstUnitId=28, dstClientId=20, dstClientType=-1, data=s)
