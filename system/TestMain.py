#!/usr/bin/python -u

# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2010 INRIA 
#
import sys, os, os.path
from optparse import OptionParser
import traceback
import readline
import glob
from datetime import datetime

import utils
from TestPlc import TestPlc, Ignored
from TestSite import TestSite
from TestNode import TestNode
from macros import sequences

# add $HOME in PYTHONPATH so we can import LocalSubstrate.py
sys.path.append(os.environ['HOME'])
import LocalSubstrate

class Step:

    natives=TestPlc.__dict__

    def display (self): return self.name.replace('_','-')
    def internal (self): return self.name.replace('-','_')

    def __init__ (self, name):
        self.name=name
        # a native step is implemented as a method on TestPlc
        self.native = self.internal() in Step.natives
        if self.native:
            self.method=Step.natives[self.internal()]
        else:
            try:
                self.substeps=sequences[self.internal()]
            except Exception,e:
                print "macro step %s not found in macros.py (%s) - exiting"%(self.display(),e)
                raise

    def print_doc (self,level=0):
        tab=32
        trail=8
        if self.native:
            start=level*' '+'* '
            # 2 is the len of '* '
            width=tab-level-2
            format="%%-%ds"%width
            line=start+format%self.display()
            print line,
            try:
                print self.method.__doc__
            except:
                print "*** no doc found"
        else:
            beg_start=level*' '+'>>> '
            end_start=level*' '+'<<< '
            trailer=trail*'-'
            # 4 is the len of '>>> '
            width=tab-level-4-trail
            format=("%%-%ds"%width)
            beg_line=beg_start+format%self.display()+trail*'>'
            end_line=end_start+format%self.display()+trail*'<'
            print beg_line
            for step in self.substeps:
                Step(step).print_doc(level+1)
            print end_line

    # return a list of (name, method) for all native steps involved
    def tuples (self):
        if self.native: return [ (self.internal(), self.method,) ]
        else:
            result=[]
            for substep in [ Step(name) for name in self.substeps ] : 
                result += substep.tuples()
            return result

    # convenience for listing macros
    # just do a listdir, hoping we're in the right directory...
    @staticmethod
    def list_macros ():
        names= sequences.keys()
        names.sort()
        return names

class TestMain:

    subversion_id = "Now using git -- version tracker broken"

    default_config = [ 'default' ] 
