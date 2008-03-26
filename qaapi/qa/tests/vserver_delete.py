#!/usr/bin/python
import os,sys
from Test import Test
from qa import utils

class vserver_delete(Test):
    """
    Delete the specified vserver
    """

    def call(self, name):
        (status, output) = utils.commands("vserver %(name)s stop" % locals(), False)
        (status, output) = utils.commands("vserver %(name)s delete" % locals())

        return 1

