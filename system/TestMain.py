#!/usr/bin/env python

import os, sys, time
from optparse import OptionParser
from TestPlc import TestPlc
from TestSite import TestSite
from TestNode import TestNode
import TestConfig
import threading

class TestMain:

    subversion_id = "$Id$"

    def __init__ (self):
	self.path=os.path.dirname(sys.argv[0])

    def main (self):
        try:
            usage = """usage: %prog [options] MyplcURL"""
            parser=OptionParser(usage=usage,version=self.subversion_id)
            # verbosity
            parser.add_option("-v","--verbose", action="store_true", dest="verbose", default=False, 
                              help="Run in verbose mode")
            # debug mode
            parser.add_option("-g","--debug", action="store", dest="debug", 
                              help="Run in debug mode for eventual virtual problems")
            #exporting Display
            parser.add_option("-d","--display", action="store", dest="Xterm", default='bellami:0.0',
                              help="export the display on the mentionneted one")
        
            (self.options, self.args) = parser.parse_args()

            display=''
            url=''
            test_plcs=[]
            test_nodes=[]
            pids=[]
            timset=time.strftime("%H:%M:%S", time.localtime())
            #test the existence of the URL
            if (len (self.args)):
                url=self.args[0]
                print 'the myplc url is ',url
            else:
                print "PLease introduce a right URL for the myplc instal"
                sys.exit(1)
            #check where to display Virtual machines
            if (self.options.Xterm):
                display=self.options.Xterm
                print 'the display is', display
            #the debug option 
            if (self.options.debug):
                file=self.path+'/'+self.options.debug+'/My_Virtual_Machine.vmx'
                if os.path.exists(file):
                    print 'vmx file is',file
                    arg='< /dev/null &>/dev/null &'
                    os.system('DISPLAY=%s vmplayer %s %s '%(display,file,arg))
                    sys.exit(0)
                else:
                    print "no way to find the virtual file"
                    sys.exit(1)
            
            for plc_spec in TestConfig.plc_specs:
                print '========>Creating plc at '+timset+':',plc_spec
                test_plc = TestPlc(plc_spec)
                test_plc.connect()
                test_plcs.append(test_plc)
                test_plc.cleanup_plc()
                print '========>Installing myplc at: ', timset
                if (len(sys.argv) > 1):
                    test_plc.install_plc(url)
                    test_plc.config_plc(plc_spec)
                else :
                    print "========>PLease insert a valid url for the myplc install"
                ##create all the sites under the new plc,and then populate them with
                ##nodes,persons and slices
                for site_spec in plc_spec['sites']:
                    print '========>Creating site at '+timset+ ':',site_spec
                    test_site = test_plc.init_site(site_spec)
                    for node_spec in site_spec['nodes']:
                        print '========>Creating node at  '+ timset+' :',node_spec
                        test_nodes.append(node_spec)
                        test_node = test_plc.init_node(test_site,node_spec,self.path)
                test_node.create_slice ("pi")
                print 'Runing Checkers and Vmwares for Site nodes at :',timset
                test_site.run_vmware(test_nodes,display)
                if(test_site.node_check_status(test_nodes,True)):
                    test_plc.db_dump()
                    test_site.slice_access(test_nodes)
                    print "all is alright"
                    return 0
                else :
                    print "There is something wrong"
                    sys.exit(1)
        except Exception, e:
            print str(e)
            sys.exit(1)
	    
if __name__ == "__main__":
    TestMain().main()
