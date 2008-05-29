ifdef PLCHOST
ifdef VSERVER
PLCSSH:=root@$(PLCHOST):/vservers/$(VSERVER)
endif
endif

LOCAL_RSYNC_EXCLUDES	:= --exclude '*.pyc' 
RSYNC_EXCLUDES		:= --exclude .svn --exclude CVS --exclude '*~' --exclude TAGS $(LOCAL_RSYNC_EXCLUDES)
RSYNC_COND_DRY_RUN	:= $(if $(findstring n,$(MAKEFLAGS)),--dry-run,)
RSYNC			:= rsync -a -v $(RSYNC_COND_DRY_RUN) $(RSYNC_EXCLUDES)

sync:
ifeq (,$(PLCSSH))
	echo "sync: You must define PLCHOST and VSERVER on the command line"
	echo " e.g. make sync PLCHOST=private.one-lab.org VSERVER=myplc01" ; exit 1
else
	+$(RSYNC) Test.py $(PLCSSH)/usr/share/plc_api/
endif
