#!/usr/bin/env python
#
# this checks various forms of URLS for reaching a PLCAPI
# i.e. with http:// or https:// (only the latter is expected to work)
# with or without a trailing slash
# using a hostname or an IP

import socket
import xmlrpclib
import traceback

class PlcapiUrlScanner:

    # turns out the config has an ip but no name..
    def __init__ (self, auth, hostname=None, ip=None, verbose=False):
        self.auth=auth
        if not hostname and not ip:
            raise Exception,"PlcapiUrlScanner needs _some_ input"
        if hostname:
            if not ip: 
                try:    ip=socket.gethostbyname(hostname)
                except: 
                    hostname="%s.pl.sophia.inria.fr"%hostname
                    ip=socket.gethostbyname(hostname)
        else:
            if not hostname: hostname=socket.gethostbyaddr(ip)[0]
        self.hostname=hostname
        self.ip=ip
        self.verbose=verbose
        
    def try_url (self,url):
        try:
            xmlrpclib.ServerProxy (url, verbose=self.verbose, allow_none=True).GetNodes(self.auth)
            print 'YES',url
            return True
        except xmlrpclib.ProtocolError as e:
            print '... (http error %s)'%e.errcode,url
            return False
        except Exception as e:
            print '---',type(e).__name__,url,e
            if self.verbose: traceback.print_exc()
            return False

    def try_url_expected (self, url, expected):
        return self.try_url(url)==expected

    def scan(self):
        overall=True
        for protocol in ['http','https']:
            expected= protocol=='https'
            for dest in [ self.hostname, self.ip ]:
                for port in [ '',':80',':443']:
                    for path in ['PLCAPI','PLCAPI/']:
                        if protocol=='http' and port==':443': continue
                        if protocol=='https' and port==':80': continue
                        url="%s://%s%s/%s"%(protocol,dest,port,path)
                        if not self.try_url_expected (url,expected): overall=False
        return overall

from optparse import OptionParser
import sys

auth={'AuthMethod':'password','Username':'root@test.onelab.eu','AuthString':'test++'}

def main ():
    usage="%prog hostname"
    parser=OptionParser()
    parser.add_option("-v","--verbose",dest='verbose',action='store_true',default=False)
    (options,args)=parser.parse_args()
    if len(args)!=1:
        parser.print_help()
        sys.exit(1)
    hostname=args[0]
    success=PlcapiUrlScanner (auth=auth, hostname=hostname,verbose=options.verbose).scan()
    sys.exit(0 if success else -1)

if __name__ == '__main__':
    main()
