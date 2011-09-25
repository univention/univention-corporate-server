#!/usr/bin/make -f

VERSION := $(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')
UVMM := univention-virtual-machine-manager

MODULES := $(shell find umc/modules/univention/management -name '*.py')
PO_FILES := $(shell find umc/modules/univention/management src -name '*.po')
MO_FILES := $(PO_FILES:%.po=%.mo)
IMAGES := $(shell find umc/images -name '*.gif' -o -name '*.png')
MODULENAME=uvmm

.PHONY: all
all:: $(MO_FILES) $(IMAGES)

%.mo:	%.po
	msgfmt --check --output-file $@ $<

.PHONY: install
install:: install-modules install-locales install-images
	install -m 0755 -d $(DESTDIR)/etc/univention
	install -m 0755 -t $(DESTDIR)/etc/univention src/uvmmd.ini
	install -m 0755 -d $(DESTDIR)/usr/share/pyshared/univention/uvmm
	install -m 0644 -t $(DESTDIR)/usr/share/pyshared/univention/uvmm src/univention/uvmm/*.py
	install -m 0755 -d $(DESTDIR)/usr/sbin
	install -m 0755 -t $(DESTDIR)/usr/sbin src/univention-virtual-machine-manager-daemon
	install -m 0755 -t $(DESTDIR)/usr/sbin src/univention-virtual-machine-manager
	$(RM) $(DESTDIR)/usr/sbin/uvmm
	ln -s univention-virtual-machine-manager $(DESTDIR)/usr/sbin/uvmm
	install -m 0755 -d $(DESTDIR)/var/www
	install -m 0444 -t $(DESTDIR)/var/www TightVncViewer.jar
	install -m 0755 -d $(DESTDIR)/usr/share/man/man8
	install -m 0755 -d $(DESTDIR)/usr/lib/univention-virtual-machine-manager-daemon
	install -m 0755 -t $(DESTDIR)/usr/lib/univention-virtual-machine-manager-daemon uvmmd-check.sh
	install -m 0644 -t $(DESTDIR)/usr/share/man/man8 doc/*.8
	install -m 0755 -d $(DESTDIR)/usr/lib/univention-directory-listener/system
	install -m 0644 -t $(DESTDIR)/usr/lib/univention-directory-listener/system uvmmd-nodes.py
	install -m 0644 -t $(DESTDIR)/usr/lib/univention-directory-listener/system uvmmd-ldap.py
	install -m 0755 -d $(DESTDIR)/usr/lib/univention-install
	install -m 0755 -t $(DESTDIR)/usr/lib/univention-install 44univention-virtual-machine-manager-daemon.inst
	install -m 0755 -d $(DESTDIR)/etc/runit/univention-virtual-machine-manager-daemon
	install -m 0755 univention-virtual-machine-manager-daemon.runit $(DESTDIR)/etc/runit/univention-virtual-machine-manager-daemon/run

.PHONY: uninstall
uninstall:
	$(RM) $(DESTDIR)/usr/sbin/univention-virtual-machine-manager
	$(RM) $(DESTDIR)/usr/sbin/uvmm
	$(RM) $(DESTDIR)/usr/sbin/univention-virtual-machine-manager-daemon
	-rmdir -p $(DESTDIR)/usr/sbin
	$(RM) $(DESTDIR)/usr/share/pyshared/univention/uvmm/*
	-rmdir -p $(DESTDIR)/usr/share/pyshared/univention/uvmm
	$(RM) $(DESTDIR)/etc/univention/uvmmd.ini
	-rmdir -p $(DESTDIR)/etc/univention
	$(RM) $(DESTDIR)/var/www/TightVncViewer.jar
	-rmdir -p $(DESTDIR)/var/www
	$(RM) $(DESTDIR)/usr/lib/univention-virtual-machine-manager-daemon/uvmmd-check.sh
	-rmdir -p $(DESTDIR)/usr/lib/univention-virtual-machine-manager-daemon
	$(RM) $(DESTDIR)/usr/lib/univention-directory-listener/system/uvmmd-nodes.py
	$(RM) $(DESTDIR)/usr/lib/univention-directory-listener/system/uvmmd-ldap.py
	-rmdir -p $(DESTDIR)/usr/lib/univention-directory-listener/system
	$(RM) $(DESTDIR)/usr/lib/univention-install/44univention-virtual-machine-manager-daemon.inst
	-rmdir -p $(DESTDIR)/usr/lib/univention-install
	$(RM) $(DESTDIR)/etc/runit/univention-virtual-machine-manager-daemon/run
	-rmdir -p $(DESTDIR)/etc/runit/univention-virtual-machine-manager-daemon

.PHONY: clean
clean::
	find -name \*.pyc -exec $(RM) {} +
	$(RM) src/virtual-machine-manager-daemon.log
	$(RM) $(MO_FILES)
	$(RM) tags

.PHONY: modules
modules: $(MODULES)

.PHONY: install-modules
install-modules: modules
	install -d $(DESTDIR)/usr/share/pyshared/univention/management/console/handlers/$(MODULENAME)
	install -m 0644 -t $(DESTDIR)/usr/share/pyshared/univention/management/console/handlers/$(MODULENAME) umc/modules/univention/management/console/handlers/$(MODULENAME)/*.py

.PHONY: install-images
install-images: $(IMAGES)
	for i in $^; do\
		dest=`dirname $$i | sed 's,^umc/,,'`;\
		o=$(DESTDIR)/usr/share/univention-management-console/www/themes/$$dest;\
		install -d "$$o";\
		install -m 0644 $$i $$o;\
	done

.PHONY: install-locales
install-locales: $(MO_FILES)
	for i in $(filter umc/modules/%,$^); do\
		lang=`basename $$i .mo`;\
		domain=`dirname $$i | sed 's,^umc/modules/,,;s,/,-,g'`;\
		o=$(DESTDIR)/usr/share/locale/$$lang/LC_MESSAGES/$$domain.mo;\
		install -d "`dirname $$o`";\
		install -m 644 $$i $$o;\
	done
	for i in $(filter src/%,$^); do\
		lang=`basename $$i .mo`;\
		o=$(DESTDIR)/usr/share/locale/$$lang/LC_MESSAGES/$(UVMM).mo;\
		install -d "`dirname $$o`";\
		install -m 644 $$i $$o;\
	done

DIRS := src umc/modules/univention/management/console/handlers/$(MODULENAME)
clean::
	$(RM) $(foreach d,$(DIRS),$(d)/messages.pot)

ifeq ($(M),1)
LANGUAGES := de

.PHONY: maintainer-locales
maintainer-locales: $(foreach d,$(DIRS),$(d)/messages.pot)
maintainer-locales: $(foreach d,$(DIRS),$(foreach l,$(LANGUAGES),$(d)/$(l).po))

define I18N_template
 %/$(1).po: %/messages.pot
	msgmerge --update --sort-output $$@ $$<
endef
$(foreach lang,$(LANGUAGES),$(eval $(call I18N_template,$(lang))))

umc/modules/univention/management/console/handlers/$(MODULENAME)/messages.pot: $(shell find umc/modules/univention/management/console/handlers/$(MODULENAME) -name \*.py)

src/messages.pot: src/univention-virtual-machine-manager
src/messages.pot: src/univention-virtual-machine-manager-daemon
src/messages.pot: $(shell find src/univention/uvmm -name \*.py)

%/messages.pot:
	xgettext --output=$(@) \
		--language=Python \
		--keyword=N_:1 \
		--sort-output \
		--package-name=$(UVMM) \
		--package-version=$(VERSION) \
		--msgid-bugs-address="packages@univention.de" \
		--copyright-holder="Univention GmbH" \
		$^


IMAGES_12 := domain group node
IMAGES_16 := add domain-off domain-on domain-paused domain group node node-off refresh
IMAGES_64 := module

SIZES := 12 16 24 64
FORMATS := png gif

IMAGES := $(foreach format,$(FORMATS),$(foreach size,$(SIZES),$(foreach img,$(IMAGES_$(size)),umc/images/default/$(size)x$(size)/$(MODULENAME)/$(img).$(format))))
all:: $(IMAGES)

define CONVERT_template
 umc/images/default/$(1)x$(1)/%.png: umc/images/default/scalable/%.svg
	inkscape -w $(1) -h $(1) -f $$< -e $$@
endef
$(foreach size,$(SIZES),$(eval $(call CONVERT_template,$(size))))

%.gif: %.png
	convert $< $@

endif

tags: $(shell find src umc -name \*.py)
	ctags-exuberant -o $@ $^
