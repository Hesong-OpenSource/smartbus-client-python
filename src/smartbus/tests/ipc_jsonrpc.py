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
import uuid
import multiprocessing

logging.root.level = logging.DEBUG

from smartbus.ipcclient.client import Client

jsonrpc_version = '2.0'

CMDTYPE_JSONRPC_REQ = 211
'''JSONRPC 请求. 用于 smartbus 客户端 send 函数的 cmd_type 参数.'''

CMDTYPE_JSONRPC_RES = 212
'''JSONRPC 回复. 用于 smartbus 客户端 send 函数的 cmd_type 参数.'''

CLIENT_CLIENT_ID = 18
SERVER_CLIENT_ID = 19


def run_echo_server(started_cond, term_cond):
    term_cond.acquire()

    Client.initialize(SERVER_CLIENT_ID, 17)

    cond_connect = threading.Condition()
    cond_connect.acquire()

    def ConnectSuccess(unitId):
        logging.getLogger('ServerProcess').info('ConnectSuccess: unit_id={}'.format(unitId))
        cond_connect.acquire()
        cond_connect.notify()
        cond_connect.release()

    pass

    def onConnectFail(unitId, errno):
        logging.getLogger('ServerProcess').error('ConnectFail: unitId={}, errno={}'.format(unitId, errno))
        cond_connect.acquire()
        cond_connect.notify()
        cond_connect.release()

    pass

    def onDisconnect():
        logging.getLogger('ServerProcess').warn('Disconnect')
        cond_connect.acquire()
        cond_connect.notify()
        cond_connect.release()

    pass

    def onReceiveText(packInfo, txt):
        #         print('Server Process: ReceiveText: txt={1}'.format(packInfo, txt))
        reqobj = json.loads(txt)
        id_ = reqobj['id']
        try:
            method = reqobj['method']
            params = reqobj['params']
            if method == 'Echo':
                if isinstance(params, list):
                    msg = params[0]
                elif isinstance(params, dict):
                    msg = params['msg']
                txt = json.dumps({'jsonrpc': jsonrpc_version, 'id': id_, 'result': msg})
            else:
                raise NameError('Unknown method "{}"'.format(method))
        except Exception as e:
            txt = json.dumps({'jsonrpc': jsonrpc_version, 'id': id_, 'error': {'message': str(e), 'data': None}})
        Client.instance().send(-1, CMDTYPE_JSONRPC_RES, packInfo.src_unit_id, packInfo.srcUnitClientId,
                               packInfo.srcUnitClientType, txt)

    pass

    Client.instance().on_connect_success = ConnectSuccess
    Client.instance().on_connect_fail = onConnectFail
    Client.instance().on_disconnect = onDisconnect
    Client.instance().on_receive_text = onReceiveText

    Client.instance().connect()

    cond_connect.wait()

    started_cond.acquire()
    started_cond.notify()
    started_cond.release()

    term_cond.wait()
    logging.getLogger('ServerProcess').debug('terminate')
    logging.getLogger('ServerProcess').debug('finalize smartbus...')
    Client.instance().finalize()
    logging.getLogger('ServerProcess').debug('finalize smartbus OK.')


