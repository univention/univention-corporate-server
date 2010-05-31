#!/usr/bin/make -f

VERSION := $(shell dpkg-parsechangelog | sed -ne 's/^Version: //p')
UVMM := univention-virtual-machine-manager

MODULES=$(shell find umc/modules/univention/management -name '*.py')
PO_FILES := $(shell find umc/modules/univention/management src -name '*.po')
MO_FILES := $(PO_FILES:%.po=%.mo)
IMAGES=$(shell find umc/images -name '*.gif' -o -name '*.png')
MODULENAME=uvmm

%.mo:	%.po
	msgfmt --check --output-file $@ $<

.PHONY: all
all: $(MO_FILES)

.PHONY: install
install:: install-modules install-locales install-images
	install -m 0755 -d $(DESTDIR)/etc/univention
	install -m 0755 -t $(DESTDIR)/etc/univention src/uvmmd.ini
	install -m 0755 -d $(DESTDIR)/usr/share/pyshared/univention/uvmm
	install -m 0644 -t $(DESTDIR)/usr/share/pyshared/univention/uvmm src/univention/uvmm/*.py
	install -m 0755 -d $(DESTDIR)/usr/sbin
	install -m 0755 -t $(DESTDIR)/usr/sbin src/univention-virtual-machine-manager-daemon
	install -m 0755 -t $(DESTDIR)/usr/sbin src/univention-virtual-machine-manager
	ln -s univention-virtual-machine-manager $(DESTDIR)/usr/sbin/uvmm

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

.PHONY: clean
clean::
	find -name \*.pyc -exec $(RM) {} +
	$(RM) src/virtual-machine-manager-daemon.log
	$(RM) $(MO_FILES)

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

ifeq ($(M),1)
LANGUAGES := de
DIRS := src umc/modules/univention/management/console/handlers/uvmm

.PHONY: maintainer-locales
maintainer-locales: $(foreach d,$(DIRS),$(d)/messages.pot)
maintainer-locales: $(foreach d,$(DIRS),$(foreach l,$(LANGUAGES),$(d)/$(l).po))

define I18N_template
 %/$(1).po: %/messages.pot
	msgmerge --update --sort-output $$@ $$<
endef
$(foreach lang,$(LANGUAGES),$(eval $(call I18N_template,$(lang))))

umc/modules/univention/management/console/handlers/uvmm/messages.pot: $(shell find umc/modules/univention/management/console/handlers/uvmm -name \*.py)

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

clean::
	$(RM) $(foreach d,$(DIRS),$(d)/messages.pot)
endif
