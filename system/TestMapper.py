#
# Thierry Parmentelat - INRIA Sophia Antipolis 
#
# mapper class
# 
# this works on a spec as defined in a config file
# and allows to remap various fields, typically to another testbox 
# see an example in config-testbox2.py
# 

import re
import utils

class TestMapper:

    def __init__ (self,plcs,mapper,options):
        self.plcs=plcs
        self.mapper=mapper
        self.options=options

    @staticmethod
    def match (name,key):
        key=key.replace("*",".*")
        return re.compile(key).match(name)

    @staticmethod
    def plc_name (plc):
        return plc['name']

    @staticmethod
    def node_name (node):
        return node['node_fields']['hostname']

    def apply_first_map (self, obj, name, type, maplist):
        for (key,dict) in maplist:
            if TestMapper.match (name,key):
                utils.header("TestMapper/%s : applying match key %s on plc %s"%(type,key,name))
                for (k,v) in dict.iteritems():
                    if not obj.has_key(k):
                        utils.header ("WARNING : no such key %s in %s %s",k,type,name)
                    else:
                        # apply formatting if found
                        if v.find('%s')>=0:
                            v=v%obj[k]
                        if self.options.verbose:
                            utils.header("mapping %s->%s towards %s"%(name,k,v))
                        obj[k]=v
                break

    def map (self):

        plc_maps = self.mapper['plc']

        for plc in self.plcs:
            name=TestMapper.plc_name(plc)
            self.apply_first_map (plc,name,'plc',plc_maps)

            node_maps = self.mapper['node']

            for site in plc['sites']:
                for node in site['nodes']:
                    nodename = TestMapper.node_name(node)
                    self.apply_first_map(node,nodename,"node",node_maps)

        return self.plcs
                                               
                                              
