# a rough utility for testing xmlrpclib URL's
import xmlrpclib
auth={'AuthMethod':'password','Username':'root@test.onelab.eu','AuthString':'test++'}

host='vplc21'

import socket
hostname="%s.pl.sophia.inria.fr"%host
ip=socket.gethostbyname(hostname)

import traceback
verbose=True

def try_url (url,xmlrpclib_verbose=False):
    try:
        xmlrpclib.ServerProxy (url, verbose=xmlrpclib_verbose, allow_none=True).GetNodes(auth)
        print 'YES',url
    except xmlrpclib.ProtocolError as e:
        print '... (http error %s)'%e.errcode,url
    except Exception as e:
        print '---',type(e).__name__,url
        if verbose: traceback.print_exc()

def scan():
    for protocol in ['http','https']:
        for dest in [ hostname, ip ]:
            for port in [ '',':80',':443']:
#            for port in [ ':80',':443']:
                for path in ['PLCAPI','PLCAPI/']:
                    if protocol=='http' and port==':443': continue
                    if protocol=='https' and port==':80': continue
                    url="%s://%s%s/%s"%(protocol,dest,port,path)
                    try_url (url)

