#!/usr/bin/env python
# $Id$

import os, sys
from optparse import OptionParser
import traceback

import utils
from TestPlc import TestPlc
from TestSite import TestSite
from TestNode import TestNode


default_config = [ 'onelab' ]

default_steps = ['uninstall','install','configure', 'start', 'store_keys',
                 'sites', 'nodes', 'initscripts', 'slices',  
                 'bootcd', 'start_nodes', 
                 'check-nodes', 'check-slices' ]
other_steps = [ 'fresh-install', 'stop', 'clean_sites', 'clean_slices' , 'clean_keys',
                'stop_nodes' ,  'db_dump' , 'db_restore',
                ]

class TestMain:

    subversion_id = "$Id$"

    def __init__ (self):
	self.path=os.path.dirname(sys.argv[0])

    @staticmethod
    def show_env (options, message):
        utils.header (message)
        utils.show_spec("main options",options)

    @staticmethod
    def optparse_list (option, opt, value, parser):
        try:
            setattr(parser.values,option.dest,getattr(parser.values,option.dest)+[value])
        except:
            setattr(parser.values,option.dest,[value])

    def test_main (self):
        usage = """usage: %prog [options] steps
myplc-url defaults to the last value used, as stored in MYPLC-URL
build-url defaults to the last value used, as stored in BUILD-URL
steps refer to a method in TestPlc or to a step-* module"""
        usage += "\n  Defaut steps are %r"%default_steps
        usage += "\n  Other useful steps are %r"%other_steps
        usage += "\n  Default config(s) are %r"%default_config
        parser=OptionParser(usage=usage,version=self.subversion_id)
        parser.add_option("-u","--url",action="store", dest="myplc_url", 
                          help="myplc URL - for locating build output")
        parser.add_option("-b","--build",action="store", dest="build_url", 
                          help="Build URL - for using myplc-init-vserver.sh in native mode")
        parser.add_option("-c","--config",action="callback", callback=TestMain.optparse_list, dest="config",
                          nargs=1,type="string",
                          help="config module - can be set multiple times")
        parser.add_option("-a","--all",action="store_true",dest="all_steps", default=False,
                          help="Runs all default steps")
        parser.add_option("-s","--state",action="store",dest="dbname",default=None,
                           help="Used by db_dump and db_restore")
        parser.add_option("-d","--display", action="store", dest="display", default='bellami.inria.fr:0.0',
                          help="set DISPLAY for vmplayer")
        parser.add_option("-v","--verbose", action="store_true", dest="verbose", default=False, 
                          help="Run in verbose mode")
        parser.add_option("-n","--dry-run", action="store_true", dest="dry_run", default=False,
                          help="Show environment and exits")
        (self.options, self.args) = parser.parse_args()

        if len(self.args) == 0:
            if self.options.all_steps:
                self.options.steps=default_steps
            else:
                parser.print_help()
                sys.exit(1)
        else:
            self.options.steps = self.args

        # display display
        utils.header('X11 display : %s'% self.options.display)

        # handle defaults and option persistence
        for (recname,filename) in ( ('myplc_url','MYPLC-URL') , ('build_url','BUILD-URL') ) :
            if not getattr(self.options,recname):
                try:
                    url_file=open("%s/%s"%(self.path,filename))
                    url=url_file.read().strip()
                    url_file.close()
                    setattr(self.options,recname,url)
                except:
                    print "Cannot determine",recname
                    parser.print_help()
                    sys.exit(1)
            utils.header('* Using %s = %s'%(recname,getattr(self.options,recname)))

            fsave=open('%s/%s'%(self.path,filename),"w")
            fsave.write(getattr(self.options,recname))
            fsave.write('\n')
            fsave.close()
            utils.header('Saved %s into %s'%(recname,filename))

        # config modules
        if not self.options.config:
            # legacy default - do not set in optparse
            self.options.config=default_config
        # step modules
        if not self.options.steps:
            #default (all) steps
            #self.options.steps=['dump','clean','install','populate']
            self.options.steps=default_steps

        # store self.path in options.path for the various callbacks
        self.options.path = self.path

        if self.options.verbose:
            self.show_env(self.options,"Verbose")

        all_plc_specs = []
        for config in self.options.config:
            modulename='config-'+config
            try:
                m = __import__(modulename)
                all_plc_specs = m.config(all_plc_specs,self.options)
            except :
                traceback.print_exc()
                print 'Cannot load config %s -- ignored'%modulename
                raise
        # show config
        utils.show_spec("Test specifications",all_plc_specs)
        # build a TestPlc object from the result
        for spec in all_plc_specs:
            spec['disabled'] = False
        all_plcs = [ (x, TestPlc(x)) for x in all_plc_specs]

        overall_result = True
        testplc_method_dict = __import__("TestPlc").__dict__['TestPlc'].__dict__
        all_step_infos=[]
        for step in self.options.steps:
            # try and locate a method in TestPlc
            if testplc_method_dict.has_key(step):
                all_step_infos += [ (step, testplc_method_dict[step] )]
            # otherwise search for the 'run' method in the step-<x> module
            else:
                modulename='step-'+step
                try:
                    # locate all methods named run* in the module
                    module_dict = __import__(modulename).__dict__
                    names = [ key for key in module_dict.keys() if key.find("run")==0 ]
                    if not names:
                        raise Exception,"No run* method in module %s"%modulename
                    names.sort()
                    all_step_infos += [ ("%s.%s"%(step,name),module_dict[name]) for name in names ]
                except :
                    print 'Step %s -- ignored'%(step)
                    traceback.print_exc()
                    overall_result = False
            
        if self.options.dry_run:
            self.show_env(self.options,"Dry run")
            sys.exit(0)
            
        # do all steps on all plcs
        for (name,method) in all_step_infos:
            for (spec,obj) in all_plcs:
                if not spec['disabled']:
                    try:
                        utils.header("Running step %s on plc %s"%(name,spec['name']))
                        step_result = method(obj,self.options)
                        if step_result:
                            utils.header('Successful step %s on %s'%(name,spec['name']))
                        else:
                            overall_result = False
                            spec['disabled'] = True
                            utils.header('Step %s on %s FAILED - discarding that plc from further steps'%(name,spec['name']))
                    except:
                        overall_result=False
                        spec['disabled'] = True
                        utils.header ('Step %s on plc %s FAILED (exception) - discarding this plc from further steps'%(name,spec['name']))
                        traceback.print_exc()
        return overall_result

    # wrapper to shell
    def main(self):
        try:
            success=self.test_main()
            if success:
                return 0
            else:
                return 1 
        except:
            return 2

if __name__ == "__main__":
    sys.exit(TestMain().main())
