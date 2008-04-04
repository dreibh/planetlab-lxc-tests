#!/usr/bin/env python
# $Id$

import sys, os, os.path
from optparse import OptionParser
import traceback

import utils
from TestPlc import TestPlc
from TestSite import TestSite
from TestNode import TestNode

SEP='<sep>'

class TestMain:

    subversion_id = "$Id$"

    default_config = [ 'main' , '1vnodes' , '1testbox64' ]

    default_steps = ['uninstall','install','install_rpm', 
                     'configure', 'start', SEP,
                     'store_keys', 'initscripts', 
                     'sites', 'nodes', 'slices', 'nodegroups', SEP,
                     'init_node','bootcd', 'configure_qemu', SEP,
                     'kill_all_qemus', 'start_nodes', SEP,
                     'standby_20', SEP,
                     'nodes_booted', 'nodes_ssh', 'check_slices',
                     'check_initscripts', 'check_tcp',SEP,
                     'force_gather_logs', 'force_kill_qemus', ]
    other_steps = [ 'stop_all_vservers','fresh_install', 'cache_rpm', 'stop', SEP,
                    'clean_sites', 'clean_nodes', 'clean_slices', 'clean_keys', SEP,
                    'show_boxes', 'list_all_qemus', 'list_qemus', SEP,
                    'db_dump' , 'db_restore',
                    'standby_1 through 20'
                    ]
    default_build_url = "http://svn.planet-lab.org/svn/build/trunk"

    def __init__ (self):
	self.path=os.path.dirname(sys.argv[0]) or "."
        os.chdir(self.path)

    @staticmethod
    def show_env (options, message):
        utils.header (message)
        utils.show_options("main options",options)

    @staticmethod
    def optparse_list (option, opt, value, parser):
        try:
            setattr(parser.values,option.dest,getattr(parser.values,option.dest)+value.split())
        except:
            setattr(parser.values,option.dest,value.split())

    @staticmethod
    def printable_steps (list):
        return " ".join(list).replace(" "+SEP+" ","\n")

    def run (self):
        steps_message=20*'x'+" Defaut steps are\n"+TestMain.printable_steps(TestMain.default_steps)
        steps_message += "\n"+20*'x'+" Other useful steps are\n"+TestMain.printable_steps(TestMain.other_steps)
        usage = """usage: %%prog [options] steps
myplc-url defaults to the last value used, as stored in arg-myplc-url,
   no default
build-url defaults to the last value used, as stored in arg-build-url, 
   or %s
config defaults to the last value used, as stored in arg-config,
   or %r
ips defaults to the last value used, as stored in arg-ips,
   default is to use IP scanning
steps refer to a method in TestPlc or to a step_* module
===
"""%(TestMain.default_build_url,TestMain.default_config)
        usage += steps_message
        parser=OptionParser(usage=usage,version=self.subversion_id)
        parser.add_option("-u","--url",action="store", dest="myplc_url", 
                          help="myplc URL - for locating build output")
        parser.add_option("-b","--build",action="store", dest="build_url", 
                          help="Build URL - for using vtest-init-vserver.sh in native mode")
        parser.add_option("-c","--config",action="callback", callback=TestMain.optparse_list, dest="config",
                          nargs=1,type="string",
                          help="Config module - can be set multiple times, or use quotes")
        parser.add_option("-x","--exclude",action="callback", callback=TestMain.optparse_list, dest="exclude",
                          nargs=1,type="string",default=[],
                          help="steps to exclude - can be set multiple times, or use quotes")
        parser.add_option("-a","--all",action="store_true",dest="all_steps", default=False,
                          help="Run all default steps")
        parser.add_option("-l","--list",action="store_true",dest="list_steps", default=False,
                          help="List known steps")
        parser.add_option("-i","--ip",action="callback", callback=TestMain.optparse_list, dest="ips",
                          nargs=1,type="string",
                          help="Specify the set of IP addresses to use in vserver mode (disable scanning)")
        parser.add_option("-s","--small",action="store_true",dest="small_test",default=False,
                          help="run a small test -- typically only one node")
        parser.add_option("-d","--dbname",action="store",dest="dbname",default=None,
                           help="Used by db_dump and db_restore")
        parser.add_option("-v","--verbose", action="store_true", dest="verbose", default=False, 
                          help="Run in verbose mode")
        parser.add_option("-q","--quiet", action="store_true", dest="quiet", default=False, 
                          help="Run in quiet mode")
        parser.add_option("-n","--dry-run", action="store_true", dest="dry_run", default=False,
                          help="Show environment and exits")
        parser.add_option("-f","--forcenm", action="store_true", dest="forcenm", default=False, 
                          help="Force the NM to restart in check_slices step")
        (self.options, self.args) = parser.parse_args()

        # tmp : force small test 
        utils.header("XXX WARNING : forcing small tests")
        self.options.small_test = True

        if len(self.args) == 0:
            if self.options.all_steps:
                self.options.steps=TestMain.default_steps
            elif self.options.dry_run:
                self.options.steps=TestMain.default_steps
            elif self.options.list_steps:
                print steps_message
                sys.exit(1)
            else:
                print 'No step found (do you mean -a ? )'
                print "Run %s --help for help"%sys.argv[0]                        
                sys.exit(1)
        else:
            self.options.steps = self.args

        # handle defaults and option persistence
        for (recname,filename,default) in (
            ('build_url','arg-build-url',TestMain.default_build_url) ,
            ('ips','arg-ips',[]) , 
            ('config','arg-config',TestMain.default_config) , 
            ('myplc_url','arg-myplc-url',"") , 
            ) :
