'''
Created on 2013-1-28

@author: root
'''
import unittest

    
    
def on_connection(param, ack):
    pass

def on_disconnect(param):
    pass

def on_recvdata(param, head, data, size):
    pass

class Test(unittest.TestCase):


    def setUp(self):
        pass


    def tearDown(self):
        pass

    def testLoad(self):
        import smartbus.client
        
        lib_file_path = '/media/sf_E_DRIVE/My Projects/TK ClientsServiceSystem/smartbus/lib/linux-gcc4.1.2-x86/libbusipccli.so'
        
        smartbus.client.Client.initialize(1, 11, lib_file_path)
        client = smartbus.client.Client()
        assert(client)
        client.connect('username', 'password', 'info')
        smartbus.client.Client.finalize()



if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testLoad']
    unittest.main()
