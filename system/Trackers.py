#!/usr/bin/python

import os

import utils
from TestSsh import TestSsh

# 2 types of trackers
# (*) plc trackers remembers the running myplcs
# (*) qemu trackers keeps track of the running qemu nodes
#
# trackers allow us to let the test run after the build has finished, 
# and to kill/stop the oldest instances later when we need space
# 

#################### Tracker
class Tracker:
    
    def __init__ (self, options,filename, instances):
        self.options=options
        self.filename=filename
        self.instances=instances
        try:
            tracks=file(self.filename).readlines()
            tracks = [ track.strip() for track in tracks ]
        except:
            tracks=[]
        self.tracks = [track for track in tracks if track]

    def store (self):
        out = file(self.filename,'w')
        for track in self.tracks:
            out.write('%s\n'%(track))
        out.close()

    def record (self,track):
        for already in self.tracks:
            if already==track:
                print '%s is already included in %s'%(already,self.filename)
                return
        if self.options.dry_run:
            print 'dry_run: Tracker.record - skipping %s'%(track)
            return
        self.tracks.append( track )
        print "Recorded %s in tracker %s"%(track,self.filename)

    # this actually stops the old instances to fit the number of instances 
    def free (self):
        # number of instances to stop
        how_many=len(self.tracks)-self.instances
        # nothing todo until we have more than keep_vservers in the tracker
        if how_many <= 0:
            print 'Tracker.free : limit %d not reached'%self.instances
            return
        to_stop = self.tracks[:how_many]
        for track in to_stop:
            command = self.stop_command (track)
            utils.system(command)
        if not self.options.dry_run:
            self.tracks = self.tracks[how_many:]

    # this stops ALL known instances
    def cleanup (self):
        for track in self.tracks:
            command=self.stop_command(track)
            utils.system(command)
        if not self.options.dry_run:
            self.tracks=[]

class TrackerPlc (Tracker):
    
    DEFAULT_FILENAME=os.environ['HOME']+"/tracker-plcs"
    # how many concurrent plcs are we keeping alive - adjust with the IP pool size
    DEFAULT_MAX_INSTANCES = 12

    def __init__ (self,options,filename=None,instances=0):
        if not filename: filename=TrackerPlc.DEFAULT_FILENAME
        if not instances: instances=TrackerPlc.DEFAULT_MAX_INSTANCES
        Tracker.__init__(self,options,filename,instances)

    def record (self, hostname, vservername):
        Tracker.record (self,"%s@%s"%(hostname,vservername))

    def stop_command (self, track):
        (hostname,vservername) = track.split('@')
        return TestSsh(hostname).actual_command("vserver --silent %s stop"%vservername)
        

class TrackerQemu (Tracker):

    DEFAULT_FILENAME=os.environ['HOME']+"/tracker-emus"
    # how many concurrent plcs are we keeping alive - adjust with the IP pool size
    DEFAULT_MAX_INSTANCES = 2

    def __init__ (self,options,filename=None,instances=0):
        if not filename: filename=TrackerQemu.DEFAULT_FILENAME
        if not instances: instances=TrackerQemu.DEFAULT_MAX_INSTANCES
        Tracker.__init__(self,options,filename,instances)

    def record (self, hostname, buildname, nodename):
        Tracker.record (self,"%s@%s@%s"%(hostname,buildname,nodename))

    def stop_command (self, track):
        (hostname,buildname,nodename) = track.split('@')
        return TestSsh(hostname).actual_command("%s/qemu-%s/qemu-kill-node this"%(buildname,nodename))
