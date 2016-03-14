#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2013-1-29

@author: root
"""
from locale import atoi
from uuid import uuid1

if __name__ == '__main__':
    import sys
    import os
    import threading
    from time import time, sleep
    import smartbus.ipcclient

    cc = 0
    bg_tm = time()
    cc_sent = 0
    cc_recv = 0
    cc_corr = 0
    cc_tmot = 0
    map_data = {}


    #    lib_file_path = None  # '/media/sf_E_DRIVE/My Projects/TK ClientsServiceSystem/smartbus/lib/linux-gcc4.1.2-x86/libbusipccli.so'
    def on_connect_ok(client, unitId):
        print('connected!', unitId)


    def on_connect_err(client, unitId, errno):
        print('connect error:', unitId, errno)
        raise Exception('connect error')


    def on_receive(client, packInfo, txt):
        print('receive:', packInfo, txt)


    def onInvokeFlowRespond(client, packInfo, project, invokeId, result):
        global cc
        global cc_recv
        global cc_corr
        global map_data
        global bg_tm
        cc_recv += 1
        if result[0] == map_data.pop(invokeId, None):
            cc_corr += 1
        if cc_recv == cc:
            print('---------------------------------------------------------------')
            print(cc, 'tasks, duration time(sec):', time() - bg_tm)
            print('sent: %d, received: %d, correct:%d, timeout:%d' % (cc_sent, cc_recv, cc_corr, cc_tmot))
            print('---------------------------------------------------------------')
            print()


    def onInvokeFlowTimeout(client, packInfo, project, invokeId):
        global cc_tmot
        cc_tmot += 1
        print('timeout:', project, invokeId, file=sys.stderr)


    smartbus.ipcclient.Client.initialize(15, 15)
    client = smartbus.ipcclient.Client.instance()
    assert (client)
    print(client)
    client.onConnectSuccess = on_connect_ok
    client.onConnectFail = on_connect_err
    client.onReceiveText = on_receive
    client.onInvokeFlowRespond = onInvokeFlowRespond
    client.onInvokeFlowTimeout = onInvokeFlowTimeout
    rt = client.connect()
    print('connect returns', rt)

    while True:
        s = ''
        if sys.version_info[0] == 2:
            s = raw_input('>')
        elif sys.version_info[0] == 3:
            s = input('>')

        if s.strip().lower() in ('quit', 'exit'):
            break
        else:
            n = 0
            try:
                n = atoi(s)
            except:
                pass

            if n:
                cc_sent = 0
                cc_recv = 0
                cc_corr = 0
                cc_tmot = 0
                project = 'Project1'
                flow = 'Flow1'
                map_data.clear()
                cc = n
                bg_tm = time()
                for i in range(n):
                    txt = '%09d-%s' % (cc_sent, uuid1().hex)
                    rt = client.invokeFlow(0, 0, 'Project1', 'Flow1', txt, timeout=20)
                    if rt < 0:
                        print('send error', file=sys.stderr)
                        break
                    cc_sent += 1
                    map_data[rt] = txt
                    while cc_sent - cc_recv > 1000:
                        sleep(0.001)


            elif s.strip().lower() == 'show':
                print('sent: %d, received: %d, correct:%d, timeout:%d' % (cc_sent, cc_recv, cc_corr, cc_tmot))

    print('finalize...')
    smartbus.ipcclient.Client.finalize()
    print('finalized')
