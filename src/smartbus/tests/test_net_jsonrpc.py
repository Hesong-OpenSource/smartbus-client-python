#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
Created on 2013年11月22日

@author: tanbro
'''
import unittest
import sys
import threading
import json
import logging
import uuid
import multiprocessing

logging.root.level = logging.DEBUG

from smartbus.netclient.client import Client

jsonrpc_version = '2.0'

CMDTYPE_JSONRPC_REQ = 211
'''JSONRPC 请求. 用于 smartbus 客户端 send 函数的 cmd_type 参数.'''

CMDTYPE_JSONRPC_RES = 212
'''JSONRPC 回复. 用于 smartbus 客户端 send 函数的 cmd_type 参数.'''


CLIENT_UNIT_ID = 38
SERVER_UNIT_ID = 39

SMARTBUS_HOST = '10.4.62.45'  # '192.168.5.10'
SMARTBUS_PORT = 8089

def run_echo_server(started_cond, term_cond):
    print('ServerProcess')
    term_cond.acquire()
    
    _connected = False
    
    Client.initialize(SERVER_UNIT_ID)
    client = Client(0, 19, SMARTBUS_HOST, SMARTBUS_PORT)
    
    cond_connect = threading.Condition()
    cond_connect.acquire()

    def ConnectSuccess(unitId):
        logging.getLogger('ServerProcess').info('ConnectSuccess: unitid={}'.format(unitId))
        print('ServerProcess: ConnectSuccess: unitid={}'.format(unitId))
        nonlocal _connected 
        _connected = True
        cond_connect.acquire()
        cond_connect.notify()
        cond_connect.release()
    pass
    
    def onConnectFail(unitId, errno):
        logging.getLogger('ServerProcess').error('ConnectFail: unitId={}, errno={}'.format(unitId, errno))
        print('ServerProcess: ConnectFail: unitId={}, errno={}'.format(unitId, errno))
        nonlocal _connected 
        _connected = False
        cond_connect.acquire()
        cond_connect.notify()
        cond_connect.release()
    pass                
    
    def onDisconnect():
        logging.getLogger('ServerProcess').warn('Disconnect')
        print('ServerProcess: Disconnect')
        nonlocal _connected
        _connected = False
        cond_connect.acquire()
        cond_connect.notify()
        cond_connect.release()
    pass

    def onReceiveText(packInfo, txt):
        print('Server Process: ReceiveText: txt={1}'.format(packInfo, txt))
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
                txt = json.dumps({'jsonrpc':jsonrpc_version, 'id':id_, 'result':msg})
            else:
                raise NameError('Unknown method "{}"'.format(method))
        except Exception as e:
            txt = json.dumps({'jsonrpc':jsonrpc_version, 'id':id_, 'error':{'message' : str(e), 'data' : None}})
        client.send(-1, CMDTYPE_JSONRPC_RES, packInfo.srcUnitId, packInfo.srcUnitClientId, packInfo.srcUnitClientType, txt)
    pass
    
    client.onConnectSuccess = ConnectSuccess
    client.onConnectFail = onConnectFail
    client.onDisconnect = onDisconnect
    client.onReceiveText = onReceiveText
    
    print('ServerProcess: connecting...')
    client.connect()
    
    cond_connect.wait()
    print('ServerProcess: connected={}'.format(_connected))
    
    started_cond.acquire()
    started_cond.notify()
    started_cond.release()
    
    term_cond.wait()
    logging.getLogger('ServerProcess').debug('terminate')
    logging.getLogger('ServerProcess').debug('finalize smartbus...')
    Client.finalize()
    logging.getLogger('ServerProcess').debug('finalize smartbus OK.')



class JsonRpcTest(unittest.TestCase):

    is_connected = False
    pending_invokes = {}
    pending_lock = threading.Lock()
    unitid = -1
        
    @classmethod
    def setUpClass(cls):
        print('setUpClass')
        cls._is_svrproc_started = multiprocessing.Condition()
        cls._is_svrproc_term = multiprocessing.Condition()
        cls._is_svrproc_started.acquire()
        cls._server_proc = multiprocessing.Process(target=run_echo_server, args=(cls._is_svrproc_started, cls._is_svrproc_term))
        cls._server_proc.daemon = True
        cls._server_proc.start()
        logging.getLogger('MainProcess').debug('setUpClass waiting server proc')
        cls._is_svrproc_started.wait()
        logging.getLogger('MainProcess').debug('setUpClass server proc started')
        
        Client.initialize(CLIENT_UNIT_ID)
            
        cls._client = Client(0 , 18, SMARTBUS_HOST, SMARTBUS_PORT)
            
        if not cls.is_connected:
            cond_connect = threading.Condition()
            cond_connect.acquire()
        
            def ConnectSuccess(unitId):
                logging.getLogger('MainProcess').info('ConnectSuccess: unitid={}'.format(unitId))
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
                print('ReceiveText: txt={1}'.format(packInfo, txt))
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
                            raise KeyError('neither result nor error attribute can be found in json rpc response message')
                except Exception as e:
                    pending[2] = e
                cond.acquire()
                cond.notify()
                cond.release()
            pass
            
            cls._client.onConnectSuccess = ConnectSuccess
            cls._client.onConnectFail = onConnectFail
            cls._client.onDisconnect = onDisconnect
            cls._client.onReceiveText = onReceiveText
            
            cls._client.connect()
            cond_connect.wait()
            cls.assertTrue(cls.is_connected, 'setUpClass connect failed.')

    @classmethod
    def tearDownClass(cls):
        print('tearDownClass')
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
            cmdType=CMDTYPE_JSONRPC_REQ,
            dstUnitId=SERVER_UNIT_ID,
            dstClientId=0,
            dstClientType=-1,
            data=json.dumps({
                'jsonrpc' : jsonrpc_version,
                'id' : id_,
                'method' : 'Echo',
                'params' : {
                    'msg' : msg
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
        
        
    def test_echo_thread(self):
        cls = type(self)
         
        def _echo(index):
            id_ = uuid.uuid1().hex
            msg = '{}: test_concurrent_echo: Hello! 你好！'.format(index)
            cond = threading.Condition()
            cond.acquire()
 
            with cls.pending_lock:
                pending = cls.pending_invokes[id_] = [cond, None]
 
            print('[{}] >>> send'.format(index))
            try:
                self._client.send(
                    cmd=0,
                    cmdType=CMDTYPE_JSONRPC_REQ,
                    dstUnitId=SERVER_UNIT_ID,
                    dstClientId=0,
                    dstClientType=-1,
                    data=json.dumps({
                        'jsonrpc' : jsonrpc_version,
                        'id' : id_,
                        'method' : 'Echo',
                        'params' : {
                            'msg' : msg
                        }
                    })
                )
            except:
                with cls.pending_lock:
                    cls.pending_invokes.pop(id_)
                raise
            print('[{}] <<< send'.format(index))       
                 
            print('[{}] >>> wait'.format(index))  
            cond.wait()
            print('[{}] <<< wait'.format(index))
            with cls.pending_lock:
                cls.pending_invokes.pop(id_)
            result = pending[1]
            if isinstance(result, Exception):
                raise result
            self.assertEqual(result, msg)
         
        threads = []
        
        for i in range(10):
            trd = threading.Thread(target=_echo, args=(i,))
            trd.daemon = True
            threads.append(trd)
            trd.start()
             
        for i in range(len(threads)):
            print('[{}] joinning...'.format(i))
            trd = threads[i]
            trd.join()
            print('[{}] joinned'.format(i))

if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
