'''
Created on 2013-1-28

@author: root
'''
import unittest

import smartbus.client



class Test(unittest.TestCase):
    
    def on_connect_ok(self):
        pass
        
    def on_connect_err(self, errno):
        raise AssertionError('on_connect_err')
    
    def on_flow_respond(self, packInfo, project, invokeId, result):
        pass
        
    def on_flow_timeout(self, packInfo, project, invokeId):
        raise AssertionError('on_flow_timeout')

    def setUp(self):
        self.invoke_counter = 0
        self.flow_server = 0
        self.flow_process = 0
        self.flow_project = 'Project1'
        self.flow_flow = 'FLow1'
        smartbus.client.Client.initialize(20, 20)
        client = smartbus.client.Client.instance()
        client.onConnectSuccess = self.on_connect_ok
        client.onConnectFail = self.on_connect_err
        client.onInvokeFlowRespond = self.on_flow_respond
        client.onInvokeFlowTimeout = self.on_flow_timeout
        client.connect()

    def tearDown(self):
        smartbus.client.Client.finalize()

    def testInvokeFlow(self):
        smartbus.client.Client.instance().invokeFlow(self.flow_server, self.flow_process, self.flow_project, self.flow_flow)    
        



if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testInvokeFlow']
    unittest.main()
