tags:
	find . '(' -name '*.py' -o -name 'qemu-*' ')' | grep -v '.svn/' | xargs etags


LOCAL_RSYNC_EXCLUDES	:= --exclude '*.pyc' --exclude 'arg*' 
RSYNC_EXCLUDES		:= --exclude .svn --exclude CVS --exclude '*~' --exclude TAGS $(LOCAL_RSYNC_EXCLUDES)
RSYNC_COND_DRY_RUN	:= $(if $(findstring n,$(MAKEFLAGS)),--dry-run,)
RSYNC			:= rsync -a -v $(RSYNC_COND_DRY_RUN) $(RSYNC_EXCLUDES)

sync:
ifeq (,$(RSYNC_URL))
	echo "sync: You must define target host as RSYNC_URL on the command line"
	echo " e.g. make sync RSYNC_URL=root@testbox1:workdir" ; exit 1
else
	+$(RSYNC) ./ $(RSYNC_URL)/
endif
