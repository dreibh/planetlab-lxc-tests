#!/usr/bin/env python
import sys, time
from datetime import datetime, timedelta

import utils

### more generic code for waiting for any number of things 
### within a given timeframe i.e. given some timeout/silent/period
### takes in argument a list of tasks that are instances 
### of a CompleterTask subclass
class Completer:
    def __init__ (self, tasks, verbose=True):
        self.tasks=tasks
        self.verbose=verbose
    def run (self, timeout_timedelta, silent_timedelta, period=None):
        timeout = datetime.now()+timeout_timedelta
        timeout_minutes = timeout_timedelta.total_seconds()/60
        graceout = datetime.now()+silent_timedelta
        silent_minutes = silent_timedelta.total_seconds()/60
        period_seconds=int(period.total_seconds())
        if self.verbose:
            utils.header("max timeout is %d minutes, silent for %d minutes (period is %s s)"%\
                             (timeout_minutes,silent_minutes,period_seconds))
        tasks=self.tasks
        while tasks:
            fine=[]
            for task in tasks:
                success=task.run (silent=datetime.now() <= graceout)
                if success: fine.append(task)
            for task in fine: tasks.remove(task)
            if not tasks: return True
            if datetime.now() > timeout:
                for task in tasks: 
                    print task.failure_message()
                    task.failure_epilogue()
                return False
            if self.verbose:
                print '%ds..'%period_seconds,
            time.sleep(period_seconds)
        # in case we're empty 
        return True


#################### CompleterTask
### . run(silent)  (return True or False)
###   silent is an input boolean indicating if we're within the silent period
### . failure()    (print a message)

########## expectations (+ first arg self)
# failure()     (to describe which went wrong once it's over)
# -- and --
# run (silent)  
# -- or -- 
# actual_run()
# message()

class CompleterTask:
    def run (self, silent):
        result=self.actual_run()
        if silent:
            print '+' if result else '.',
            sys.stdout.flush()
        else:
            print self.message(),"->","OK" if result else "KO"
        return result
    def message (self): return "you-need-to-redefine-message"
    def failure_message (self): return "you-need-to-redefine-failure_message"
    def failure_epilogue (self): pass

# random result
class TaskTest (CompleterTask):
    counter=1
    def __init__ (self,max):
        import random
        self.counter=TaskTest.counter
        TaskTest.counter+=1
        self.delay=random.random()*max
        self.fire=datetime.now()+timedelta(seconds=self.delay)
    def actual_run(self):
        return datetime.now()>=self.fire
    def message (self):
        return "Task %d - delay was %d s"%(self.counter,self.delay)

    def failure_message (self): return "BOTTOM LINE: FAILURE with task (%s)"%self.counter

def main ():
    import sys
    if len(sys.argv)!=6:
        print "Usage: <command> number_tasks max_random timeout_s silent_s period_s"
        sys.exit(1)
    [number,max,timeout,silent,period]= [ int(x) for x in sys.argv[1:]]
    tasks = [ TaskTest(max) for i in range(number)]
    success=Completer(tasks,verbose=True).run(timedelta(seconds=timeout),
                                              timedelta(seconds=silent),
                                              timedelta(seconds=period))
    print "OVERALL",success

if __name__ == '__main__':
    main()
