#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Created on 2013年11月22日

@author: tanbro
"""
import unittest
import sys
import threading
import json
import logging

logging.root.addHandler(logging.StreamHandler())
logging.root.level = logging.DEBUG

from smartbus.ipcclient.client import Client

jsonrpc_version = '2.0'

CMDTYPE_JSONRPC_REQ = 211
'''JSONRPC 请求. 用于 smartbus 客户端 send 函数的 cmd_type 参数.'''

CMDTYPE_JSONRPC_RES = 212
'''JSONRPC 回复. 用于 smartbus 客户端 send 函数的 cmd_type 参数.'''


class FlowJsonRpcTest(unittest.TestCase):
    is_inited = False
    is_connected = False
    pending_invokes = {}
    pending_lock = threading.Lock()
    unitid = -1

    def setUp(self):
        cls = type(self)

        if not cls.is_inited:
            Client.initialize(17, 17)
            cls.is_inited = True

        self._client = Client.instance()
        print('library file :', self._client.library)

        if not cls.is_connected:
            cond_connect = threading.Condition()
            cond_connect.acquire()

            def ConnectSuccess(unitId):
                print('ConnectSuccess: unit_id={}'.format(unitId))
                cls.is_connected = True
                cls.unitid = unitId
                cond_connect.acquire()
                cond_connect.notify()
                cond_connect.release()

            pass

            def onConnectFail(unitId, errno):
                print('ConnectFail: unitId={}, errno={}'.format(unitId, errno), file=sys.stderr)
                cls.is_connected = False
                cond_connect.acquire()
                cond_connect.notify()
                cond_connect.release()

            pass

            def onDisconnect():
                print('Disconnect', file=sys.stderr)
                cls.is_connected = False
                cond_connect.acquire()
                cond_connect.notify()
                cond_connect.release()

            pass

            def onInvokeFlowRespond(packInfo, project, invokeId, result):
                print('>>> InvokeFlowRespond: invokeId={2}, result={3}'.format(packInfo, project, invokeId, result))
                with cls.pending_lock:
                    pending = cls.pending_invokes[invokeId]
                pending[1] = result
                cond = pending[0]
                cond.acquire()
                cond.notify()
                cond.release()
                print('<<< InvokeFlowRespond: invokeId={}'.format(invokeId))

            pass

            def onInvokeFlowTimeout(packInfo, project, invokeId):
                print('InvokeFlowTimeout: invokeId={2}'.format(packInfo, project, invokeId), file=sys.stderr)
                with cls.pending_lock:
                    pending = cls.pending_invokes[invokeId]
                pending[1] = TimeoutError()
                cond = pending[0]
                cond.acquire()
                cond.notify()
                cond.release()

            pass

            def onReceiveText(packInfo, txt):
                print('ReceiveText: txt={1}'.format(packInfo, txt))
                reqobj = json.loads(txt)
                id_ = reqobj['id']
                method = reqobj['method']
                params = reqobj['params']
                if method == 'Echo':
                    if isinstance(params, list):
                        msg = params[0]
                    elif isinstance(params, dict):
                        msg = params['msg']
                    msg = 'ReEcho: ' + msg
                    txt = json.dumps({'jsonrpc': jsonrpc_version, 'id': id_, 'result': msg})
                self._client.send(0, CMDTYPE_JSONRPC_RES, packInfo.src_unit_id, packInfo.srcUnitClientId,
                                  packInfo.srcUnitClientType, txt)

            pass

            self._client.on_connect_success = ConnectSuccess
            self._client.on_connect_fail = onConnectFail
            self._client.on_disconnect = onDisconnect
            self._client.on_flow_resp = onInvokeFlowRespond
            self._client.on_flow_timeout = onInvokeFlowTimeout
            self._client.on_receive_text = onReceiveText

            self._client.connect()
            cond_connect.wait()
            self.assertTrue(cls.is_connected, 'connect failed.')

    def tearDown(self):
        pass

    #     def test_flow_echo(self):
    #         cls = type(self)
    #         msg = 'Hello! 你好！'
    #         cond = threading.Condition()
    #         cond.acquire()
    #         invoke_id = self._client.startup_flow(
    #             server=cls.unit_id,
    #             process=0,
    #             project='Project1',
    #             flow='_agent_rpc',
    #             parameters={
    #                 'method' : 'test.Echo',
    #                 'params' : {
    #                     'msg' : msg
    #                 }
    #             },
    #             isNeedReturn=True,
    #         )
    #         with cls.pending_lock:
    #             pending = cls.pending_invokes[invoke_id] = [cond, None]
    #         cond.wait()
    #         with cls.pending_lock:
    #             cls.pending_invokes.pop(invoke_id)
    #         result = pending[1]
    #         if isinstance(result, Exception):
    #             raise result
    #         self.assertIsInstance(result, list)
    #         self.assertEqual(result[0], True)
    #         self.assertEqual(result[1], msg)
    #
    #     def test_flow_reecho(self):
    #         cls = type(self)
    #         msg = 'Hello! 你好！'
    #         cond = threading.Condition()
    #         cond.acquire()
    #         invoke_id = self._client.startup_flow(
    #             server=cls.unit_id,
    #             process=0,
    #             project='Project1',
    #             flow='_agent_rpc',
    #             parameters={
    #                 'method' : 'test.ReEcho',
    #                 'params' : {
    #                     'msg' : msg
    #                 }
    #             },
    #             isNeedReturn=True,
    #         )
    #         with cls.pending_lock:
    #             pending = cls.pending_invokes[invoke_id] = [cond, None]
    #         cond.wait()
    #         with cls.pending_lock:
    #             cls.pending_invokes.pop(invoke_id)
    #         result = pending[1]
    #         if isinstance(result, Exception):
    #             raise result
    #         self.assertIsInstance(result, list)
    #         self.assertEqual(result[0], True)
    #         self.assertEqual(result[1], 'ReEcho: ' + msg)


    def test_flow_echo_multithread(self):
        """
        该测试需要：
        在本 IPC Smartbus 的 IPSC 中，需要
        """
        cls = type(self)
        threads = []

        def _do(n):
            print('test.Echo [{}] start'.format(n))
            msg = 'Hello! 你好！ {}'.format(n)
            cond = threading.Condition()
            cond.acquire()

            print('>>> test.Echo [{}] startup_flow'.format(n))
            invoke_id = self._client.startup_flow(
                server=cls.unitid,
                process=0,
                project='Project1',
                flow='_agent_rpc',
                parameters={
                    'method': 'test.Echo',
                    'params': {
                        'msg': msg
                    }
                },
                is_resp=True,
            )
            print('<<< test.Echo [{}] startup_flow returns {}'.format(n, invoke_id))

            with cls.pending_lock:
                pending = cls.pending_invokes[invoke_id] = [cond, None]

            print('test.Echo [{}] -> {} waiting...'.format(n, invoke_id))
            cond.wait()
            with cls.pending_lock:
                cls.pending_invokes.pop(invoke_id)
            result = pending[1]
            if isinstance(result, Exception):
                raise result
            self.assertIsInstance(result, list)
            self.assertEqual(result[0], True)
            self.assertEqual(result[1], msg)
            print('test.Echo [{}] -> {} OK.'.format(n, invoke_id))

        pass

        for i in range(100):
            trd = threading.Thread(target=_do, args=(i,))
            trd.daemon = True
            threads.append(trd)
            trd.start()

        for i in range(len(threads)):
            trd = threads[i]
            print('join Echo test thread {} ...'.format(i))
            trd.join()
            print('Echo test thread {} joined'.format(i))


# def test_flow_multi_reecho(self):
#         cls = type(self)
#         threads = []
#         
#         def _do(n):
#             msg = 'Hello! 你好！ {}'.format(n)
#             cond = threading.Condition()
#             cond.acquire()
#             invoke_id = self._client.startup_flow(
#                 server=cls.unit_id,
#                 process=0,
#                 project='Project1',
#                 flow='_agent_rpc',
#                 parameters={
#                     'method' : 'test.ReEcho',
#                     'params' : {
#                         'msg' : msg
#                     }
#                 },
#                 isNeedReturn=True,
#             )
#             with cls.pending_lock:
#                 pending = cls.pending_invokes[invoke_id] = [cond, None]
#             cond.wait()
#             with cls.pending_lock:
#                 cls.pending_invokes.pop(invoke_id)
#             result = pending[1]
#             if isinstance(result, Exception):
#                 raise result
#             self.assertIsInstance(result, list)
#             self.assertEqual(result[0], True)
#             self.assertEqual(result[1], 'ReEcho: ' + msg)
#             print('test.ReEcho[{}] OK.'.format(i))
#         pass
#     
#         for i in range(100):
#             trd = threading.Thread(target=_do, args=(i,))
#             trd.daemon = True
#             threads.append(trd)
#             trd.start()
#             
#         for i in range(len(threads)):
#             trd = threads[i]
#             print('join ReEcho test thread {} ...'.format(i))
#             trd.join()
#             print('ReEcho test thread {} joined'.format(i))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
