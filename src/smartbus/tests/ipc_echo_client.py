#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2013-1-29

@author: root
"""

if __name__ == '__main__':
    import sys
    import smartbus.ipcclient


    #    lib_file_path = None  # '/media/sf_E_DRIVE/My Projects/TK ClientsServiceSystem/smartbus/lib/linux-gcc4.1.2-x86/libbusipccli.so'
    def on_connect_ok(unitId):
        print('connected!', unitId)


    def on_connect_err(unitId, errno):
        print('connect error:', unitId, errno)
        raise Exception('connect error')


    def on_receive(packInfo, txt):
        print('receive:', txt)


    def onInvokeFlowRespond(packInfo, project, invokeId, result):
        print('receive:', result)


    def onInvokeFlowTimeout(packInfo, project, invokeId):
        print('timeout:')


    def onglobalconnect(unitid, clientid, clienttype, status, ext_info):
        print('onglobalconnect:', unitid, clientid, clienttype, status, ext_info)


    smartbus.ipcclient.Client.initialize(15, 15, onglobalconnect)
    client = smartbus.ipcclient.Client.instance()
    assert (client)

    client.on_connect_success = on_connect_ok
    client.on_connect_fail = on_connect_err
    client.on_receive_text = on_receive
    client.on_flow_resp = onInvokeFlowRespond
    client.on_flow_timeout = onInvokeFlowTimeout
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
            rt = client.startup_flow(0, 0, 'Project1', 'Flow1', s, timeout=20)

    print('finalize...')
    smartbus.ipcclient.Client.finalize()
    print('finalized')
