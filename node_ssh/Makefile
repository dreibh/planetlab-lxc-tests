CODE = nst.py

CONFIG = nst_config

SSH_CONFIG = ssh_config

CRON = nst.cron

CROND = /etc/init.d/crond
 
APPS = nst

datadir := /usr/share
vardir := /var/lib
appdir := /planetlab/tests/node-ssh

all: $(APPS)

nst: $(CODE) config cron data
	install -D -m 755 nst.py $(datadir)/$(appdir)/$(CODE)

	# create symlink to executable	
	ln -s $(datadir)/$(appdir)/$(CODE) /usr/bin/nst

cron: $(CRON)
	install -D -m 644 $(CRON) /etc/cron.d/$(CRON)
	
	# restart cron
	$(CROND) restart

config: $(CONFIG)
	install -D -m 640 $(CONFIG) $(datadir)/$(appdir)/$(CONFIG)
	install -D -m 644 $(SSH_CONFIG) /root/.ssh/config

data:
	install -d -m 755 $(vardir)/$(appdir)/plots/	
	install -d -m 755 $(vardir)/$(appdir)/data/

cleandata:
	rm -Rf $(vardir)/$(appdir)

clean: cleandata
	rm -Rf $(datadir)/$(appdir)
	rm -rf /usr/bin/nst
	rm -rf /root/.ssh/config
	rm -rf /etc/cron.d/$(CRON)
	$(CROND) restart

.PHONY: clean data config cron nst
