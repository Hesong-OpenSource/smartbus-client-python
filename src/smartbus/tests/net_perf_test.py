#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2013-1-29

@author: root
"""

print('importing...')

from locale import atoi
from uuid import uuid1

try:
    readln = raw_input
except NameError:
    readln = input

if __name__ == '__main__':
    print('start main...')

    import sys
    import os
    import threading
    from time import time, sleep
    import smartbus.netclient

    cc = 0
    bg_tm = time()
    cc_sent = 0
    cc_recv = 0
    cc_corr = 0
    cc_tmot = 0
    map_data = {}

    print('def....')


    def on_connect_ok(unitId):
        print('connected!', unitId)


    def on_connect_err(unitId, errno):
        print('connect error:', unitId, errno)
        raise Exception()


    def on_disconnect():
        print('disconnect')


    def on_receive(packInfo, txt):
        global bg_tm
        global cc
        global cc_recv
        global cc_corr
        global map_data
        global bg_tm
        #        print(time() - bg_tm, txt)
        cc_recv += 1
        try:
            map_data.pop(txt)
            cc_corr += 1
        except KeyError:
            pass
        if cc_recv == cc:
            print('---------------------------------------------------------------')
            print(cc, 'tasks, duration time(sec):', time() - bg_tm)
            print('sent: %d, received: %d, correct:%d, timeout:%d' % (cc_sent, cc_recv, cc_corr, cc_tmot))
            print('---------------------------------------------------------------')
            print()


    def onInvokeFlowRespond(packInfo, project, invokeId, result):
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


    if sys.version_info[0] < 3:
        def on_global_connect(client, unitid, clientid, clienttype, status, ext_info):
            print(unitid, clientid, clienttype, status, ext_info)
    else:
        def on_global_connect(unitid, clientid, clienttype, status, ext_info):
            print(unitid, clientid, clienttype, status, ext_info)

    lib_file = '''E:\My Projects\TK ClientsServiceSystem\smartbus\lib\windows-msc1600-x86\smartbus_net_cli.dll'''
    print('init....')
    smartbus.netclient.Client.initialize(23, on_global_connect, library_file=lib_file)
    print('create....')
    client = smartbus.netclient.Client(1, 20, '192.168.1.203', 8089, ext_info='这个是netclient节点')
    print('connect...')
    assert (client)
    print(client)
    client.on_connect_success = on_connect_ok
    client.on_connect_fail = on_connect_err
    client.on_disconnect = on_disconnect
    client.on_receive_text = on_receive
    #    client.on_flow_resp = on_flow_resp
    #    client.on_flow_timeout = on_flow_timeout
    print('connecting')
    client.connect()

    while True:
        s = readln('>')
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
                map_data.clear()
                cc = n
                bg_tm = time()
                for i in range(n):
                    #                    txt = '%09d-%s' % (cc_sent, uuid1().hex)
                    client.sendText(9, 9, 14, 14, 14, str(i))
                    cc_sent += 1
                    map_data[i] = i
                    while cc_sent - cc_recv > 1000:
                        sleep(0.001)


            elif s.strip().lower() == 'show':
                print('sent: %d, received: %d, correct:%d, timeout:%d' % (cc_sent, cc_recv, cc_corr, cc_tmot))

    print('dispose...')
    client.dispose()
    print('disposed')
    print('finalize...')
    smartbus.netclient.Client.finalize()
    print('finalized')
