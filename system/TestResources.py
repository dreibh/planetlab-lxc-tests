#
# $Id$
#

import sys

import utils
from TestMapper import TestMapper
from TestPool import TestPoolQemu, TestPoolIP
from Trackers import TrackerPlc, TrackerQemu

class TestResources ():

    # need more specialization, see an example in OnelabTestResources

    ########## 
    def localize (self,plcs,options):
        try:
            plcs = self.localize_qemus(plcs,options)
        except:
            print 'Could not localize qemus - exiting'
            sys.exit(1)
        try:
            plcs = self.localize_nodes(plcs,options)
        except:
            print 'Could not localize nodes - exiting'
            sys.exit(1)
        try:
            plcs = self.localize_plcs(plcs,options)
        except:
            print 'Could not localize plcs - exiting'
            sys.exit(1)
        return plcs

    def localize_qemus (self,plcs,options):

        # all plcs on the same vserver box
        plc_box = self.plc_boxes()[0]

        # informative
        label=options.personality.replace("linux","")

        node_map = []
        qemu_pool = TestPoolQemu (self.qemus_ip_pool(), options)

        for index in range(options.size):
            index += 1
            if options.ips_qemu:
                ip_or_hostname=options.ips_qemu.pop()
                (hostname,ip,unused)=qemu_pool.locate_entry(ip_or_hostname)
            else:
                (hostname,ip,unused) = qemu_pool.next_free()

            node_map += [ ('node%d'%index, {'host_box':hostname},) ]

        mapper = {'plc': [ ('*' , {'hostname':plc_box,
                                   'PLC_DB_HOST':plc_box,
                                   'PLC_API_HOST':plc_box,
                                   'PLC_BOOT_HOST':plc_box,
                                   'PLC_WWW_HOST':plc_box,
                                   'name':'%s-'+label } ) 
                           ],
                  'node': node_map,
                  }
    
        return TestMapper(plcs,options).map(mapper)
        

    def localize_nodes (self, plcs, options):
        
        ip_pool = TestPoolIP (self.nodes_ip_pool(),options)
        network_dict = self.network_dict()

        test_mapper = TestMapper (plcs, options)
    
        all_nodenames = test_mapper.node_names()
        maps = []
        for nodename in all_nodenames:
            if options.ips_node:
                ip_or_hostname=options.ips_node.pop()
                print 'debug','in',ip_or_hostname,'out',ip_pool.locate_entry(ip_or_hostname)
                (hostname,ip,mac)=ip_pool.locate_entry(ip_or_hostname)
            else:
                (hostname,ip,mac) = ip_pool.next_free()
            utils.header('Attaching node %s to %s (%s)'%(nodename,hostname,ip))
            node_dict= {'node_fields:hostname':hostname,
                        'interface_fields:ip':ip, 
                        'interface_fields:mac':mac,
                        }
        
            node_dict.update(network_dict)
            maps.append ( ( nodename, node_dict) )
    
        plc_map = [ ( '*' , { 'PLC_NET_DNS1' : network_dict [ 'interface_fields:dns1' ],
                              'PLC_NET_DNS2' : network_dict [ 'interface_fields:dns2' ], } ) ]
    
        return test_mapper.map ({'node': maps, 'plc' : plc_map } )
        

    def localize_plcs (self,plcs,options):
        
        utils.header ("Turning configuration into a vserver-based one for onelab")
    
        ip_pool = TestPoolIP (self.plcs_ip_pool(),options)
    
        plc_counter=0
        for plc in plcs:
            if options.ips_plc :
                ip_or_hostname=options.ips_plc.pop()
                (hostname,ip,mac)=ip_pool.locate_entry(ip_or_hostname)
                if options.verbose:
                    utils.header("Using user-provided %s %s for plc %s"%(
                            hostname,ip_or_hostname,plc['name']))
            else:
                (hostname,ip,mac)=ip_pool.next_free()
                if options.verbose:
                    utils.header("Using auto-allocated %s %s for plc %s"%(
                            hostname,ip,plc['name']))
    
            ### rewrite fields in plc
            # compute a helpful vserver name - remove domain in hostname
            simplehostname=hostname.split('.')[0]
            vservername = options.buildname
            if len(plcs) == 1 :
                vservername = "%s-%s" % (vservername,simplehostname)
            else:
                plc_counter += 1
                vservername = "%s-%d-%s" % (vservername,plc_counter,simplehostname)
            # apply
            plc['vservername']=vservername
            plc['vserverip']=ip
            plc['name'] = "%s_%s"%(plc['name'],simplehostname)
            utils.header("Attaching plc %s to vserver %s (%s)"%(
                    plc['name'],plc['vservername'],plc['vserverip']))
            for key in [ 'PLC_DB_HOST', 'PLC_API_HOST', 'PLC_WWW_HOST', 'PLC_BOOT_HOST',]:
                plc[key] = hostname
    
        return plcs

    # as a plc step this should return a boolean
    def step_pre (self,plc):
        return self.trqemu_record (plc) and self.trqemu_free(plc)

    def step_post (self,plc):
        return self.trplc_record (plc) and self.trplc_free(plc)

    def step_cleanup (self,plc):
        return self.trqemu_cleanup(plc) and self.trplc_cleanup(plc)

    ####################
    def trqemu_record (self,plc):
        tracker=TrackerQemu(plc.options,instances=self.max_qemus()-1)
        for site_spec in plc.plc_spec['sites']:
            for node_spec in site_spec['nodes']:
                tracker.record(node_spec['host_box'],plc.options.buildname,node_spec['node_fields']['hostname'])
        tracker.store()
        return True

    def trqemu_free (self,plc):
        tracker=TrackerQemu(plc.options,instances=self.max_qemus()-1)
        for site_spec in plc.plc_spec['sites']:
            for node_spec in site_spec['nodes']:
                tracker.free()
        tracker.store()
        return True

    ###
    def trplc_record (self):
        tracker = TrackerPlc(plc.options,instances=self.max_plcs())
        tracker.record(self.test_ssh.hostname,self.vservername)
        tracker.store()
        return True

    def trplc_free (self):
        tracker = TrackerPlc(plc.options,instances=self.max_plcs())
        tracker.free()
        tracker.store()
        return True

    ###
    def trqemu_cleanup (self,plc):
        tracker=TrackerQemu(plc.options,instances=self.max_qemus()-1)
        for site_spec in plc.plc_spec['sites']:
            for node_spec in site_spec['nodes']:
                tracker.cleanup()
        tracker.store()
        return True

    def trplc_cleanup (self,plc):
        tracker = TrackerPlc(plc.options,instances=self.max_plcs())
        tracker.cleanup()
        tracker.store()
        return True

