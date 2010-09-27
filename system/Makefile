tags:
	find . '(' -name '*.py' -o -name 'qemu-*' ')' | grep -v '.svn/' | xargs etags

.PHONY: tags

####################

TESTMASTER ?= testmaster.onelab.eu

########## make sync TESTMASTER=hostname BUILD=vservername
ifdef BUILD
PLCSSH:=root@$(TESTMASTER):$(BUILD)
endif

LOCAL_RSYNC_EXCLUDES	:= --exclude '*.pyc' --exclude 'arg*' --exclude LocalTestResources.py
RSYNC_EXCLUDES		:= --exclude .svn --exclude CVS --exclude '*~' --exclude TAGS $(LOCAL_RSYNC_EXCLUDES)
RSYNC_COND_DRY_RUN	:= $(if $(findstring n,$(MAKEFLAGS)),--dry-run,)
RSYNC			:= rsync -a -v $(RSYNC_COND_DRY_RUN) $(RSYNC_EXCLUDES)

sync:
ifeq (,$(PLCSSH))
	echo "sync: You must define TESTMASTER and BUILD on the command line"
	echo " e.g. make sync TESTMASTER=testmaster.onelab.eu BUILD=2009.07.10--1l-f8-32" ; exit 1
else
	+$(RSYNC) ./ $(PLCSSH)
endif



