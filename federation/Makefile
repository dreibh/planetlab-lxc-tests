### -*-Makefile-*-
# $Id$
PLC1=plc1.inria.fr
PLC2=plc2.inria.fr

CHROOTJAIL=/plc/root
CHROOT=chroot $(CHROOTJAIL)
PORT=5432
SITEDIR=/etc/planetlab/configs
SITE=site.xml
APIDIR=/usr/share/plc_api
ROOTAPIDIR=/plc/root$(APIDIR)
WORKDIR=new_plc_api/tests

PLC1SSH=root@$(PLC1)
PLC2SSH=root@$(PLC2)

PY=python -u

PLCS=-1 -2
SIZES=-m -n -b -h

all:help

# if make is invoked with -n, run rsync, but with --dry-run
RSYNC_EXCLUDES		:= --exclude .svn --exclude '*~' --exclude '*.pyc'
RSYNC_CMD		:= rsync
RSYNC_COND_DRY_RUN	:= $(if $(findstring n,$(MAKEFLAGS)),--dry-run,)
RSYNC_ARGS		+= $(RSYNC_COND_DRY_RUN) $(RSYNC_EXCLUDES)
RSYNC			:= $(RSYNC_CMD) $(RSYNC_ARGS)

#################### remote invokation and chroot hops
# rule to invoke a target within the chroot context
%.chroot: target=$(subst .chroot,,$@)
%.chroot:
	$(CHROOT) $(MAKE) -C $(APIDIR)/tests INCHROOT=true $(target)
	-cp $(ROOTAPIDIR)/tests/$(target) .

# generic rules to ssh and make
# need to explicitly export MAKEFLAGS that cannot be exported by make through ssh
%.1: prefix=$(subst .1,,$@)
%.1: output=$(subst .chroot,,$(prefix))
%.1:
	@echo ">>>>>>>> entering ssh $(PLC1SSH)"
	ssh $(PLC1SSH) $(MAKE) MAKEFLAGS=$(MAKEFLAGS) -C $(WORKDIR) PLCEND=1 $(prefix) 
	@echo "<<<<<<<< exiting  ssh $(PLC1SSH)"
	-scp $(PLC1SSH):$(WORKDIR)/$(output) . 2> /dev/null
%.2: prefix=$(subst .2,,$@)
%.2: output=$(subst .chroot,,$(prefix))
%.2:
	@echo ">>>>>>>> entering ssh $(PLC2SSH)"
	ssh $(PLC2SSH) $(MAKE) MAKEFLAGS=$(MAKEFLAGS) -C $(WORKDIR) PLCEND=2 $(prefix) 
	@echo "<<<<<<<< exiting  ssh $(PLC2SSH)"
	-scp $(PLC2SSH):$(WORKDIR)/$(output) . 2> /dev/null

# cannot just depend on .1 and .2 because they are phony
%.3: prefix=$(subst .3,,$@)
%.3: 
	$(MAKE) $(prefix).1 $(prefix).2

%.both: prefix=$(subst .both,,$@)
%.both:
	$(MAKE) $(prefix).chroot.1 $(prefix).chroot.2

####################
# phony targets MUST NOT try to get their result through scp
# usage: ssh_phony_target <target>
define ssh_phony_target
$(1).chroot:
	$(CHROOT) $(MAKE) -C $(APIDIR)/tests INCHROOT=true $(1)
$(1).1:
	@echo ">>>>>>>> entering ssh $(PLC1SSH)"
	ssh $(PLC1SSH) $(MAKE) MAKEFLAGS=$(MAKEFLAGS) -C $(WORKDIR) PLCEND=1 $(1)
	@echo "<<<<<<<< exiting  ssh $(PLC1SSH)"
$(1).2:
	@echo ">>>>>>>> entering ssh $(PLC2SSH)"
	ssh $(PLC2SSH) $(MAKE) MAKEFLAGS=$(MAKEFLAGS) -C $(WORKDIR) PLCEND=2 $(1)
	@echo "<<<<<<<< exiting  ssh $(PLC2SSH)"
endef

####################
define here_and_proceed_target
PHONIES += $(1)
ifdef INCHROOT
$(1): 
	$(2)
else
ifdef PLCEND
$(1): $(1).chroot
	$(2)
else
$(1): $(1).3
	$(2)
endif
endif
endef

####################
####################
####################
PLC-PUSHS=  ../PLC ../planetlab4.sql ../migrations ../plcsh ../tests

PUSH += pclean
pclean:
	-find .. '(' -name '*.pyc' -o -name '*~' ')' | xargs rm
PUSH += proot1
proot1:
	+$(RSYNC) -a -v -C ../ root@$(PLC1):new_plc_api/
