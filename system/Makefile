tags:
	find . '(' -name '*.py' -o -name 'qemu-*' ')' | grep -v '.svn/' | xargs etags

.PHONY: tags

####################

########## make sync TESTMASTER=hostname BUILDNAME=vservername
ifdef TESTMASTER
ifdef BUILDNAME
PLCSSH:=root@$(TESTMASTER):$(BUILDNAME)
endif
endif

LOCAL_RSYNC_EXCLUDES	:= --exclude '*.pyc' --exclude 'arg*'
RSYNC_EXCLUDES		:= --exclude .svn --exclude CVS --exclude '*~' --exclude TAGS $(LOCAL_RSYNC_EXCLUDES)
RSYNC_COND_DRY_RUN	:= $(if $(findstring n,$(MAKEFLAGS)),--dry-run,)
RSYNC			:= rsync -a -v $(RSYNC_COND_DRY_RUN) $(RSYNC_EXCLUDES)

sync:
ifeq (,$(PLCSSH))
	echo "sync: You must define TESTMASTER and BUILDNAME on the command line"
	echo " e.g. make sync TESTMASTER=testmaster.onelab.eu BUILDNAME=2009.07.10--1l-f8-32" ; exit 1
else
	+$(RSYNC) ./ $(PLCSSH)
endif



