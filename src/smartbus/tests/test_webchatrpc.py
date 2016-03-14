"""
Created on 2013年12月2日

@author: tanbro
"""
import unittest
import logging
import threading

from smartbus.netclient import Client
from smartbus.netclient import _c_smartbus_netcli_interface as clib

logging.root.addHandler(logging.StreamHandler())
logging.root.level = logging.DEBUG

jsonrpc_version = '2.0'

CMDTYPE_JSONRPC_REQ = 211
'''JSONRPC 请求. 用于 smartbus 客户端 send 函数的 cmd_type 参数.'''

CMDTYPE_JSONRPC_RES = 212
'''JSONRPC 回复. 用于 smartbus 客户端 send 函数的 cmd_type 参数.'''


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cond_connect = threading.Condition()

        cls._recv_buf = {}
        cls._recv_buf_lock = threading.Lock()

        def onReceiveText(self, packInfo, txt):
            print(txt)

        pass

        def flow_response(packInfo, project, invokeId, result):
            print('response:', invokeId, result)
            with cls._recv_buf_lock:
                pending = cls._recv_buf[invokeId]
            cond = pending[0]
            cond.acquire()
            pending[1] = result
            cond.notify()
            cond.release()

        pass

        def flow_timeout(packInfo, project, invokeId):
            print('timeout:', invokeId)

        pass

        def connect_succeed(unit_id):
            print('smartbus connect_succeed: %s' % (unit_id))
            cls._connected = True
            cond_connect.acquire()
            cond_connect.notify()
            cond_connect.release()

        pass

        def connect_failed(unit_id, errno):
            print('smartbus connect_failed: %s, %s' % (unit_id, errno))
            cls._connected = False
            cond_connect.acquire()
            cond_connect.notify()
            cond_connect.release()

        pass

        def disconnected():
            print('disconnected')
            cls._connected = False

        pass

        Client.initialize(26)
        print('library file = {}'.format(clib._lib))
        _cli = cls._cli = Client(localClientId=0, localClientType=25, masterHost='10.4.62.45', masterPort=8089,
                                 encoding='utf-8')

        _cli.onConnectSuccess = connect_succeed
        _cli.onConnectFail = connect_failed
        _cli.onDisconnect = disconnected
        _cli.onInvokeFlowRespond = flow_response
        _cli.onInvokeFlowTimeout = flow_timeout
        _cli.onReceiveText = onReceiveText

        print('conneting...')
        cond_connect.acquire()
        _cli.connect()
        cond_connect.wait()
        assert cls._connected

    def test_robot_connected(self):
        cond = threading.Condition()
        cond.acquire()
        with self._recv_buf_lock:
            flowid = self._cli.invokeFlow(0, 0, 'Project2', '_webchat_rpc',
                                          {'method': 'RobotConnected', 'params': ['robot-001']}, True, 5)
            pending = [cond, None]
            self._recv_buf[flowid] = pending
        cond.wait()
        retval = pending[1]
        print(retval)
        retval = retval[0]
        self.assertIn('result', retval)


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.test_robot_connected']
    unittest.main()