PUSH += pchroot1
pchroot1:
	+$(RSYNC) -a -v -C $(PLC-PUSHS) root@$(PLC1):$(CHROOTJAIL)$(APIDIR)/
PUSH += proot2
proot2:
	+$(RSYNC) -a -v -C ../ root@$(PLC2):new_plc_api/
PUSH += pchroot2
pchroot2:
	+$(RSYNC) -a -v -C $(PLC-PUSHS) root@$(PLC2):$(CHROOTJAIL)$(APIDIR)/

push: $(PUSH)
push.1: proot1 pchroot1
push.2: proot2 pchroot2
# DONT! mention this in PHONIES
.PHONY: push push.1 push.2

PHONIES += $(PUSH)

####################
PEERS += peer-gpg-1
peer-gpg-1:
	ssh $(PLC1SSH) "gpg --homedir=/etc/planetlab --export --armor > /etc/planetlab/gpg_plc1.pub"
PEERS += peer-gpg-2
peer-gpg-2:
	ssh $(PLC2SSH) "gpg --homedir=/etc/planetlab --export --armor > /etc/planetlab/gpg_plc2.pub"
# directly scp'ing from one url to the other does not work, looks like
# first host tries to connect the second one
PEERS += peer-push-gpg-1
peer-push-gpg-1:
	scp $(PLC1SSH):/etc/planetlab/gpg_plc1.pub ./
	scp ./gpg_plc1.pub $(PLC2SSH):/etc/planetlab/
PEERS += peer-push-gpg-2
peer-push-gpg-2:
	scp $(PLC2SSH):/etc/planetlab/gpg_plc2.pub ./
	scp ./gpg_plc2.pub $(PLC1SSH):/etc/planetlab/
PEERS += peer-push-cacert-1
peer-push-cacert-1:
	scp $(PLC1SSH):/etc/planetlab/api_ca_ssl.crt ./api_plc1.crt
	scp ./api_plc1.crt $(PLC2SSH):/etc/planetlab/
	scp ./api_plc1.crt $(PLC1SSH):/etc/planetlab/
PEERS += peer-push-cacert-2
peer-push-cacert-2:
	scp $(PLC2SSH):/etc/planetlab/api_ca_ssl.crt ./api_plc2.crt
	scp ./api_plc2.crt $(PLC1SSH):/etc/planetlab/
	scp ./api_plc2.crt $(PLC2SSH):/etc/planetlab/

PHONIES += $(PEERS)

PHONIES += peers
peers: $(PEERS)

