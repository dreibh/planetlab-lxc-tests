#!/usr/bin/env python3

# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA
#

# this is a small and simple standalone utility
# designed to run in slice-space
# we keep this in python2 for now until python3
# can be taken for granted in sliceimage

# pylint: disable=c0111, c0103, w0622, r0903, r0201, w0703

import sys
import time
import subprocess
import socket
import socketserver
import threading
from argparse import ArgumentParser


def myprint(message, id='client'):
    now = time.strftime("%H:%M:%S", time.localtime())
    print("* {now} ({id}) -- {message}"
          .format(now=now, id=id, message=message))
    sys.stdout.flush()


def show_network_status(id):
    myprint("ip address show", id=id)
    subprocess.call(['ip', 'address', 'show'])
    myprint("ip route show", id=id)
    subprocess.call(['ip', 'route', 'show'])


class EchoRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        line = self.rfile.readline()
        self.wfile.write(line)


class UppercaseRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        line = self.rfile.readline()
        self.wfile.write(line.upper())


class Server:
    """
    A TCP server, running for some finite amount of time
    """
    def main(self):
        parser = ArgumentParser()
        parser.add_argument("-p", "--port", type=int, default=10000,
                            action="store", dest="port",
                            help="port number")
        parser.add_argument("-a", "--address", action="store", dest="address",
                            default=socket.gethostname(), help="address")
        parser.add_argument("-t", "--timeout", action="store", dest="timeout",
                            type=int, default="0")
        args = parser.parse_args()

        if not args:
            parser.print_help()
            sys.exit(1)

        myprint("==================== tcptest.py server on {}:{}"
                .format(args.address, args.port),
                id='server')
        show_network_status(id='server')
        server = socketserver.TCPServer((args.address, args.port),
                                        UppercaseRequestHandler)
        try:
            if args.timeout:
                t = threading.Thread(target=server.serve_forever)
                t.setDaemon(True)  # don't hang on exit
                t.start()
                time.sleep(args.timeout)
                sys.exit(0)
            else:
                server.serve_forever()
        except KeyboardInterrupt:
            print('Bailing out on keyboard interrupt')
            sys.exit(1)


class Ready:
    """
    A utility that does exit(0) iff network as perceived
    from the sliver is ready. Designed to be run before Server,
    so one can wait for the right conditions.
    """
    def main(self):
        parser = ArgumentParser()
        # by default use another port so we don't run into
        # the SO_LINGER kind of trouble
        parser.add_argument("-p", "--port", action="store", dest="port",
                            type=int, default=9999, help="port number")
        parser.add_argument("-a", "--address", action="store", dest="address",
                            default=socket.gethostname(), help="address")
        args = parser.parse_args()

        myprint("==================== tcptest.py ready", id='ready')

        def can_bind():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.bind((args.address, args.port))
                return True
            except Exception as e:
                print(e)
                return False

        def eth0_has_ipv4():
            command = "ip address show eth0 | grep -q ' inet '"
            return subprocess.check_call(command, shell=True) == 0

        sys.exit(0 if can_bind() and eth0_has_ipv4() else 1)


class Client:
    """
    Runs a client against a Server instance
    """
    def main(self):
        parser = ArgumentParser()
        parser.add_argument("-p", "--port", action="store", dest="port",
                            type=int, default=10000, help="port number")
        parser.add_argument("-a", "--address", action="store", dest="address",
                            default=socket.gethostname(), help="address")
        parser.add_argument("-s", "--sleep", action="store", dest="sleep",
                            type=int, default=1, help="sleep seconds")
        parser.add_argument("-l", "--loops", action="store", dest="loops",
                            type=int, default=1, help="iteration loops")

        args = parser.parse_args()
        if not args:
            parser.print_help()
            sys.exit(1)

        myprint("==================== tcptest.py client -> {}:{}"
                .format(args.address, args.port),
                id='client')
        result = True
        for i in range(1, args.loops+1):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((args.address, args.port))
            mout = i*b'ping_out ' + b'\n'
            min =  i*b'PING_in  ' + b'\n'
            if s.send(mout) != len(mout):
                myprint("cannot send {}".format(mout.strip()))
                result = False
                break
            line = s.recv(len(min))
            if line is not line:
                myprint("unexpected reception\ngot:{}\nexpected: {}"
                        .format(line, min))
                result = False
            else:
                myprint("OK:{}".format(mout.strip()))
            # leave the connection open, but the last (so 1 iter returns fast)
            if i != args.loops:
                time.sleep(args.sleep)
            myprint("disconnecting")
            s.close()
        myprint("Done")
        exit_return = 0
        if not result:
            exit_return = 1
        sys.exit(exit_return)


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        if arg.find("client") >= 0:
            sys.argv.remove(arg)
            Client().main()
        elif arg.find("server") >= 0:
            sys.argv.remove(arg)
            Server().main()
        elif arg.find("ready") >= 0:
            sys.argv.remove(arg)
            Ready().main()
    print('you must specify either --client or --server')
    sys.exit(1)
