#!/usr/bin/env python3
# -*- python3 -*-
# Thierry Parmentelat <thierry.parmentelat@inria.fr>
# Copyright (C) 2015 INRIA 

import sys, time
from datetime import datetime, timedelta

import utils

### more generic code for waiting for any number of things 
### within a given timeframe i.e. given some timeout/silent/period
### takes in argument a list of tasks that are instances 
### of a CompleterTask subclass
class Completer:
    def __init__ (self, tasks, verbose=True, message=None):
        self.tasks = tasks
        self.verbose = verbose
        self.message = "({})".format(message) if message else ""
    def run (self, timeout_timedelta, silent_timedelta, period):
        begin = datetime.now()
        timeout = begin+timeout_timedelta
        timeout_seconds = timeout_timedelta.total_seconds()
        timeout_minutes = timeout_seconds/60
        graceout = datetime.now()+silent_timedelta
        silent_seconds = silent_timedelta.total_seconds()
        silent_minutes = silent_seconds/60
        period_seconds = int(period.total_seconds())
        if self.verbose:
            if timeout_seconds >= 120:
                utils.header("Completer [{} tasks]: max timeout is {} minutes, "
                             "silent for {} minutes (period is {} s)"\
                             .format(len(self.tasks), timeout_minutes,
                                     silent_minutes, period_seconds))
            else:
                utils.header("Completer [{} tasks]: max timeout is {} seconds, "
                             "silent for {} seconds (period is {} s)"\
                             .format(len(self.tasks), timeout_seconds,
                                     silent_seconds, period_seconds))
        tasks = self.tasks
        while tasks:
            fine = []
            for task in tasks:
                success = task.run (silent=datetime.now() <= graceout)
                if success:
                    fine.append(task)
            for task in fine:
                tasks.remove(task)
            if not tasks:
                if self.verbose:
                    duration = datetime.now() - begin
                    print("total completer {} {}s".format(self.message,
                                                          int(duration.total_seconds())))
                return True
            if datetime.now() > timeout:
                for task in tasks: 
                    task.failure_epilogue()
                return False
            if self.verbose:
                print('{}s..'.format(period_seconds), end=' ')
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
        result = self.actual_run()
        if silent:
            print('+' if result else '.', end=' ')
            sys.stdout.flush()
        else:
            print(self.message(), "->", "OK" if result else "KO")
        return result

    def message (self):
        return "you-need-to-redefine-message"

    def failure_epilogue (self):
        print("you-need-to-redefine-failure_epilogue")

# random result
class TaskTest (CompleterTask):
    counter = 1
    def __init__ (self,max):
        import random
        self.counter = TaskTest.counter
        TaskTest.counter += 1
        self.delay = random.random()*max
        self.fire = datetime.now() + timedelta(seconds=self.delay)
    def actual_run(self):
        return datetime.now() >= self.fire
    def message (self):
        return "Task {} - delay was {}s".format(self.counter, self.delay)

    def failure_epilogue (self):
        print("BOTTOM LINE: FAILURE with task ({})".format(self.counter))

def main ():
    import sys
    if len(sys.argv) != 6:
        print("Usage: <command> number_tasks max_random timeout_s silent_s period_s")
        sys.exit(1)
    [number, max, timeout, silent, period] = [ int(x) for x in sys.argv[1:]]
    tasks = [ TaskTest(max) for i in range(number)]
    success = Completer(tasks,verbose=True).run(timedelta(seconds=timeout),
                                                timedelta(seconds=silent),
                                                timedelta(seconds=period))
    print("OVERALL",success)

if __name__ == '__main__':
    main()
