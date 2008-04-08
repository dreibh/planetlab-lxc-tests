#!/usr/bin/python

import sys
import re

def main ():
    fin=open(sys.argv[1])
    fou=open(sys.argv[2],"w")
    ip=sys.argv[3]
    
    found=False
    lo_matcher=re.compile("\A(?P<left>.+)\s+-i\s+lo\s+-j\s+ACCEPT")
    # what comes out of iptables-save has short-options syntax
    ip_matcher=re.compile("-(s|d) %s"%ip)
    for line in fin.readlines():
        attempt=lo_matcher.match(line)
        if attempt:
            fou.write(line)
            # open-up for this IP
            fou.write("%s -s %s -j ACCEPT\n"%(attempt.group('left'),ip))
            fou.write("%s -d %s -j ACCEPT\n"%(attempt.group('left'),ip))
            found=True
        else:
            attempt = ip_matcher.match(line)
            # do not rewrite old lines for this ip
            if not attempt:
                fou.write(line)

    fin.close()
    fou.close()
    if found : return 0
    else : return 1

if __name__ == '__main__':
    main()
                    
