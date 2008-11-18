#!/usr/bin/env python
# $Id$

import sys, os, os.path
from optparse import OptionParser
import traceback
from time import strftime
import readline

import utils
from TestPlc import TestPlc
from TestSite import TestSite
from TestNode import TestNode

class TestMain:

    subversion_id = "$Id$"

    default_config = [ 'default' ] 

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

    def run (self):
        steps_message=20*'x'+" Defaut steps are\n"+TestPlc.printable_steps(TestPlc.default_steps)
        steps_message += "\n"+20*'x'+" Other useful steps are\n"+TestPlc.printable_steps(TestPlc.other_steps)
        usage = """usage: %%prog [options] steps
arch-rpms-url defaults to the last value used, as stored in arg-arch-rpms-url,
   no default
build-url defaults to the last value used, as stored in arg-build-url, 
   or %s
config defaults to the last value used, as stored in arg-config,
   or %r
node-ips and plc-ips defaults to the last value used, as stored in arg-ips-node and arg-ips-plc,
   default is to use IP scanning
steps refer to a method in TestPlc or to a step_* module
===
"""%(TestMain.default_build_url,TestMain.default_config)
        usage += steps_message
        parser=OptionParser(usage=usage,version=self.subversion_id)
        parser.add_option("-u","--url",action="store", dest="arch_rpms_url", 
                          help="URL of the arch-dependent RPMS area - for locating what to test")
        parser.add_option("-b","--build",action="store", dest="build_url", 
                          help="Build URL - for locating vtest-init-vserver.sh")
        parser.add_option("-c","--config",action="callback", callback=TestMain.optparse_list, dest="config",
                          nargs=1,type="string",
                          help="Config module - can be set multiple times, or use quotes")
        parser.add_option("-p","--personality",action="store", dest="personality", 
                          help="personality - as in vbuild-nightly")
        parser.add_option("-d","--pldistro",action="store", dest="pldistro", 
                          help="pldistro - as in vbuild-nightly")
        parser.add_option("-f","--fcdistro",action="store", dest="fcdistro", 
                          help="fcdistro - as in vbuild-nightly")
        parser.add_option("-x","--exclude",action="callback", callback=TestMain.optparse_list, dest="exclude",
                          nargs=1,type="string",default=[],
                          help="steps to exclude - can be set multiple times, or use quotes")
        parser.add_option("-a","--all",action="store_true",dest="all_steps", default=False,
                          help="Run all default steps")
        parser.add_option("-l","--list",action="store_true",dest="list_steps", default=False,
                          help="List known steps")
        parser.add_option("-N","--nodes",action="callback", callback=TestMain.optparse_list, dest="ips_node",
                          nargs=1,type="string",
                          help="Specify the set of IP addresses to use for nodes (scanning disabled)")
        parser.add_option("-P","--plcs",action="callback", callback=TestMain.optparse_list, dest="ips_plc",
                          nargs=1,type="string",
                          help="Specify the set of IP addresses to use for plcs (scanning disabled)")
        parser.add_option("-1","--small",action="store_true",dest="small_test",default=False,
                          help="run a small test -- typically only one node")
        parser.add_option("-D","--dbname",action="store",dest="dbname",default=None,
                           help="Used by db_dump and db_restore")
        parser.add_option("-v","--verbose", action="store_true", dest="verbose", default=False, 
                          help="Run in verbose mode")
        parser.add_option("-q","--quiet", action="store_true", dest="quiet", default=False, 
                          help="Run in quiet mode")
        parser.add_option("-i","--interactive",action="store_true",dest="interactive",default=False,
                          help="prompts before each step")
        parser.add_option("-n","--dry-run", action="store_true", dest="dry_run", default=False,
                          help="Show environment and exits")
        parser.add_option("-r","--restart-nm", action="store_true", dest="forcenm", default=False, 
                          help="Force the NM to restart in check_slices step")
        parser.add_option("-t","--trace", action="store", dest="trace_file", default=None,
                          #default="logs/trace-@TIME@.txt",
                          help="Trace file location")
        (self.options, self.args) = parser.parse_args()

        if len(self.args) == 0:
            if self.options.all_steps:
                self.options.steps=TestPlc.default_steps
            elif self.options.dry_run:
                self.options.steps=TestPlc.default_steps
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
            ('ips_node','arg-ips-node',[]) , 
            ('ips_plc','arg-ips-plc',[]) , 
            ('config','arg-config',TestMain.default_config) , 
            ('arch_rpms_url','arg-arch-rpms-url',"") , 
            ('personality','arg-personality',"linux32"),
            ('pldistro','arg-pldistro',"planetlab"),
            ('fcdistro','arg-fcdistro','f8'),
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

        if self.options.personality == "linux32":
            self.options.arch = "i386"
        elif self.options.personality == "linux64":
            self.options.arch = "x86_64"
        else:
            raise Exception, "Unsupported personality %r"%self.options.personality
        # steps
        if not self.options.steps:
            #default (all) steps
            #self.options.steps=['dump','clean','install','populate']
            self.options.steps=TestPlc.default_steps

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
        # remember plc IP address(es) if not specified
        current=file('arg-ips-plc').read()
        if not current:
            ips_plc_file=open('arg-ips-plc','w')
            for plc_spec in all_plc_specs:
                ips_plc_file.write("%s\n"%plc_spec['PLC_API_HOST'])
            ips_plc_file.close()
        # ditto for nodes
        current=file('arg-ips-node').read()
        if not current:
            ips_node_file=open('arg-ips-node','w')
            for plc_spec in all_plc_specs:
                for site_spec in plc_spec['sites']:
                    for node_spec in site_spec['nodes']:
                        ips_node_file.write("%s\n"%node_spec['node_fields']['hostname'])
            ips_node_file.close()
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
            if not TestPlc.valid_step(step):
                continue
            force=False
            # is it a forced step
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
                    print '********** step %s NOT FOUND -- ignored'%(step)
                    traceback.print_exc()
                    overall_result = False
            
        if self.options.dry_run:
            self.show_env(self.options,"Dry run")
        
        # init & open trace file if provided
        if self.options.trace_file and not self.options.dry_run:
            time=strftime("%H-%M")
            date=strftime("%Y-%m-%d")
            trace_file=self.options.trace_file
            trace_file=trace_file.replace("@TIME@",time)
            trace_file=trace_file.replace("@DATE@",date)
            self.options.trace_file=trace_file
            # create dir if needed
            trace_dir=os.path.dirname(trace_file)
            if trace_dir and not os.path.isdir(trace_dir):
                os.makedirs(trace_dir)
            trace=open(trace_file,"w")

        # do all steps on all plcs
        TRACE_FORMAT="TRACE: time=%(time)s plc=%(plcname)s step=%(stepname)s status=%(status)s force=%(force)s\n"
        for (stepname,method,force) in all_step_infos:
            for (spec,obj) in all_plcs:
                plcname=spec['name']

                # run the step
                time=strftime("%Y-%m-%d-%H-%M")
                if not spec['disabled'] or force or self.options.interactive:
                    skip_step=False
                    if self.options.interactive:
                        prompting=True
                        while prompting:
                            msg="Run step %s on %s [r](un)/d(ry_run)/s(kip)/q(uit) ? "%(stepname,plcname)
                            answer=raw_input(msg).strip().lower() or "r"
                            answer=answer[0]
                            if answer in ['s','n']:     # skip/no/next
                                print '%s on %s skipped'%(stepname,plcname)
                                prompting=False
                                skip_step=True
                            elif answer in ['q','b']:   # quit/bye
                                print 'Exiting'
                                return
                            elif answer in ['d']:       # dry_run
                                dry_run=self.options.dry_run
                                self.options.dry_run=True
                                obj.options.dry_run=True
                                obj.apiserver.set_dry_run(True)
                                step_result=method(obj)
                                print 'dry_run step ->',step_result
                                self.options.dry_run=dry_run
                                obj.options.dry_run=dry_run
                                obj.apiserver.set_dry_run(dry_run)
                            elif answer in ['r','y']:   # run/yes
                                prompting=False
                    if skip_step:
                        continue
                    try:
                        force_msg=""
                        if force: force_msg=" (forced)"
                        utils.header("********** RUNNING step %s%s on plc %s"%(stepname,force_msg,plcname))
                        step_result = method(obj)
                        if step_result:
                            utils.header('********** SUCCESSFUL step %s on %s'%(stepname,plcname))
                            status="OK"
                        else:
                            overall_result = False
                            spec['disabled'] = True
                            utils.header('********** FAILED Step %s on %s - discarding that plc from further steps'%(stepname,plcname))
                            status="KO"
                    except:
                        overall_result=False
                        spec['disabled'] = True
                        traceback.print_exc()
                        utils.header ('********** FAILED (exception) Step %s on plc %s - discarding this plc from further steps'%(stepname,plcname))
                        status="KO"

                # do not run, just display it's skipped
                else:
                    utils.header("********** IGNORED Plc %s is disabled - skipping step %s"%(plcname,stepname))
                    status="UNDEF"
                if not self.options.dry_run:
                    # alwas do this on stdout
                    print TRACE_FORMAT%locals()
                    # duplicate on trace_file if provided
                    if self.options.trace_file:
                        trace.write(TRACE_FORMAT%locals())

        if self.options.trace_file and not self.options.dry_run:
            trace.close()

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
