# $Id$
# wrapper to xmlrpc server, that support dry-run commands
# we dont want to have to depend on PLCAPI, so:
import xmlrpclib

server_methods = [ ('GetNodes' ,  []),
                   ('AddNode' , True),
                   ('DeleteNode' , True),
                   ('UpdateNode' , True),
                   ('AddInterface' , True),
                   ('GetInterfaces' , True),
                   ('GetTagTypes' , []),
                   ('AddTagType' , True),
                   ('AddInterfaceSetting' , True),
                   ('GetBootMedium' , True),
                   ('GetNodeGroups' , True),
                   ('AddNodeGroup' , True),
                   ('DeleteNodeGroup', True),
                   ('GetNodeTags', True),
                   ('AddInitScript' , True),
                   ('DeleteInitScript', True),
                   ('GetInitScripts', True),
                   ('AddSite' , True),
                   ('AddSiteAddress' , True),
                   ('DeleteSite' , True),
                   ('DeleteSlice' , True),
                   ('AddSlice' , True),
                   ('AddPersonToSlice' , True),
                   ('AddSliceToNodes' , True),
                   ('AddSliceAttribute' , True),
                   ('AddPerson' , True),
                   ('UpdatePerson' , True),
                   ('AddRoleToPerson' , True),
                   ('AddPersonToSite' , True),
                   ('DeletePerson' , True),
                   ('AddPersonKey' , True),
                   ('GetPlcRelease', {'build': {'target-arch':'i386'}}),
                   ('GetSites', []),
                   ]

class TestApiserver:
    class Callable:
        def __init__(self,server,dry_run,method,defaults):
            self.server=server
            self.dry_run=dry_run
            self.method=method
            self.defaults=defaults
        def __call__ (self, *args):
            if self.dry_run:
                print "dry_run:",self.method,
                if len(args)>0 and type(args[0])==type({}) and args[0].has_key('AuthMethod'):
                    print '<auth>',
                    args=args[1:]
                print '(',args,')'
                return self.defaults
            else:
                actual_method=getattr(self.server,self.method)
                return actual_method(*args)

    def __init__(self,url,dry_run=False):
        self.apiserver = xmlrpclib.Server(url,allow_none=True)
        self.dry_run=dry_run
        for (method,defaults) in server_methods:
            setattr(self,method,TestApiserver.Callable(self.apiserver,dry_run,method,defaults))
