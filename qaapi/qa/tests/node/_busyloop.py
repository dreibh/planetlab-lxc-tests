#!/usr/bin/python

import sys
import time

def main(sec):                         
    now = time.time()
    stop = now + float(sec)
    print 'about to busy-wait for', sec, 'seconds'
    while now < stop:
        now = time.time()

if __name__ == "__main__":
    main(sys.argv[1])