class JsonRpcTest(unittest.TestCase):
    is_connected = False
    pending_invokes = {}
    pending_lock = threading.Lock()
    unitid = -1

    @classmethod
    def setUpClass(cls):
        cls._is_svrproc_started = multiprocessing.Condition()
        cls._is_svrproc_term = multiprocessing.Condition()
        cls._is_svrproc_started.acquire()
        cls._server_proc = multiprocessing.Process(target=run_echo_server,
                                                   args=(cls._is_svrproc_started, cls._is_svrproc_term))
        cls._server_proc.daemon = True
        cls._server_proc.start()
        logging.getLogger('MainProcess').debug('setUpClass waiting server proc')
        cls._is_svrproc_started.wait()
        logging.getLogger('MainProcess').debug('setUpClass server proc started')

        Client.initialize(CLIENT_CLIENT_ID, 17)

        cls._client = Client.instance()

        if not cls.is_connected:
            cond_connect = threading.Condition()
            cond_connect.acquire()

            def ConnectSuccess(unitId):
                logging.getLogger('MainProcess').info('ConnectSuccess: unit_id={}'.format(unitId))
                cls.is_connected = True
                cls.unitid = unitId
                cond_connect.acquire()
                cond_connect.notify()
                cond_connect.release()

            pass

            def onConnectFail(unitId, errno):
                logging.getLogger('MainProcess').error('ConnectFail: unitId={}, errno={}'.format(unitId, errno))
                cls.is_connected = False
                cond_connect.acquire()
                cond_connect.notify()
                cond_connect.release()

            pass

            def onDisconnect():
                logging.getLogger('MainProcess').warn('Disconnect')
                cls.is_connected = False
                cond_connect.acquire()
                cond_connect.notify()
                cond_connect.release()

            pass

            def onReceiveText(packInfo, txt):
                #                 print('ReceiveText: txt={1}'.format(packInfo, txt))
                reqobj = json.loads(txt)
                id_ = reqobj['id']
                try:
                    with cls.pending_lock:
                        pending = cls.pending_invokes[id_]
                    cond = pending[0]
                    try:
                        pending[1] = reqobj['result']
                    except KeyError:
                        try:
                            pending[1] = Exception('{}'.format(reqobj['error']))
                        except KeyError:
                            raise KeyError(
                                'neither result nor error attribute can be found in json rpc response message')
                except Exception as e:
                    pending[2] = e
                cond.acquire()
                cond.notify()
                cond.release()

            pass

            cls._client.on_connect_success = ConnectSuccess
            cls._client.on_connect_fail = onConnectFail
            cls._client.on_disconnect = onDisconnect
            cls._client.on_receive_text = onReceiveText

            cls._client.connect()
            cond_connect.wait()
            cls.assertTrue(cls.is_connected, 'setUpClass connect failed.')

    @classmethod
    def tearDownClass(cls):
        logging.getLogger('MainProcess').debug('tearDownClass: terminate server proc...')
        cls._is_svrproc_term.acquire()
        cls._is_svrproc_term.notify()
        cls._is_svrproc_term.release()
        cls._server_proc.join()
        logging.getLogger('MainProcess').debug('tearDownClass: server proc terminated')

    def test_echo(self):
        cls = type(self)
        id_ = uuid.uuid1().hex
        msg = 'Hello! 你好！'
        cond = threading.Condition()
        cond.acquire()
        self._client.send(
            cmd=0,
            cmd_type=CMDTYPE_JSONRPC_REQ,
            dst_unit_id=cls.unitid,
            dst_client_id=SERVER_CLIENT_ID,
            dst_client_type=-1,
            data=json.dumps({
                'jsonrpc': jsonrpc_version,
                'id': id_,
                'method': 'Echo',
                'params': {
                    'msg': msg
                }
            })
        )
        with cls.pending_lock:
            pending = cls.pending_invokes[id_] = [cond, None]
        cond.wait()
        with cls.pending_lock:
            cls.pending_invokes.pop(id_)
        result = pending[1]
        if isinstance(result, Exception):
            raise result
        self.assertEqual(result, msg)

    def test_concurrent_echo(self):
        cls = type(self)

        def _echo(index):
            id_ = uuid.uuid1().hex
            msg = '{}: test_concurrent_echo: Hello! 你好！'.format(index)
            cond = threading.Condition()
            cond.acquire()

            with cls.pending_lock:
                pending = cls.pending_invokes[id_] = [cond, None]

            #             print('[{}] >>> send'.format(index))
            try:
                self._client.send(
                    cmd=0,
                    cmd_type=CMDTYPE_JSONRPC_REQ,
                    dst_unit_id=cls.unitid,
                    dst_client_id=SERVER_CLIENT_ID,
                    dst_client_type=-1,
                    data=json.dumps({
                        'jsonrpc': jsonrpc_version,
                        'id': id_,
                        'method': 'Echo',
                        'params': {
                            'msg': msg
                        }
                    })
                )
            except:
                with cls.pending_lock:
                    cls.pending_invokes.pop(id_)
                raise
            #             print('[{}] <<< send'.format(index))

            cond.wait()
            with cls.pending_lock:
                cls.pending_invokes.pop(id_)
            result = pending[1]
            if isinstance(result, Exception):
                raise result
            self.assertEqual(result, msg)

        threads = []

        for i in range(100):
            trd = threading.Thread(target=_echo, args=(i,))
            trd.daemon = True
            threads.append(trd)
            trd.start()

        for i in range(len(threads)):
            trd = threads[i]
            trd.join()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
