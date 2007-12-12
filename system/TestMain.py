#!/usr/bin/env python
# $Id$

import os, sys
from optparse import OptionParser
import pprint

import utils
from TestPlc import TestPlc
from TestSite import TestSite
from TestNode import TestNode
import TestConfig

class TestMain:

    subversion_id = "$Id$"

    def __init__ (self):
	self.path=os.path.dirname(sys.argv[0])

    def main (self):
        try:
            usage = """usage: %prog [options] [myplc-url]
myplc-url defaults to the last value used, as stored in URL"""
            parser=OptionParser(usage=usage,version=self.subversion_id)

            parser.add_option("-d","--display", action="store", dest="Xdisplay", default='bellami:0.0',
                              help="sets DISPLAY for vmplayer")
            parser.add_option("-v","--verbose", action="store_true", dest="verbose", default=False, 
                              help="Run in verbose mode")
            parser.add_option("-r","--run", action="store", dest="run_node", 
                              help="Only starts vmplayer for the specified node")
            (self.options, self.args) = parser.parse_args()

            display=''
            url=''
            test_plcs=[]
            test_nodes=[]
            pids=[]
            #test the existence of the URL
            if (len (self.args) > 2):
                parser.print_help()
                sys.exit(1)
            elif (len (self.args) == 1):
                url=self.args[0]
            else:
                try:
                    url_file=open("%s/URL"%self.path)
                    url=url_file.read().strip()
                    url_file.close()
                except:
                    print "Cannot determine myplc url"
                    parser.print_help()
                    sys.exit(1)
            utils.header('* Using myplc at url : %s'%url)
            #check where to display Virtual machines
            if (self.options.Xdisplay):
                display=self.options.Xdisplay
                utils.header('X11 display : %s'% display)
            #the run option 
            if (self.options.run_node):
                file=self.path+'/vmplayer-'+self.options.run_node+'/node.vmx'
                if os.path.exists(file):
                    utils.header('starting vmplayer for node %s'%self.options.run_node)
                    os.system('DISPLAY=%s vmplayer %s '%(display,file))
                    sys.exit(0)
                else:
                    utils.header ('File not found %s - exiting'%file)
                    sys.exit(1)
            
            utils.header('Saving current myplc url into URL')
            fsave=open('%s/URL'%self.path,"w")
            fsave.write(url)
            fsave.write('\n')
            fsave.close()

            pp = pprint.PrettyPrinter(indent=4,depth=2)
            for plc_spec in TestConfig.plc_specs:
                utils.header('Creating plc with spec')
                pp.pprint(plc_spec)
                test_plc = TestPlc(plc_spec)
                test_plc.connect()
                test_plcs.append(test_plc)
                test_plc.cleanup_plc()
                utils.header('Installing myplc from url %s'%url)
                test_plc.install_plc(url)
                test_plc.config_plc(plc_spec)
                ##create all the sites under the new plc,and then populate them with
                ##nodes,persons and slices(with initscripts)
                for site_spec in plc_spec['sites']:
                    utils.header('Creating site')
                    pp.pprint(site_spec)
                    test_site = test_plc.init_site(site_spec)
                    for node_spec in site_spec['nodes']:
                        utils.header('Creating node')
                        pp.pprint(node_spec)
                        test_nodes.append(node_spec)
                        test_node = test_plc.init_node(test_site,node_spec,self.path)
                test_node.add_initscripts()
                test_node.create_slice ("pi")
                utils.header('Starting vmware nodes')
                test_site.run_vmware(test_nodes,display)
                utils.header('Checking nodes')
                if(test_site.node_check_status(test_nodes,True)):
                    test_plc.db_dump()
                    test_site.slice_access()
                    print "System test successful"
                    return 0
                else :
                    print "System test failed"
                    sys.exit(1)
        except Exception, e:
            print str(e)
            sys.exit(1)
	    
if __name__ == "__main__":
    TestMain().main()
