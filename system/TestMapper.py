#
# Thierry Parmentelat - INRIA Sophia Antipolis 
#
# mapper class
# 
# this works on a spec as defined in a config file
# and allows to remap various fields, typically to another testbox 
# see an example in config_onelab_testbox32.py
# 

import utils

class TestMapper:

    def __init__ (self,plcs,options):
        self.plcs=plcs
        self.options=options

    @staticmethod
    def plc_name (plc):
        return plc['name']

    @staticmethod
    def node_name (node):
        return node['node_fields']['hostname']

    def apply_first_map (self, type, name, obj, maplist):
        for (map_pattern,rename_dict) in maplist:
            if utils.match (name,map_pattern):
                utils.header("TestMapper/%s : applying rules '%s' on %s"%(type,map_pattern,name))
                for (k,v) in rename_dict.iteritems():
                    # apply : separator
                    path=k.split(':')
                    # step down but last step in path
                    o=obj
                    for step in path[:-1]:
                        if not o.has_key(step):
                            o[step]={}
                            utils.header ("WARNING : created step %s in path %s on %s %s"%(
                                    step,path,type,name))
                        o=o[step]
                    # last step is the one for side-effect
                    step=path[-1]
                    if not o.has_key(step):
                        utils.header ("WARNING : inserting key %s for path %s on %s %s"%(
                                step,path,type,name))
                    # apply formatting if '%s' found in the value
                    if v.find('%s')>=0:
                        v=v%obj[k]
                    utils.header("TestMapper, rewriting %s: %s into %s"%(name,k,v))
                    o[step]=v
                # only apply first rule
                return

    def node_names (self):
        result=[]
        for plc in self.plcs:
            for site in plc['sites']:
                for node in site['nodes']:
                    result.append(node['node_fields']['hostname'])
        return result

    def map (self,mapper):

        try:
            plc_maps = mapper['plc']
        except:
            plc_maps = []
        try:
            node_maps = mapper['node']
        except:
            node_maps = []

        for plc in self.plcs:
            name=TestMapper.plc_name(plc)
            self.apply_first_map ('plc',name,plc,plc_maps)

            for site in plc['sites']:
                for node in site['nodes']:
                    nodename = TestMapper.node_name(node)
                    self.apply_first_map('node',nodename,node,node_maps)

        return self.plcs
