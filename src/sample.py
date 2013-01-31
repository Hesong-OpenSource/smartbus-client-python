'''
Created on 2013-1-29

@author: root
'''

if __name__ == '__main__':
    import sys
    import os
    import smartbus.client
    
    os.environ
        
#    lib_file_path = None  # '/media/sf_E_DRIVE/My Projects/TK ClientsServiceSystem/smartbus/lib/linux-gcc4.1.2-x86/libbusipccli.so'
    def on_connect_ok():
        print('connected!')
        
    def on_connect_err(errno):
        print('connect error:', errno)
        
    def on_receive(self, txt):
        print('receive:', txt)
    
    def onInvokeFlowRespond(project, invokeId, result):
        print ('onInvokeFlowRespond', project, invokeId, result)
    
    smartbus.client.Client.initialize(20, 20)
    client = smartbus.client.Client()
    assert(client)
    print(client)
    client.onConnectSuccess = on_connect_ok
    client.onConnectFail = on_connect_err
    client.onReceiveText = on_receive
    client.onInvokeFlowRespond = onInvokeFlowRespond
    client.connect()
    
    while True:
        s = ''
        if sys.version_info[0] == 2:
            s = raw_input('>')
        elif sys.version_info[0] == 3:
            s = input('>')
            
        if s.strip().lower() in ('quit', 'exit'):
            break
        else:            
#            client.sendText(1, 2, 1, 1, 1, s)
            project = 'Project1'
            flow = 'Flow1'
            print('invoking <{%s}.{%s}> ...' % (project, flow))
            rt = client.invokeFlow(0, 0, 'Project1', 'Flow1', s, True, 100000)
            print('returns %d' % (rt))

    print('finalize...')
    smartbus.client.Client.finalize()
    print('finalized')
    
