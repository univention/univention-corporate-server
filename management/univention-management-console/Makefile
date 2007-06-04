DESTDIR=/tmp/foo
FRONTEND=$(shell find modules/frontend -name '*.py' | sed 's/\.py/\.pyo/g')
MODULES=$(shell find modules/univention -name '*.py' | sed 's/\.py/\.pyo/g')
IMAGES=$(shell find images -name '*.gif')
MO_FILES_ADMIN=$(shell find admin-modules -name '*.po' | sed 's/\.po/\.mo/g')
MO_FILES_BACKEND=$(shell find modules/univention -name '*.po' | sed 's/\.po/\.mo/g')
MO_FILES_FRONTEND=$(shell find modules/frontend -maxdepth 1 -name '*.po' | sed 's/\.po/\.mo/g')

%.pyo:	%.py
	@./univention-pycompile $< $@

%.mo:	%.po
	msgfmt -o $@ $<

all:	$(FRONTEND) $(MODULES) $(MO_FILES_BACKEND) $(MO_FILES_FRONTEND) $(MO_FILES_ADMIN)

frontend: $(FRONTEND)

modules: $(MODULES)

clean:
	@find admin-modules -name '*.pyo' -exec rm \{\} \;
	@find modules/frontend -name '*.pyo' -exec rm \{\} \;
	@find modules/univention -name '*.pyo' -exec rm \{\} \;
	@find modules/frontend -name '*.pyo.pp' -exec rm \{\} \;
	@find modules/univention -name '*.pyo.pp' -exec rm \{\} \;
	@find modules/ -name '*.mo' -exec rm \{\} \;


install-frontend: frontend
	install -d $(DESTDIR)/usr/share/univention-management-console
	@for i in $(FRONTEND); do\
		o=$(DESTDIR)/usr/share/univention-management-console/frontend/$${i#modules/frontend};\
		install -d "`dirname $$o`";\
		install -m755 $$i $$o;\
	done

install-modules: modules
	@for i in $(MODULES); do\
                o=$(DESTDIR)/usr/lib/python2.4/site-packages/$${i#modules};\
                install -d "`dirname $$o`";\
                install -m755 $$i $$o;\
        done

install-images:
	@for i in $(IMAGES); do\
                o=$(DESTDIR)/usr/share/univention-management-console/www/themes/$$i;\
                install -d "`dirname $$o`";\
                install -m755 $$i $$o;\
        done

install-locales-admin: $(MO_FILES_ADMIN)
	@for i in $(MO_FILES_ADMIN); do\
		lang=`basename $$i .mo`;\
		name=`echo $$i | sed 's,admin-modules/,,;s,/.*\.mo,,'`;\
		o=$(DESTDIR)/usr/share/locale/$$lang/LC_MESSAGES/univention-admin-handlers-$$name-umc.mo;\
		install -d "`dirname $$o`";\
		install -m 644 $$i $$o;\
	done

install-locales-frontend: $(MO_FILES_FRONTEND)
	@for i in $(MO_FILES_FRONTEND); do\
		lang=`basename $$i .mo`;\
		o=$(DESTDIR)/usr/share/locale/$$lang/LC_MESSAGES/univention-management-console-frontend.mo;\
		install -d "`dirname $$o`";\
		install -m 644 $$i $$o;\
	done

install-locales-backend: $(MO_FILES_BACKEND)
	@for i in $(MO_FILES_BACKEND); do\
		lang=`basename $$i .mo`;\
		domain=`dirname $$i | sed 's,^modules/,,;s,/,-,g'`;\
		o=$(DESTDIR)/usr/share/locale/$$lang/LC_MESSAGES/$$domain.mo;\
		install -d "`dirname $$o`";\
		install -m 644 $$i $$o;\
	done