#            print 'handling',recname
            path=filename
            is_list = isinstance(default,list)
            if not getattr(self.options,recname):
                try:
                    parsed=file(path).readlines()
                    if not is_list:    # strings
                        if len(parsed) != 1:
                            print "%s - error when parsing %s"%(sys.argv[1],path)
                            sys.exit(1)
                        parsed=parsed[0].strip()
                    else:              # lists
                        parsed=[x.strip() for x in parsed]
                    setattr(self.options,recname,parsed)
                except:
                    if default != "":
                        setattr(self.options,recname,default)
                    else:
                        print "Cannot determine",recname
                        print "Run %s --help for help"%sys.argv[0]                        
                        sys.exit(1)
            if not self.options.quiet:
                utils.header('* Using %s = %s'%(recname,getattr(self.options,recname)))

            # save for next run
            fsave=open(path,"w")
            if not is_list:
                fsave.write(getattr(self.options,recname) + "\n")
            else:
                for value in getattr(self.options,recname):
                    fsave.write(value + "\n")
            fsave.close()
#            utils.header('Saved %s into %s'%(recname,filename))

        # steps
        if not self.options.steps:
            #default (all) steps
            #self.options.steps=['dump','clean','install','populate']
            self.options.steps=TestMain.default_steps

        # exclude
        selected=[]
        for step in self.options.steps:
            keep=True
            for exclude in self.options.exclude:
                if utils.match(step,exclude):
                    keep=False
                    break
            if keep: selected.append(step)
        self.options.steps=selected

        # this is useful when propagating on host boxes, to avoid conflicts
        self.options.buildname = os.path.basename (os.path.abspath (self.path))

        if self.options.verbose:
            self.show_env(self.options,"Verbose")

        # load configs
        all_plc_specs = []
        for config in self.options.config:
            modulename='config_'+config
            try:
                m = __import__(modulename)
                all_plc_specs = m.config(all_plc_specs,self.options)
            except :
                traceback.print_exc()
                print 'Cannot load config %s -- ignored'%modulename
                raise
        # show config
        if not self.options.quiet:
            utils.show_test_spec("Test specifications",all_plc_specs)
        # build a TestPlc object from the result, passing options
        for spec in all_plc_specs:
            spec['disabled'] = False
        all_plcs = [ (x, TestPlc(x,self.options)) for x in all_plc_specs]

        # pass options to utils as well
        utils.init_options(self.options)

        overall_result = True
        testplc_method_dict = __import__("TestPlc").__dict__['TestPlc'].__dict__
        all_step_infos=[]
        for step in self.options.steps:
            if step == SEP:
                continue
            force=False
            # is it a forcedstep
            if step.find("force_") == 0:
                step=step.replace("force_","")
                force=True
            # try and locate a method in TestPlc
            if testplc_method_dict.has_key(step):
                all_step_infos += [ (step, testplc_method_dict[step] , force)]
            # otherwise search for the 'run' method in the step_<x> module
            else:
                modulename='step_'+step
                try:
                    # locate all methods named run* in the module
                    module_dict = __import__(modulename).__dict__
                    names = [ key for key in module_dict.keys() if key.find("run")==0 ]
                    if not names:
                        raise Exception,"No run* method in module %s"%modulename
                    names.sort()
                    all_step_infos += [ ("%s.%s"%(step,name),module_dict[name],force) for name in names ]
                except :
                    print 'Step %s -- ignored'%(step)
                    traceback.print_exc()
                    overall_result = False
            
        if self.options.dry_run:
            self.show_env(self.options,"Dry run")
            
        # do all steps on all plcs
        for (stepname,method,force) in all_step_infos:
            for (spec,obj) in all_plcs:
                plcname=spec['name']

                # run the step
                if not spec['disabled'] or force:
                    try:
                        force_msg=""
                        if force: force_msg=" (forced)"
                        utils.header("********** RUNNING step %s%s on plc %s"%(stepname,force_msg,plcname))
                        step_result = method(obj)
                        if step_result:
                            utils.header('********** SUCCESSFUL step %s on %s'%(stepname,plcname))
                        else:
                            overall_result = False
                            spec['disabled'] = True
                            utils.header('********** FAILED Step %s on %s - discarding that plc from further steps'%(stepname,plcname))
                    except:
                        overall_result=False
                        spec['disabled'] = True
                        traceback.print_exc()
                        utils.header ('********** FAILED (exception) Step %s on plc %s - discarding this plc from further steps'%(stepname,plcname))

                # do not run, just display it's skipped
                else:
                    utils.header("********** IGNORED Plc %s is disabled - skipping step %s"%(plcname,stepname))

        return overall_result

    # wrapper to run, returns a shell-compatible result
    def main(self):
        try:
            success=self.run()
            if success:
                return 0
            else:
                return 1 
        except SystemExit:
            raise
        except:
            traceback.print_exc()
            return 2

if __name__ == "__main__":
    sys.exit(TestMain().main())
