DESTDIR=debian/tmp/
FRONTEND=$(shell find modules/frontend -name '*.py')
MODULES=$(shell find modules/univention -name '*.py')
IMAGES=$(shell find images -name '*.gif' -o -name '*.png')
MO_FILES_ADMIN=$(shell find admin-modules -name '*.po' | sed 's/\.po/\.mo/g')
MO_FILES_BACKEND=$(shell find modules/univention -name '*.po' | sed 's/\.po/\.mo/g')
MO_FILES_FRONTEND=$(shell find modules/frontend -maxdepth 1 -name '*.po' | sed 's/\.po/\.mo/g')

%.mo:	%.po
	msgfmt -o $@ $<

all:	$(FRONTEND) $(MODULES) $(MO_FILES_BACKEND) $(MO_FILES_FRONTEND)

frontend: $(FRONTEND)

modules: $(MODULES)

admin-modules: $(ADMIN_MODULES)

clean:
	@find modules/ -name '*.mo' -exec rm \{\} \;

install-frontend: frontend
	install -d debian/$(PACKAGE)/usr/share/univention-management-console
	@for i in $(FRONTEND); do\
		o=debian/$(PACKAGE)/usr/share/univention-management-console/frontend/$${i#modules/frontend};\
		install -d "`dirname $$o`";\
		install -m755 $$i $$o;\
	done

install-modules: modules
	install -d debian/$(PACKAGE)/usr/share/pyshared/
	@for i in $(MODULES); do\
		o=debian/$(PACKAGE)/usr/share/pyshared/$${i#modules};\
		install -d "`dirname $$o`";\
		install -m755 $$i $$o;\
	done

install-images:
	@for i in $(IMAGES); do\
		o=debian/$(PACKAGE)/usr/share/univention-management-console/www/themes/$$i;\
		install -d "`dirname $$o`";\
		install -m755 $$i $$o;\
	done

install-locales-frontend: $(MO_FILES_FRONTEND)
	@for i in $(MO_FILES_FRONTEND); do\
		lang=`basename $$i .mo`;\
		o=debian/$(PACKAGE)/usr/share/locale/$$lang/LC_MESSAGES/univention-management-console-frontend.mo;\
		install -d "`dirname $$o`";\
		install -m 644 $$i $$o;\
	done

install-locales-backend: $(MO_FILES_BACKEND)
	@for i in $(MO_FILES_BACKEND); do\
		lang=`basename $$i .mo`;\
		domain=`dirname $$i | sed 's,^modules/,,;s,/,-,g'`;\
		o=debian/$(PACKAGE)/usr/share/locale/$$lang/LC_MESSAGES/$$domain.mo;\
		install -d "`dirname $$o`";\
		install -m 644 $$i $$o;\
	done
