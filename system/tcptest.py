#!/usr/bin/env python

# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import sys
import time
import subprocess
import socket
import SocketServer
from optparse import OptionParser    

def myprint(message, is_client=True):
    now=time.strftime("%H:%M:%S", time.localtime())
    id = 'tcpclient' if is_client else 'tcpserver'
    print "*",now,'(%s)' % id, '--',message
    sys.stdout.flush()

def show_network_status(is_client):
    myprint("ip address show", is_client=is_client)
    subprocess.call(['ip','address','show'])
    myprint("ip route show", is_client=is_client)
    subprocess.call(['ip','route','show'])

class EchoRequestHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        line = self.rfile.readline()
        self.wfile.write(line)

class UppercaseRequestHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        line = self.rfile.readline()
        self.wfile.write(line.upper())

class Server:

    def main(self):
        import threading

        parser = OptionParser()
        parser.add_option("-p", "--port", action="store", dest="port", type="int",
                          default=10000, help="port number")
        parser.add_option("-a", "--address", action="store", dest="address", 
                          default=socket.gethostname(), help="address")
        parser.add_option("-t", "--timeout", action="store", dest="timeout", type="int",
                          default="0")
        
        (options, args) = parser.parse_args()
        if len(args) != 0:
            parser.print_help()
            sys.exit(1)

        show_network_status(is_client=False)

        server = SocketServer.TCPServer((options.address, options.port),
                                        UppercaseRequestHandler)

        try:
            if options.timeout:
                t = threading.Thread(target=server.serve_forever)
                t.setDaemon(True) # don't hang on exit
                t.start()
                time.sleep(options.timeout)
                sys.exit(0)
            else:
                server.serve_forever()        
        except KeyboardInterrupt as e:
            print 'Bailing out on keyboard interrupt'
            sys.exit(1)
            
class Client:
    def main(self):
        parser = OptionParser()
        parser.add_option("-p","--port", action="store", dest="port", type="int",
                          default=10000, help="port number")
        parser.add_option("-a","--address", action="store", dest="address", 
                          default=socket.gethostname(), help="address")
        parser.add_option("-s","--sleep", action="store", dest="sleep", type="int",
                          default=1, help="sleep seconds")
        parser.add_option("-l","--loops", action="store", dest="loops", type="int",
                          default=1, help="iteration loops")
        
        (options, args) = parser.parse_args()
        if len(args) != 0:
            parser.print_help()
            sys.exit(1)

        result=True
        for i in range(1,options.loops+1):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((options.address , options.port))
            mout=i*'ping ' + '\n'
            min=mout.upper()
            if s.send(mout) != len(mout):
                myprint("cannot send %s"%mout.strip())
                result=False
                break
            line=s.recv(len(min))
            if line is not line:
                myprint("unexpected reception\ngot:%s\nexpected: %s",line,min)
                result=False
            else:
                myprint("OK:%s"%mout.strip())
            # leave the connection open, but the last one (so 1 iter returns fast)
            if i != options.loops:
                time.sleep(options.sleep)
            myprint("disconnecting")
            s.close()
        myprint("Done")
        exit_return=0
        if not result:
            exit_return=1
        sys.exit(exit_return)

if __name__ == '__main__':
    for argv in sys.argv[1:]:
        if argv.find("client") >= 0:
            sys.argv.remove(argv)
            Client().main()
        elif argv.find("server") >= 0:
            sys.argv.remove(argv)
            Server().main()
    print 'you must specify either --client or --server'
    sys.exit(1)
