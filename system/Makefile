tags:
	find . '(' -name '*.py' -o -name 'qemu-*' ')' | grep -v '.svn/' | xargs etags

.PHONY: tags

####################

########## make sync PLCHOST=hostname VSERVER=vservername
ifdef PLCHOST
ifdef BUILDNAME
PLCSSH:=root@$(PLCHOST):$(BUILDNAME)
endif
endif

LOCAL_RSYNC_EXCLUDES	:= --exclude '*.pyc' --exclude 'arg*'
RSYNC_EXCLUDES		:= --exclude .svn --exclude CVS --exclude '*~' --exclude TAGS $(LOCAL_RSYNC_EXCLUDES)
RSYNC_COND_DRY_RUN	:= $(if $(findstring n,$(MAKEFLAGS)),--dry-run,)
RSYNC			:= rsync -a -v $(RSYNC_COND_DRY_RUN) $(RSYNC_EXCLUDES)

sync:
ifeq (,$(PLCSSH))
	echo "sync: You must define PLCHOST and BUILDNAME on the command line"
	echo " e.g. make sync PLCHOST=private.one-lab.org BUILDNAME=" ; exit 1
else
	+$(RSYNC) ./ $(PLCSSH)
endif
