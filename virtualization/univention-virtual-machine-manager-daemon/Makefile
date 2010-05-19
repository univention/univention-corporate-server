#!/usr/bin/make -f

MODULES=$(shell find umc/modules/univention/management -name '*.py')
MO_FILES=$(shell find umc/modules/univention/management -name '*.po' | sed 's/\.po/\.mo/g')
IMAGES=$(shell find umc/images -name '*.gif' -o -name '*.png')
MODULENAME=uvmm

%.mo:	%.po
	msgfmt -o $@ $<

.PHONY: all
all: $(MODULES) $(MO_FILES_BACKEND)

.PHONY: install
install: install-modules install-locales install-images
	install -m 0755 -d $(DESTDIR)/etc/univention
	install -m 0755 -t $(DESTDIR)/etc/univention src/uvmmd.ini
	install -m 0755 -d $(DESTDIR)/usr/share/pyshared/univention/uvmm
	install -m 0644 -t $(DESTDIR)/usr/share/pyshared/univention/uvmm src/univention/uvmm/*.py
	install -m 0755 -d $(DESTDIR)/usr/sbin
	install -m 0755 -t $(DESTDIR)/usr/sbin src/univention-virtual-machine-manager-daemon
	install -m 0755 -t $(DESTDIR)/usr/sbin src/univention-virtual-machine-manager
	ln -s univention-virtual-machine-manager $(DESTDIR)/usr/sbin/uvmm
	ln -s univention-virtual-machine-manager $(DESTDIR)/usr/sbin/uvmm-add
	ln -s univention-virtual-machine-manager $(DESTDIR)/usr/sbin/uvmm-remove
	ln -s univention-virtual-machine-manager $(DESTDIR)/usr/sbin/univention-virtual-machine-manager-add
	ln -s univention-virtual-machine-manager $(DESTDIR)/usr/sbin/univention-virtual-machine-manager-remove

.PHONY: uninstall
uninstall:
	$(RM) $(DESTDIR)/usr/sbin/univention-virtual-machine-manager-add
	$(RM) $(DESTDIR)/usr/sbin/univention-virtual-machine-manager-remove
	$(RM) $(DESTDIR)/usr/sbin/univention-virtual-machine-manager
	$(RM) $(DESTDIR)/usr/sbin/uvmm-add
	$(RM) $(DESTDIR)/usr/sbin/uvmm-remove
	$(RM) $(DESTDIR)/usr/sbin/uvmm 
	$(RM) $(DESTDIR)/usr/sbin/univention-virtual-machine-manager-daemon
	-rmdir -p $(DESTDIR)/usr/sbin
	$(RM) $(DESTDIR)/usr/share/pyshared/univention/uvmm/*
	-rmdir -p $(DESTDIR)/usr/share/pyshared/univention/uvmm
	$(RM) $(DESTDIR)/etc/univention/uvmmd.ini
	-rmdir -p $(DESTDIR)/etc/univention

.PHONY: clean
clean:
	find -name \*.pyc -exec $(RM) {} +
	$(RM) src/virtual-machine-manager-daemon.log
	@find umc/modules/ -name '*.mo' -exec rm \{\} \;

modules: $(MODULES)

clean:

install-modules: modules
	install -d $(DESTDIR)/usr/share/pyshared/univention/management/console/handlers/$(MODULENAME)
	install -m 0644 -t $(DESTDIR)/usr/share/pyshared/univention/management/console/handlers/$(MODULENAME) umc/modules/univention/management/console/handlers/$(MODULENAME)/*.py

install-images:
	for i in $(IMAGES); do\
		dest=`dirname $$i | sed 's,^umc/,,'`;\
		o=$(DESTDIR)/usr/share/univention-management-console/www/themes/$$dest;\
		install -d "$$o";\
		install -m 0644 $$i $$o;\
	done

install-locales: $(MO_FILES)
	@for i in $(MO_FILES); do\
		lang=`basename $$i .mo`;\
		domain=`dirname $$i | sed 's,^umc/modules/,,;s,/,-,g'`;\
		o=$(DESTDIR)/usr/share/locale/$$lang/LC_MESSAGES/$$domain.mo;\
		install -d "`dirname $$o`";\
		install -m 644 $$i $$o;\
	done
