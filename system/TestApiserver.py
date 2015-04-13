# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
# wrapper to xmlrpc server, that support dry-run commands
# we dont want to have to depend on PLCAPI, so:
import xmlrpc.client

# the default value is for the dry run mode
server_methods = [ ('GetNodes' ,  []),
                   ('AddNode' , True),
                   ('SetNodePlainBootstrapfs', True),
                   ('DeleteNode' , True),
                   ('UpdateNode' , True),
                   ('AddInterface' , True),
                   ('AddIpAddress' , True),
                   ('AddRoute' , True),
                   ('GetInterfaces' , True),
                   ('GetTagTypes' , []),
                   ('AddTagType' , True),
                   ('AddInterfaceTag' , True),
                   ('GetBootMedium' , "some non-empty-string"),
                   ('GetNodeGroups' , True),
                   ('AddNodeGroup' , True),
                   ('DeleteNodeGroup', True),
                   ('GetNodeTags', True),
                   ('AddNodeTag', True),
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
                   ('DeleteSliceFromNodes' , True),
                   ('AddSliceTag' , True),
                   ('AddPerson' , True),
                   ('UpdatePerson' , True),
                   ('AddRoleToPerson' , True),
                   ('AddPersonToSite' , True),
                   ('DeletePerson' , True),
                   ('AddPersonKey' , True),
                   ('GetPlcRelease', {'build': {'target-arch':'i386'}}),
                   ('GetSites', []),
                   ('GetSlices', [{'name':'dry_run_slice','node_ids':['dry_run']}]),
                   ('GetLeaseGranularity', 180),
                   ('AddLeases', True),
                   ('GetLeases', []),
                   ('DeleteLeases',True),
                   ('GetConfFiles',[]),
                   ('AddConfFile','True'),
                   ('GetSliceTags',[]),
                   ('system.listMethods',[]),
                   ]

class TestApiserver:
    class Callable:
        def __init__(self, server, dry_run, method, defaults):
            self.server = server
            self.dry_run = dry_run
            self.method = method
            self.defaults = defaults
        def __call__ (self, *args):
            if self.dry_run:
                print("dry_run:",self.method, end=' ')
                if len(args) > 0 and type(args[0]) == type({}) and 'AuthMethod' in args[0]:
                    print('<auth>', end=' ')
                    args = args[1:]
                print('(', args, ')')
                return self.defaults
            else:
                actual_method = getattr(self.server, self.method)
                return actual_method(*args)

    def __init__(self, url, dry_run=False):
        self.apiserver = xmlrpc.client.ServerProxy(url, allow_none=True,
                                                   use_builtin_types=True)
        self.dry_run = dry_run
        for method, defaults in server_methods:
            setattr(self, method, TestApiserver.Callable(self.apiserver, dry_run, method, defaults))
    
    def set_dry_run (self, dry_run):
        self.dry_run = dry_run
        for (method, defaults) in server_methods:
            getattr(self, method).dry_run = dry_run

    def has_method (self, methodname):
        return methodname in self.apiserver.system.listMethods()
