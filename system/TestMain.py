#!/usr/bin/python -u

# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import sys, os, os.path
from optparse import OptionParser
import traceback
from time import strftime
import readline

import utils
from TestPlc import TestPlc
from TestSite import TestSite
from TestNode import TestNode

# add $HOME in PYTHONPATH so we can import LocalTestResources.py
sys.path.append(os.environ['HOME'])
import LocalTestResources

class TestMain:

    subversion_id = "Now using git -- version tracker broken"

    default_config = [ 'default' ] 

    default_build_url = "git://git.onelab.eu/tests"

    def __init__ (self):
	self.path=os.path.dirname(sys.argv[0]) or "."
        os.chdir(self.path)

    def show_env (self,options, message):
        if self.options.verbose:
            utils.header (message)
            utils.show_options("main options",options)

    def init_steps(self):
        self.steps_message  = 20*'x'+" Defaut steps are\n"+TestPlc.printable_steps(TestPlc.default_steps)
        self.steps_message += 20*'x'+" Other useful steps are\n"+TestPlc.printable_steps(TestPlc.other_steps)

    def list_steps(self):
        if not self.options.verbose:
            print self.steps_message,
        else:
            testplc_method_dict = __import__("TestPlc").__dict__['TestPlc'].__dict__
            scopes = [("Default steps",TestPlc.default_steps)]
            if self.options.all_steps:
                scopes.append ( ("Other steps",TestPlc.other_steps) )
            for (scope,steps) in scopes:
                print '--------------------',scope
                for step in [step for step in steps if TestPlc.valid_step(step)]:
                    stepname=step
                    if step.find("force_") == 0:
                        stepname=step.replace("force_","")
                        force=True
                    print '*',step,"\r",4*"\t",
                    try:
                        print testplc_method_dict[stepname].__doc__
                    except:
                        print "*** no doc found"

    def run (self):
        self.init_steps()
        usage = """usage: %%prog [options] steps
arch-rpms-url defaults to the last value used, as stored in arg-arch-rpms-url,
   no default
config defaults to the last value used, as stored in arg-config,
   or %r
ips_node, ips_plc and ips_qemu defaults to the last value used, as stored in arg-ips-{node,plc,qemu},
   default is to use IP scanning
steps refer to a method in TestPlc or to a step_* module
===
"""%(TestMain.default_config)
        usage += self.steps_message
        parser=OptionParser(usage=usage,version=self.subversion_id)
        parser.add_option("-u","--url",action="store", dest="arch_rpms_url", 
                          help="URL of the arch-dependent RPMS area - for locating what to test")
        parser.add_option("-b","--build",action="store", dest="build_url", 
                          help="ignored, for legacy only")
        parser.add_option("-c","--config",action="append", dest="config", default=[],
                          help="Config module - can be set multiple times, or use quotes")
        parser.add_option("-p","--personality",action="store", dest="personality", 
                          help="personality - as in vbuild-nightly")
        parser.add_option("-d","--pldistro",action="store", dest="pldistro", 
                          help="pldistro - as in vbuild-nightly")
        parser.add_option("-f","--fcdistro",action="store", dest="fcdistro", 
                          help="fcdistro - as in vbuild-nightly")
        parser.add_option("-x","--exclude",action="append", dest="exclude", default=[],
                          help="steps to exclude - can be set multiple times, or use quotes")
        parser.add_option("-a","--all",action="store_true",dest="all_steps", default=False,
                          help="Run all default steps")
        parser.add_option("-l","--list",action="store_true",dest="list_steps", default=False,
                          help="List known steps")
        parser.add_option("-N","--nodes",action="append", dest="ips_node", default=[],
                          help="Specify the set of hostname/IP's to use for nodes")
        parser.add_option("-P","--plcs",action="append", dest="ips_plc", default=[],
                          help="Specify the set of hostname/IP's to use for plcs")
        parser.add_option("-Q","--qemus",action="append", dest="ips_qemu", default=[],
                          help="Specify the set of hostname/IP's to use for qemu boxes")
        parser.add_option("-s","--size",action="store",type="int",dest="size",default=1,
                          help="sets test size in # of plcs - default is 1")
        parser.add_option("-q","--qualifier",action="store",type="int",dest="qualifier",default=None,
                          help="run steps only on plc numbered <qualifier>, starting at 1")
        parser.add_option("-k","--keep-going",action="store",dest="keep_going",default=False,
                          help="proceeds even if some steps are failing")
        parser.add_option("-D","--dbname",action="store",dest="dbname",default=None,
                           help="Used by db_dump and db_restore")
        parser.add_option("-v","--verbose", action="store_true", dest="verbose", default=False, 
                          help="Run in verbose mode")
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

        # allow things like "run -c 'c1 c2' -c c3"
        def flatten (x):
            result = []
            for el in x:
                if hasattr(el, "__iter__") and not isinstance(el, basestring):
                    result.extend(flatten(el))
                else:
                    result.append(el)
            return result
        # flatten relevant options
        for optname in ['config','exclude','ips_node','ips_plc','ips_qemu']:
            setattr(self.options,optname, flatten ( [ arg.split() for arg in getattr(self.options,optname) ] ))

        # handle defaults and option persistence
        for (recname,filename,default) in (
            ('build_url','arg-build-url',TestMain.default_build_url) ,
            ('ips_node','arg-ips-node',[]) , 
            ('ips_plc','arg-ips-plc',[]) , 
            ('ips_qemu','arg-ips-qemu',[]) , 
            ('config','arg-config',TestMain.default_config) , 
            ('arch_rpms_url','arg-arch-rpms-url',"") , 
            ('personality','arg-personality',"linux32"),
            ('pldistro','arg-pldistro',"planetlab"),
            ('fcdistro','arg-fcdistro','centos5'),
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

            # save for next run
            fsave=open(path,"w")
            if not is_list:
                fsave.write(getattr(self.options,recname) + "\n")
            else:
                for value in getattr(self.options,recname):
                    fsave.write(value + "\n")
            fsave.close()
#            utils.header('Saved %s into %s'%(recname,filename))

            # lists need be reversed
            if isinstance(getattr(self.options,recname),list):
                getattr(self.options,recname).reverse()

            if self.options.verbose:
                utils.header('* Using %s = %s'%(recname,getattr(self.options,recname)))

        # hack : if sfa is not among the published rpms, skip these tests
        TestPlc.check_whether_build_has_sfa(self.options.arch_rpms_url)

        # no step specified
        if len(self.args) == 0:
            self.options.steps=TestPlc.default_steps
        else:
            self.options.steps = self.args

        if self.options.list_steps:
            self.init_steps()
            self.list_steps()
            return True

        # steps
        if not self.options.steps:
            #default (all) steps
            #self.options.steps=['dump','clean','install','populate']
            self.options.steps=TestPlc.default_steps

        # rewrite '-' into '_' in step names
        self.options.steps = [ step.replace('-','_') for step in self.options.steps ]

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

        # run localize as defined by local_resources
        all_plc_specs = LocalTestResources.local_resources.localize(all_plc_specs,self.options)

        # remember plc IP address(es) if not specified
        ips_plc_file=open('arg-ips-plc','w')
        for plc_spec in all_plc_specs:
            ips_plc_file.write("%s\n"%plc_spec['PLC_API_HOST'])
        ips_plc_file.close()
        # ditto for nodes
        ips_node_file=open('arg-ips-node','w')
        for plc_spec in all_plc_specs:
            for site_spec in plc_spec['sites']:
                for node_spec in site_spec['nodes']:
                    ips_node_file.write("%s\n"%node_spec['node_fields']['hostname'])
        ips_node_file.close()
        # ditto for qemu boxes
        ips_qemu_file=open('arg-ips-qemu','w')
        for plc_spec in all_plc_specs:
            for site_spec in plc_spec['sites']:
                for node_spec in site_spec['nodes']:
                    ips_qemu_file.write("%s\n"%node_spec['host_box'])
        ips_qemu_file.close()
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
            # some steps need to be done regardless of the previous ones: we force them
            force=False
            if step.find("force_") == 0:
                step=step.replace("force_","")
                force=True
            # a cross step will run a method on TestPlc that has a signature like
            # def cross_foo (self, all_test_plcs)
            cross=False
            if step.find("cross_") == 0:
                cross=True
            # allow for steps to specify an index like in 
            # run checkslice@2
            try:        (step,qualifier)=step.split('@')
            except:     qualifier=self.options.qualifier

            # try and locate a method in TestPlc
            if testplc_method_dict.has_key(step):
                all_step_infos += [ (step, testplc_method_dict[step] , force, cross, qualifier)]
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
                    all_step_infos += [ ("%s.%s"%(step,name),module_dict[name],force,cross,qualifier) for name in names ]
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
        TIME_FORMAT="%H-%M-%S"
        TRACE_FORMAT="TRACE: beg=%(beg)s end=%(end)s status=%(status)s step=%(stepname)s plc=%(plcname)s force=%(force)s\n"
        for (stepname,method,force,cross,qualifier) in all_step_infos:
            plc_counter=0
            for (spec,plc_obj) in all_plcs:
                plc_counter+=1
                # skip this step if we have specified a plc_explicit
                if qualifier and plc_counter!=int(qualifier): continue

                plcname=spec['name']
                across_plcs = [ o for (s,o) in all_plcs if o!=plc_obj ]

                # run the step
                beg=strftime(TIME_FORMAT)
                if not spec['disabled'] or force or self.options.interactive or self.options.keep_going:
                    skip_step=False
                    if self.options.interactive:
                        prompting=True
                        while prompting:
                            msg="%d Run step %s on %s [r](un)/d(ry_run)/s(kip)/q(uit) ? "%(plc_counter,stepname,plcname)
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
                                plc_obj.options.dry_run=True
                                plc_obj.apiserver.set_dry_run(True)
                                if not cross:   step_result=method(plc_obj)
                                else:           step_result=method(plc_obj,across_plcs)
                                print 'dry_run step ->',step_result
                                self.options.dry_run=dry_run
                                plc_obj.options.dry_run=dry_run
                                plc_obj.apiserver.set_dry_run(dry_run)
                            elif answer in ['r','y']:   # run/yes
                                prompting=False
                    if skip_step:
                        continue
                    try:
                        force_msg=""
                        if force: force_msg=" (forced)"
                        utils.header("********** %d RUNNING step %s%s on plc %s"%(plc_counter,stepname,force_msg,plcname))
                        if not cross:   step_result = method(plc_obj)
                        else:           step_result = method(plc_obj,across_plcs)
                        if step_result:
                            utils.header('********** %d SUCCESSFUL step %s on %s'%(plc_counter,stepname,plcname))
                            status="OK"
                        else:
                            overall_result = False
                            spec['disabled'] = True
                            utils.header('********** %d FAILED Step %s on %s (discarded from further steps)'\
                                             %(plc_counter,stepname,plcname))
                            status="KO"
                    except:
                        overall_result=False
                        spec['disabled'] = True
                        traceback.print_exc()
                        utils.header ('********** %d FAILED (exception) Step %s on %s (discarded from further steps)'\
                                          %(plc_counter,stepname,plcname))
                        status="KO"

                # do not run, just display it's skipped
                else:
                    utils.header("********** %d IGNORED Plc %s is disabled - skipping step %s"%(plc_counter,plcname,stepname))
                    status="UNDEF"
                if not self.options.dry_run:
                    end=strftime(TIME_FORMAT)
                    # always do this on stdout
                    print TRACE_FORMAT%locals()
                    # duplicate on trace_file if provided
                    if self.options.trace_file:
                        trace.write(TRACE_FORMAT%locals())
                        trace.flush()

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
            print 'Caught SystemExit'
            raise
        except:
            traceback.print_exc()
            return 2

if __name__ == "__main__":
    sys.exit(TestMain().main())
