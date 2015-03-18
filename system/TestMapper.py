#
# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
#
# mapper class
# 
# this works on a spec as defined in a config file
# and allows to remap various fields on the local substrate
# 

import utils

class TestMapper:

    def __init__(self,plcs,options):
        self.plcs = plcs
        self.options = options

    @staticmethod
    def plc_name(plc):
        return plc['name']

    @staticmethod
    def node_name(node):
        return node['name']

    def node_names(self):
        result = []
        for plc in self.plcs:
            for site in plc['sites']:
                for node in site['nodes']:
                    result.append(node['name'])
        return result

    def apply_first_map(self, type, name, obj, maplist):
        for (map_pattern,rename_dict) in maplist:
            if utils.match (name,map_pattern):
                if self.options.verbose:
                    utils.header("TestMapper/{} : applying rules '{}' on {}"\
                                 .format(type, map_pattern, name))
                for (k,v) in rename_dict.items():
                    # apply : separator
                    path = k.split(':')
                    # step down but last step in path
                    o = obj
                    for step in path[:-1]:
                        if step not in o:
                            o[step] = {}
                            if self.options.verbose:
                                utils.header ("WARNING : created step {} in path {} on {} {}"\
                                              .format(step,path,type,name))
                        o = o[step]
                    # last step is the one for side-effect
                    step = path[-1]
                    if self.options.verbose:
                        if step not in o:
                            utils.header ("WARNING : inserting key {} for path {} on {} {}"\
                                          .format(step, path, type, name))
                    # apply formatting if '%s' found in the value
                    if v is None:
                        if self.options.verbose: print("TestMapper WARNING - None value - ignored, key=",k)
                        continue
                    if v.find('%s') >= 0:
                        v = v % obj[k]
                    if self.options.verbose:
                        print(("TestMapper, rewriting {}: {} into {}"\
                              .format(name, k, v)))
                    o[step] = v
                # only apply first rule
                return

    def map(self, mapper):

        plc_maps  = mapper.get('plc',[])
        node_maps = mapper.get('node',[])

        for plc in self.plcs:
            name = TestMapper.plc_name(plc)
            self.apply_first_map('plc', name, plc, plc_maps)

            for site in plc['sites']:
                for node in site['nodes']:
                    nodename = TestMapper.node_name(node)
                    self.apply_first_map('node', nodename, node, node_maps)

        return self.plcs
