#!/usr/local/bin/python3
# encoding: utf-8
'''
ipc_echoserver -- shortdesc

ipc_echoserver is a description

It defines classes_and_methods

@author:     user_name
        
@copyright:  2013 organization_name. All rights reserved.
        
@license:    license

@contact:    user_email
@deffield    updated: Updated
'''

import sys
import os

from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

__all__ = []
__version__ = 0.1
__date__ = '2013-03-05'
__updated__ = '2013-03-05'

DEBUG = 1
TESTRUN = 0
PROFILE = 0

__cnt__ = 0

try:
    readln = raw_input
except NameError:
    readln = input

def start_server(*args, **kwargs):
    '''
    启动服务器
    '''
    program_args = kwargs['program_args']
    
    import smartbus.ipcclient
    
    def on_connect_ok(unitId):
        print('connected!', unitId)
        
    def on_connect_err(unitId, errno):
        print('connect error:', unitId, errno)
        
    def on_receive(packInfo, txt):
        cli.sendText(9, 9, packInfo.srcUnitId, packInfo.srcUnitClientId, packInfo.dstUnitClientType, txt)
    
    def onInvokeFlowRespond(packInfo, project, invokeId, result):
        print('flow respond:', packInfo, project, invokeId, result)
    
    def onInvokeFlowTimeout(packInfo, project, invokeId):
        print('flow timeout:', packInfo, project, invokeId)
       
    if sys.version_info[0] < 3:
        def onglobalconnect(client, unitid, clientid, clienttype, status, ext_info):
            print('onglobalconnect:', unitid, clientid, clienttype, status, ext_info)
    else:
        def onglobalconnect(unitid, clientid, clienttype, status, ext_info):
            print('onglobalconnect:', unitid, clientid, clienttype, status, ext_info)
    
    smartbus.ipcclient.Client.initialize(program_args.clientid, program_args.clienttype, onglobalconnect)
    cli = smartbus.ipcclient.Client.instance(extInfo='我是 ipc_echoserver')
    assert(cli)
    cli.connect()
    cli.onConnectSuccess = on_connect_ok
    cli.onConnectFail = on_connect_err
    cli.onReceiveText = on_receive
    cli.onInvokeFlowRespond = onInvokeFlowRespond
    cli.onInvokeFlowTimeout = onInvokeFlowTimeout
    
    while True:
        readln()
    

class CLIError(Exception):
    '''Generic exception to raise and log different fatal errors.'''
    def __init__(self, msg):
        super(CLIError).__init__(type(self))
        self.msg = "E: %s" % msg
    def __str__(self):
        return self.msg
    def __unicode__(self):
        return self.msg

def main(argv=None):  # IGNORE:C0111
    '''Command line options.'''
    
    if argv is None:
        argv = sys.argv
    else:
        sys.argv.extend(argv)

    program_name = os.path.basename(sys.argv[0])
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = __import__('__main__').__doc__.split("\n")[1]
    program_license = '''%s

  Created by user_name on %s.
  Copyright 2013 organization_name. All rights reserved.
  
  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0
  
  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

USAGE
''' % (program_shortdesc, str(__date__))

    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-i", "--client-id", dest="clientid", type=int, help="smartbus IPC client ID")
        parser.add_argument("-t", "--client-type", dest="clienttype", type=int, default=-1, help="smartbus IPC client ID type")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        
        # Process arguments
        args = parser.parse_args()
        start_server(program_args=args)

        return 0
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 0
    except Exception as e:
        if DEBUG or TESTRUN:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2

if __name__ == "__main__":
    if DEBUG:
        pass
    if TESTRUN:
        import doctest
        doctest.testmod()
    if PROFILE:
        import cProfile
        import pstats
        profile_filename = 'echo_server_profile.txt'
        cProfile.run('main()', profile_filename)
        statsfile = open("profile_stats.txt", "wb")
        p = pstats.Stats(profile_filename, stream=statsfile)
        stats = p.strip_dirs().sort_stats('cumulative')
        stats.print_stats()
        statsfile.close()
        sys.exit(0)
    sys.exit(main())