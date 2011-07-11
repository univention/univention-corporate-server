MODULES=$(shell find modules/univention/management -name '*.py')
MO_FILES_BACKEND=$(shell find modules/univention/management -name '*.po' | sed 's/\.po/\.mo/g')
IMAGES=$(shell find images -name '*.gif' -o -name '*.png')

MODULENAME=$(PACKAGE:univention-management-console-%=%)

%.mo:	%.po
	msgfmt -o $@ $<

all:	$(MO_FILES_ADMIN) $(MODULES) $(MO_FILES_BACKEND) 

install-locales-admin: $(MO_FILES_ADMIN)
	@for i in $(MO_FILES_ADMIN); do\
		domain=`dirname $$i | sed 's,^modules/,,;s,/,-,g'`-$(MODULENAME);\
		o=debian/$(PACKAGE)/usr/share/locale/$(LANGUAGE)/LC_MESSAGES/$$domain.mo;\
		install -d "`dirname $$o`";\
		install -m 644 $$i $$o;\
	done

clean:
	@find modules/ -name '*.mo' -exec rm \{\} \;

install-modules: $(MODULES)
	install -d debian/$(PACKAGE)/usr/share/pyshared
	@for i in $(MODULES); do\
		o=debian/$(PACKAGE)/usr/share/pyshared/$${i#modules};\
		install -d "`dirname $$o`";\
		install -m755 $$i $$o;\
	done

install-images: $(IMAGES)
	@for i in $(IMAGES); do\
		o=debian/$(PACKAGE)/usr/share/univention-management-console/www/themes/$$i;\
		install -d "`dirname $$o`";\
		install -m755 $$i $$o;\
	done

install-locales-backend: $(MO_FILES_BACKEND)
	@for i in $(MO_FILES_BACKEND); do\
		lang=`basename $$i .mo`;\
		domain=`dirname $$i | sed 's,^modules/,,;s,/,-,g'`;\
		o=debian/$(PACKAGE)/usr/share/locale/$$lang/LC_MESSAGES/$$domain.mo;\
		install -d "`dirname $$o`";\
		install -m 644 $$i $$o;\
	done