PHONIES += peers-clean
peers-clean:
	rm -f /etc/planetlab/*plc[12]*

HELP += peers-clean.3
####################
# upgrade : install the most recent myplc rpm found in /root/$(WORKDIR)
RPM=$(shell ls -rt /root/$(WORKDIR)/myplc*rpm | tail -1)
HELP += rpm
PHONIES += rpm
rpm:
	@echo upgrade would install latest rpm : $(RPM)
HELP += version
PHONIES += version
version:
	rpm -q myplc

#### how to upgrade
UPGRADE += plc-stop
plc-stop:
	-$(CHROOT) service plc safestop
UPGRADE += plc-preserve
plc-preserve:
	cp $(SITEDIR)/$(SITE) .
UPGRADE += plc-uninstall
plc-uninstall:
	rpm -e myplc
UPGRADE += plc-clean
plc-clean:
	-rm -rf /plc/root /plc/data
UPGRADE += plc-install
plc-install:
	rpm -i $(RPM)
UPGRADE += plc-reconfig
plc-reconfig:
	service plc mount
	mkdir -p $(SITEDIR)
	cp $(SITE) $(SITEDIR)
	(echo w; echo q) | $(CHROOT) plc-config-tty
UPGRADE += plc-start
plc-start:
	$(CHROOT) service plc start

PHONIES += $(UPGRADE)

PHONIES += upgrade
upgrade: $(UPGRADE)

####################
# cleaning the database

DB += db-drop
db-drop:
	$(CHROOT) psql -U postgres --port $(PORT) template1 -c 'drop database planetlab4'
DB += db-restart
db-restart:
	service plc stop db postgresql httpd
	service plc start httpd postgresql db 
DB += db-clean-save
db-clean-save:
	$(CHROOT) pg_dump -c -U pgsqluser planetlab4 > test-clean.sql
DB += db-safeclean
db-safeclean: db-drop db-restart db-clean-save

DB += db-clean
db-clean:
	$(CHROOT) psql -U pgsqluser --port $(PORT) -d planetlab4 < test-clean.sql &> test-clean.restore 

PHONIES += $(DB)

####################
# TestPeers options :
# -m -b -h : allow to select test size (mini, normal, big, huge)
# -l 1|2	required for running -p locally from a given end for performance
# -1 | -2 	shorthands for -l 1 and -l 2 - for integration with this Makefile
### the idea is:
# first clean off dbs
# run populate separately on both ends
# optionally save database at this point
# then run end of script locally
####################

### for a given 'targetname' like, e.g. 'e-n', we define the following targets
# testpeers.<targetname>.out -- for running the test
# testpeers.<targetname>.diff -- to compute the difference with expected result
# testpeers.<targetname>.adopt -- phony target for adopting new result - no commit done

###
# generic rule for running TestPeers
# make testpeers.-option.some.stuff.out
# => python -u ./TestPeers.py -option some stuff > testpeers.-option.some.stuff.out 2>&1
testpeers.%.out: prefix=$(subst .out,,$@)
testpeers.%.out: dotargs=$(subst testpeers.,,$(prefix))
testpeers.%.out: args=$(subst ., ,$(dotargs))
testpeers.%.out:
	$(PY) ./TestPeers.py $(args) > $@ 2>&1 ; if [ "$$?" != 0 ] ; then mv $@ $@.fail ; exit 1; fi

### generic rule for computing differences -- 
# xxx this requires changes in TestPeers due to the new return code of RefreshPeers
# remove time/delay dependent output
normalize	= egrep -v "'expires':|^+++.*ellapsed"
%.nout: %.out
	$(normalize) $*.out > $@
%.nref: %.ref
	$(normalize) $*.ref > $@

testpeers.%.diff: out=$(subst .diff,.out,$@)
testpeers.%.diff: nout=$(subst .diff,.nout,$@)
testpeers.%.diff: ref=$(subst .diff,.ref,$@)
testpeers.%.diff: nref=$(subst .diff,.nref,$@)
testpeers.%.diff: 
	@if [ ! -f $(out) ] ; then echo "Could not locate $(out)" ; exit 1 ; fi
	@if [ ! -f $(ref) ] ; then echo "Could not locate $(ref)" ; exit 1 ; fi
	$(MAKE) $(nref) $(nout)
	diff $(nref) $(nout) > $@

### generic rule for adopting current result 
testpeers.%.ckp: prefix=$(subst .ckp,,$@)
testpeers.%.ckp: out=$(subst .ckp,.out,$@)
testpeers.%.ckp: ref=$(subst .ckp,.ref,$@)
testpeers.%.ckp:
	@if [ ! -f $(out) ] ; then echo "Could not locate $(out)" ; exit 1 ; fi
	cp $(out) $(ref)
	rm -f $(prefix).{diff,nout,nref}

testpeers.%.clean: prefix=$(subst .clean,,$@)
testpeers.%.clean: 
	rm -f $(prefix).{out,nout,nref,diff}


HELP += testpeers-clean
$(eval $(call here_and_proceed_target,testpeers-clean,rm -f testpeers*.nref testpeers*.nout))

HELP += testpeers-distclean
$(eval $(call here_and_proceed_target,testpeers-distclean,rm -f testpeers*.out testpeers*.sql testpeers*.nref testpeers*.nout))

HELP += clean 
clean: testpeers-clean
HELP += sqlclean
$(eval $(call here_and_proceed_target,sqlclean,rm test*.sql))
HELP += distclean
distclean: testpeers-distclean
PHONIES += clean distclean

HELP += sql-clean
$(eval $(call here_and_proceed_target,sql-clean,rm testpeers.*.sql))

##############################
# creating a snapshot of the databases
# for efficiency this is done from a Direct API method, thus under a chroot

define snapshot_and_restore_size_plc
testpeers.$(1).$(2).sql: testpeers.$(1).$(2).out
	pg_dump -c -U pgsqluser planetlab4 > testpeers.$(1).$(2).sql

testpeers.$(1).$(2).restore: testpeers.$(1).$(2).sql
	echo Restoring testpeers.$(1).$(2).sql
	psql -U pgsqluser --port $(PORT) -d planetlab4 -f testpeers.$(1).$(2).sql &> testpeers.$(1).$(2).restore
DB-SQL += testpeers.$(1).$(2).sql 
DB-RESTORE += testpeers.$(1).$(2).restore
endef

define snapshot_and_restore_size
$(foreach plc,$(PLCS),$(eval $(call snapshot_and_restore_size_plc,$(1),$(plc).populate)))
endef

$(foreach size,$(SIZES),$(eval $(call snapshot_and_restore_size,$(size))))

define populate_shortcut
ifndef PLCEND
populate$(1): populate$(1).init populate$(1).run
populate$(1).all: db-clean.3 populate$(1).clean populate$(1).init populate$(1).run
populate$(1).init: testpeers.$(1).-1.populate.out.chroot.1 testpeers.$(1).-1.populate.sql.chroot.1 
populate$(1).init: testpeers.$(1).-2.populate.out.chroot.2 testpeers.$(1).-2.populate.sql.chroot.2 
populate$(1).restore: testpeers.$(1).-1.populate.restore.chroot.1 testpeers.$(1).-2.populate.restore.chroot.2
populate$(1).run: testpeers.$(1).populate_end.out
populate$(1).diff: testpeers.$(1).-1.populate.diff testpeers.$(1).-2.populate.diff testpeers.$(1).populate_end.diff 
populate$(1).ckp: testpeers.$(1).-1.populate.ckp testpeers.$(1).-2.populate.ckp testpeers.$(1).populate_end.ckp 
$(eval $(call here_and_proceed_target,populate$(1).clean,rm -f testpeers.$(1)*populate*.out testpeers.$(1)*populate*.restore))
$(eval $(call here_and_proceed_target,populate$(1).sqlclean,rm -f testpeers.$(1)*populate*.sql))
endif
endef

$(foreach size,$(SIZES),$(eval $(call populate_shortcut,$(size))))

populate.help:
	@echo "===================="
	@echo "populate test targets"	
	@echo -e "populate-n\t\truns .init and .run"
	@echo -e "populate-b.init\t\texpects a clean db, populates only and dumps"
	@echo -e "populate-b.all\t\tcleans the db and former test results, runs the full test"
	@echo -e "populate-m.run\t\truns the actual test after both plcs were inited"
	@echo -e "populate-h.restore\t\trestores both plcs as if just inited"
	@echo -e "populate-n.ckp\t\tcheckpoints out files as references"
	@echo -e "populate-n.diff\t\tcompares out files against reference"

####################
define testpeers_shortcut
ifndef PLCEND
testpeers$(1).run: testpeers.$(1).test_all.out
testpeers$(1).all: db-clean.3 testpeers.$(1).test_all.out
testpeers$(1).diff: testpeers.$(1).test_all.diff
testpeers$(1).ckp: testpeers.$(1).test_all.ckp
endif
endef

$(foreach size,$(SIZES),$(eval $(call testpeers_shortcut,$(size))))

testpeers.help:
	@echo "Available sizes" $(SIZES)
	@echo "testpeers targets"	
	@echo -e "testpeers-n.run\t\truns the test"
	@echo -e "testpeers-b.all\t\tcleans the db and former test results, runs the full test"
	@echo -e "testpeers-m.run\t\truns the actual test after both plcs were inited"
	@echo -e "testpeers-h.restore\t\trestores both plcs as if just inited"
	@echo -e "testpeers-n.ckp\t\tcheckpoints out files as references"
	@echo -e "testpeers-n.diff\t\tcompares out files against reference"


####################
RUN += api
api:
	$(CHROOT) /usr/bin/plcsh
RUN += sql
sql:
	$(CHROOT) psql -U pgsqluser planetlab4
RUN += log
log:
	emacs /plc/data/var/log/httpd/error_log /plc/data/var/log/boot.log

PHONIES += $(RUN)


$(foreach phony,$(PHONIES),$(eval $(call ssh_phony_target,$(phony))))

#######
help: testpeers.help populate.help 
	@echo "===================="
	@echo "other known targets:"
	@echo "db family:" $(DB) 
	@echo -e "e.g.\tmake db-clean.3"
	@echo "push:" $(PUSH) 
	@echo "peers:" $(PEERS)
	@echo "===================="
	@echo "For running on plc1, on plc2, or both:"
	@echo -e "\t make <target>.1 <target>.2 <target.3>"
	@echo "For running in a chroot jail"
	@echo -e "\t make <target>.chroot"
	@echo "So for running on both nodes chroots"
	@echo -e "\t make <target>.chroot.3"
	@echo "for running TestPeers : testpeers=<args separated by +>.out"
	@echo -e "\t e.g. make testpeers.-m.test_all"
	@echo -e "\t e.g. make testpeers.-h.-1.populate"
	@echo "comparing run with reference : testpeers.<args separated by .>.diff"
	@echo "adopt run as reference : testpeers.<args separated by .>.ckp"
	@echo -e "\t e.g. make testpeers.-m.test_all"
	@echo -e "\t e.g. make testpeers.-h.-1.populate"
	@echo "===================="
	@echo "Supported size variants:" $(SIZES)
	@echo "Supported plc ids:" $(PLCS)
	@echo "snapshotting the DB : " $(DB-SQL) $(DB-RESTORE)
	@echo "===================="
	@echo "upgrade:" $(UPGRADE)
	@echo "run family (convenience):" $(RUN)
	@echo "OTHERS:" $(HELP)


#################### convenience, for debugging only
# make +foo : prints the value of $(foo)
# make ++foo : idem but verbose, i.e. foo=$(foo)
++%: varname=$(subst +,,$@)
++%:
	@echo "$(varname)=$($(varname))"
+%: varname=$(subst +,,$@)
+%:
	@echo "$($(varname))"

