CODE = nst.py

CONFIG = nst_config

CRON = nst.cron

CROND = /etc/init.d/crond
 
APPS = nst

datadir := /usr/share
appdir := /planetlab/tests/nst

all: $(APPS)

nst: $(CODE) $(CONFIG) $(CRON) data
	install -D -m 755 nst.py $(datadir)/$(appdir)/$(CODE)
	install -D -m 750 nst_config $(datadir)/$(appdir)/$(CONFIG)
	install -D -m 755 nst.cron /etc/cron.d/$(CRON)

	# create symlink to executable	
	ln -s $(datadir)/$(appdir)/$(CODE) /usr/bin/nst

        # reload cron
	$(CROND) restart


data:
	install -d -m 755 $(datadir)/$(appdir)/plots/	
	install -d -m 755 $(datadir)/$(appdir)/data/
clean:
	rm -Rf $(datadir)/$(appdir)
	rm -rf /etc/cron.d/$(CRON)
	rm -rf /usr/bin/nst

	$(CROND) restart

.PHONY: clean data