#    default_rspec_styles = [ 'pl', 'pg' ]
    default_rspec_styles = [ 'pg' ]

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
        self.steps_message += 20*'x'+" Macro steps are\n"+" ".join(Step.list_macros())

    def list_steps(self):
        if not self.options.verbose:
            print self.steps_message,
        else:
            # steps mentioned on the command line
            if self.options.args:
                scopes = [("Argument steps",self.options.args)]
            else:
                scopes = [("Default steps",TestPlc.default_steps)]
                if self.options.all_steps:
                    scopes.append ( ("Other steps",TestPlc.other_steps) )
                    # try to list macro steps as well
                    scopes.append ( ("Macro steps", Step.list_macros()) )
            for (scope,steps) in scopes:
                print '--------------------',scope
                for step in [step for step in steps if TestPlc.valid_step(step)]:
                    try:        (step,qualifier)=step.split('@')
                    except:     pass
                    stepname=step
                    for special in ['force','ignore']:
                        stepname = stepname.replace('_'+special,"")
                    Step(stepname).print_doc()

    def run (self):
        self.init_steps()
        usage = """usage: %%prog [options] steps
arch-rpms-url defaults to the last value used, as stored in arg-arch-rpms-url,
   no default
config defaults to the last value used, as stored in arg-config,
   or %r
ips_vnode, ips_vplc and ips_qemu defaults to the last value used, as stored in arg-ips-{bplc,vplc,bnode,vnode},
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
        parser.add_option("-e","--exclude",action="append", dest="exclude", default=[],
                          help="steps to exclude - can be set multiple times, or use quotes")
        parser.add_option("-i","--ignore",action="append", dest="ignore", default=[],
                          help="steps to run but ignore - can be set multiple times, or use quotes")
        parser.add_option("-a","--all",action="store_true",dest="all_steps", default=False,
                          help="Run all default steps")
        parser.add_option("-l","--list",action="store_true",dest="list_steps", default=False,
                          help="List known steps")
        parser.add_option("-V","--vserver",action="append", dest="ips_bplc", default=[],
                          help="Specify the set of hostnames for the boxes that host the plcs")
        parser.add_option("-P","--plcs",action="append", dest="ips_vplc", default=[],
                          help="Specify the set of hostname/IP's to use for vplcs")
        parser.add_option("-Q","--qemus",action="append", dest="ips_bnode", default=[],
                          help="Specify the set of hostnames for the boxes that host the nodes")
        parser.add_option("-N","--nodes",action="append", dest="ips_vnode", default=[],
                          help="Specify the set of hostname/IP's to use for vnodes")
        parser.add_option("-s","--size",action="store",type="int",dest="size",default=1,
                          help="sets test size in # of plcs - default is 1")
        parser.add_option("-q","--qualifier",action="store",type="int",dest="qualifier",default=None,
                          help="run steps only on plc numbered <qualifier>, starting at 1")
        parser.add_option("-y","--rspec-style",action="append",dest="rspec_styles",default=[],
                          help="pl is for planetlab rspecs, pg is for protogeni")
        parser.add_option("-k","--keep-going",action="store",dest="keep_going",default=False,
                          help="proceeds even if some steps are failing")
        parser.add_option("-D","--dbname",action="store",dest="dbname",default=None,
                           help="Used by plc_db_dump and plc_db_restore")
        parser.add_option("-v","--verbose", action="store_true", dest="verbose", default=False, 
                          help="Run in verbose mode")
        parser.add_option("-I","--interactive",action="store_true",dest="interactive",default=False,
                          help="prompts before each step")
        parser.add_option("-n","--dry-run", action="store_true", dest="dry_run", default=False,
                          help="Show environment and exits")
        parser.add_option("-t","--trace", action="store", dest="trace_file", default=None,
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
        for optname in ['config','exclude','ignore','ips_bplc','ips_vplc','ips_bnode','ips_vnode']:
            setattr(self.options,optname, flatten ( [ arg.split() for arg in getattr(self.options,optname) ] ))

        if not self.options.rspec_styles:
            self.options.rspec_styles=TestMain.default_rspec_styles

        # handle defaults and option persistence
        for (recname,filename,default,need_reverse) in (
            ('build_url','arg-build-url',TestMain.default_build_url,None) ,
            ('ips_bplc','arg-ips-bplc',[],True),
            ('ips_vplc','arg-ips-vplc',[],True) , 
            ('ips_bnode','arg-ips-bnode',[],True),
            ('ips_vnode','arg-ips-vnode',[],True) , 
            ('config','arg-config',TestMain.default_config,False) , 
            ('arch_rpms_url','arg-arch-rpms-url',"",None) , 
            ('personality','arg-personality',"linux64",None),
            ('pldistro','arg-pldistro',"onelab",None),
            ('fcdistro','arg-fcdistro','f14',None),
            ) :
#            print 'handling',recname
            path=filename
            is_list = isinstance(default,list)
            is_bool = isinstance(default,bool)
            if not getattr(self.options,recname):
                try:
                    parsed=file(path).readlines()
                    if is_list:         # lists
                        parsed=[x.strip() for x in parsed]
                    else:               # strings and booleans
                        if len(parsed) != 1:
                            print "%s - error when parsing %s"%(sys.argv[1],path)
                            sys.exit(1)
                        parsed=parsed[0].strip()
                        if is_bool:
                            parsed = parsed.lower()=='true'
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
            if is_list:                 # lists
                for value in getattr(self.options,recname):
                    fsave.write(value + "\n")
            else:                       # strings and booleans - just call str()
                fsave.write(str(getattr(self.options,recname)) + "\n")
            fsave.close()
#            utils.header('Saved %s into %s'%(recname,filename))

            # lists need be reversed
            # I suspect this is useful for the various pools but for config, it's painful
            if isinstance(getattr(self.options,recname),list) and need_reverse:
                getattr(self.options,recname).reverse()

            if self.options.verbose:
                utils.header('* Using %s = %s'%(recname,getattr(self.options,recname)))

        # hack : if sfa is not among the published rpms, skip these tests
        TestPlc.check_whether_build_has_sfa(self.options.arch_rpms_url)

        # no step specified
        self.options.args = self.args
        if len(self.args) == 0:
            self.options.steps=TestPlc.default_steps
        else:
            self.options.steps = self.args

        if self.options.list_steps:
            self.init_steps()
            self.list_steps()
            return 'SUCCESS'

        # steps
        if not self.options.steps:
            #default (all) steps
            #self.options.steps=['dump','clean','install','populate']
            self.options.steps=TestPlc.default_steps

        # rewrite '-' into '_' in step names
        self.options.steps = [ step.replace('-','_') for step in self.options.steps ]
        self.options.exclude = [ step.replace('-','_') for step in self.options.exclude ]
        self.options.ignore = [ step.replace('-','_') for step in self.options.ignore ]

        # technicality, decorate known steps to produce the '_ignore' version
        TestPlc.create_ignore_steps()

        # exclude
        selected=[]
        for step in self.options.steps:
            keep=True
            for exclude in self.options.exclude:
                if utils.match(step,exclude):
                    keep=False
                    break
            if keep: selected.append(step)

        # ignore
        selected = [ step if step not in self.options.ignore else step+"_ignore"
                     for step in selected ]

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

        # provision on local substrate
        all_plc_specs = LocalSubstrate.local_substrate.provision(all_plc_specs,self.options)

        # remember substrate IP address(es) for next run
        ips_bplc_file=open('arg-ips-bplc','w')
        for plc_spec in all_plc_specs:
            ips_bplc_file.write("%s\n"%plc_spec['host_box'])
        ips_bplc_file.close()
        ips_vplc_file=open('arg-ips-vplc','w')
        for plc_spec in all_plc_specs:
            ips_vplc_file.write("%s\n"%plc_spec['settings']['PLC_API_HOST'])
        ips_vplc_file.close()
        # ditto for nodes
        ips_bnode_file=open('arg-ips-bnode','w')
        for plc_spec in all_plc_specs:
            for site_spec in plc_spec['sites']:
                for node_spec in site_spec['nodes']:
                    ips_bnode_file.write("%s\n"%node_spec['host_box'])
        ips_bnode_file.close()
        ips_vnode_file=open('arg-ips-vnode','w')
        for plc_spec in all_plc_specs:
            for site_spec in plc_spec['sites']:
                for node_spec in site_spec['nodes']:
                    # back to normal (unqualified) form
                    stripped=node_spec['node_fields']['hostname'].split('.')[0]
                    ips_vnode_file.write("%s\n"%stripped)
        ips_vnode_file.close()

        # build a TestPlc object from the result, passing options
        for spec in all_plc_specs:
            spec['failed_step'] = False
        all_plcs = [ (x, TestPlc(x,self.options)) for x in all_plc_specs]

        # pass options to utils as well
        utils.init_options(self.options)

        overall_result = 'SUCCESS'
        all_step_infos=[]
        for step in self.options.steps:
            if not TestPlc.valid_step(step):
                continue
            # some steps need to be done regardless of the previous ones: we force them
            force=False
            if step.endswith("_force"):
                step=step.replace("_force","")
                force=True
            # allow for steps to specify an index like in 
            # run checkslice@2
            try:        (step,qualifier)=step.split('@')
            except:     qualifier=self.options.qualifier

            try:
                stepobj = Step (step)
                for (substep, method) in stepobj.tuples():
                    # a cross step will run a method on TestPlc that has a signature like
                    # def cross_foo (self, all_test_plcs)
                    cross=False
                    if substep.find("cross_") == 0:
                        cross=True
                    all_step_infos.append ( (substep, method, force, cross, qualifier, ) )
            except :
                utils.header("********** FAILED step %s (NOT FOUND) -- won't be run"%step)
                traceback.print_exc()
                overall_result = 'FAILURE'
            
        if self.options.dry_run:
            self.show_env(self.options,"Dry run")
        
        # init & open trace file if provided
        if self.options.trace_file and not self.options.dry_run:
            # create dir if needed
            trace_dir=os.path.dirname(self.options.trace_file)
            if trace_dir and not os.path.isdir(trace_dir):
                os.makedirs(trace_dir)
            trace=open(self.options.trace_file,"w")

        # do all steps on all plcs
        TIME_FORMAT="%H-%M-%S"
        TRACE_FORMAT="TRACE: %(plc_counter)d %(begin)s->%(seconds)ss=%(duration)s status=%(status)s step=%(stepname)s plc=%(plcname)s force=%(force)s\n"
        for (stepname,method,force,cross,qualifier) in all_step_infos:
            plc_counter=0
            for (spec,plc_obj) in all_plcs:
                plc_counter+=1
                # skip this step if we have specified a plc_explicit
                if qualifier and plc_counter!=int(qualifier): continue

                plcname=spec['name']
                across_plcs = [ o for (s,o) in all_plcs if o!=plc_obj ]

                # run the step
                beg_time = datetime.now()
                begin = beg_time.strftime(TIME_FORMAT)
                if not spec['failed_step'] or force or self.options.interactive or self.options.keep_going:
                    skip_step=False
                    if self.options.interactive:
                        prompting=True
                        while prompting:
                            msg="%d Run step %s on %s [r](un)/d(ry_run)/p(roceed)/s(kip)/q(uit) ? "%(plc_counter,stepname,plcname)
                            answer=raw_input(msg).strip().lower() or "r"
                            answer=answer[0]
                            if answer in ['s','n']:     # skip/no/next
                                print '%s on %s skipped'%(stepname,plcname)
                                prompting=False
                                skip_step=True
                            elif answer in ['q','b']:   # quit/bye
                                print 'Exiting'
                                return 'FAILURE'
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
                            elif answer in ['p']:
                                # take it as a yes and leave interactive mode
                                prompting=False
                                self.options.interactive=False
                            elif answer in ['r','y']:   # run/yes
                                prompting=False
                    if skip_step:
                        continue
                    try:
                        force_msg=""
                        if force and spec['failed_step']: force_msg=" (forced after %s has failed)"%spec['failed_step']
                        utils.header("********** %d RUNNING step %s%s on plc %s"%(plc_counter,stepname,force_msg,plcname))
                        if not cross:   step_result = method(plc_obj)
                        else:           step_result = method(plc_obj,across_plcs)
                        if isinstance (step_result,Ignored):
                            step_result=step_result.result
                            if step_result:
                                msg="OK"
                            else:
                                msg="KO"
                                # do not overwrite if FAILURE
                                if overall_result=='SUCCESS': 
                                    overall_result='IGNORED'
                            utils.header('********** %d IGNORED (%s) step %s on %s'%(plc_counter,msg,stepname,plcname))
                            status="%s[I]"%msg
                        elif step_result:
                            utils.header('********** %d SUCCESSFUL step %s on %s'%(plc_counter,stepname,plcname))
                            status="OK"
                        else:
                            overall_result = 'FAILURE'
                            spec['failed_step'] = stepname
                            utils.header('********** %d FAILED step %s on %s (discarded from further steps)'\
                                             %(plc_counter,stepname,plcname))
                            status="KO"
                    except:
                        overall_result='FAILURE'
                        spec['failed_step'] = stepname
                        traceback.print_exc()
                        utils.header ('********** %d FAILED (exception) step %s on %s (discarded from further steps)'\
                                          %(plc_counter,stepname,plcname))
                        status="KO"

                # do not run, just display it's skipped
                else:
                    why="has failed %s"%spec['failed_step']
                    utils.header("********** %d SKIPPED Step %s on %s (%s)"%(plc_counter,stepname,plcname,why))
                    status="UNDEF"
                if not self.options.dry_run:
                    delay = datetime.now()-beg_time
                    seconds = int(delay.total_seconds())
                    duration = str(delay)
                    # always do this on stdout
                    print TRACE_FORMAT%locals()
                    # duplicate on trace_file if provided
                    if self.options.trace_file:
                        trace.write(TRACE_FORMAT%locals())
                        trace.flush()

        if self.options.trace_file and not self.options.dry_run:
            trace.close()

        # free local substrate
        LocalSubstrate.local_substrate.release(self.options)
        
        return overall_result

    # wrapper to run, returns a shell-compatible result
    # retcod:
    # 0: SUCCESS
    # 1: FAILURE
    # 2: SUCCESS but some ignored steps failed
    # 3: OTHER ERROR
    def main(self):
        try:
            success=self.run()
            if success == 'SUCCESS':    return 0
            elif success == 'IGNORED':  return 2
            else:                       return 1
        except SystemExit:
            print 'Caught SystemExit'
            return 3
        except:
            traceback.print_exc()
            return 3

if __name__ == "__main__":
    exit_code = TestMain().main()
    print "TestMain exit code",exit_code
    sys.exit(exit_code)
