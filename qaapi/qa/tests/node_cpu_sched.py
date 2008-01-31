#!/usr/bin/python

"""
This file contains a stand-alone CPU scheduler test to be run on a node.
It still needs to be integrated into the testing framework.
"""

import sys
import commands
import re
from threading import Thread

class CpuTest:
    def __init__(self, ctx, cpu, resv, share, min, max, desc):
        self.ctx = ctx
        self.cpu = cpu
        self.resv = resv
        self.share = share
        self.min = min
        self.max = max
        self.desc = desc


class Spinner(Thread):
    def __init__(self, test):
        Thread.__init__(self)

        cmd = '/usr/bin/time ./busyloop.py 15'
        if test.share:
            flags = '--idle-time'
        else:
            flags = ''

        self.cmd = 'taskset -c ' + str(test.cpu) \
            + ' vcontext --create --xid ' + str(test.ctx) + ' --disconnect ' \
            + '-- vsched --fill-rate ' + str(test.resv) + ' --interval 100 ' \
            + '--fill-rate2 ' + str(test.share) + ' --interval2 1000 ' \
            + '--tokens 100 --tokens-min 50 --tokens-max 100 --force '\
            + flags + ' -- vattribute --flag sched_hard -- ' + cmd

        self.test = test

    def run(self):
        self.output = commands.getoutput( self.cmd )

    def passed(self):
        match = re.search('elapsed (\d+)%CPU', self.output)
        if match:
            self.pct = int(match.group(1))
        else:
            print "Error parsing output: cannot get CPU%"
            self.pct = 0

        return ( self.pct >= self.test.min and self.pct <= self.test.max )


def run_test(testlist):
    failures = 0

    for test in testlist:
        test.thread = Spinner(test)
        test.thread.start()

    for test in testlist:
        test.thread.join()

    for test in testlist:
        if test.thread.passed():
            print "[PASSED] (" + str(test.thread.pct) + "%)\t", test.desc
        else:
            print "[FAILED] (" + str(test.thread.pct) + "%)\t", test.desc
            failures += 1

    return failures

### Test 1: test hard rate-limiting to 25% (should get <= 25%)
def test_1():
    test = CpuTest(ctx=600, cpu=0, resv=25, share=0, min=24, max=25, 
                   desc = "Test 1: single ctx, 25% resv")

    return run_test([ test ])

### Test 2: test share scheduling of a single task (should get 100%)
def test_2():
    test = CpuTest(ctx=600, cpu=0, resv=0, share=1, min=99, max=100, 
                   desc = "Test 2: single ctx, one share")

    return run_test([ test ])

### Test 3: test hard & share scheduling of a single task (should get 100%)
def test_3():
    test = CpuTest(ctx=600, cpu=0, resv=25, share=1, min=99, max=100, 
                   desc = "Test 3: single ctx, 25% resv, one share")

    return run_test([ test ])

### Test 4: test relative share scheduling of several tasks
def test_4():
    test1 = CpuTest(ctx=600, cpu=0, resv=0, share=1, min=15, max=17, 
                   desc = "Test 4: ctx 1, one share")
    test2 = CpuTest(ctx=601, cpu=0, resv=0, share=2, min=32, max=34, 
                   desc = "        ctx 2, two shares")
    test3 = CpuTest(ctx=602, cpu=0, resv=0, share=3, min=49, max=51, 
                   desc = "        ctx 3, three shares")

    return run_test([ test1, test2, test3 ])

### Test 5: test hard rate limit and shares
def test_5():
    test1 = CpuTest(ctx=600, cpu=0, resv=0, share=1, min=14, max=16, 
                   desc = "Test 5: ctx 1, one share")
    test2 = CpuTest(ctx=601, cpu=0, resv=0, share=2, min=29, max=33, 
                   desc = "        ctx 2, two shares")
    test3 = CpuTest(ctx=602, cpu=0, resv=0, share=3, min=44, max=47, 
                   desc = "        ctx 3, three shares")
    test4 = CpuTest(ctx=603, cpu=0, resv=10, share=0, min=9, max=10, 
                   desc = "        ctx 4, 10% resv")

    return run_test([ test1, test2, test3, test4 ])

### Test 6: test guarantee and shares
def test_6():
    test1 = CpuTest(ctx=600, cpu=0, resv=0, share=1, min=9, max=11, 
                   desc = "Test 6: ctx 1, one share")
    test2 = CpuTest(ctx=601, cpu=0, resv=0, share=2, min=19, max=21, 
                   desc = "        ctx 2, two shares")
    test3 = CpuTest(ctx=602, cpu=0, resv=0, share=3, min=29, max=31, 
                   desc = "        ctx 3, three shares")
    test4 = CpuTest(ctx=603, cpu=0, resv=30, share=1, min=38, max=41, 
                   desc = "        ctx 4, 30% resv, one share")

    return run_test([ test1, test2, test3, test4 ])

### Test 7: SMP active (both tasks should get 100% on an SMP)
def test_7():
    test1 = CpuTest(ctx=600, cpu=0, resv=0, share=1, min=99, max=100, 
                   desc = "Test 7: ctx 1, processor 1")
    test2 = CpuTest(ctx=601, cpu=1, resv=0, share=1, min=99, max=100, 
                   desc = "        ctx 2, processor 2")

    return run_test([ test1, test2 ])

def main():
    failures = 0

    failures += test_1()
    failures += test_2()
    failures += test_3()
    failures += test_4()
    failures += test_5()
    failures += test_6()
    failures += test_7()

    return failures

if __name__ == "__main__":
    sys.exit(main())
