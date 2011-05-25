#!/usr/bin/make -f

jsFiles=$(shell find umc -name "*.js")
pkgdir=/usr/share/univention-management-console-frontend/
.PHONY: all install jslint test_jslint build

jslint: 
	jslint $(jsFiles)

test_jslint:
	@echo "running jslint to make sure that there are no problems"
	@LINT=$$(/usr/bin/jslint $(jsFiles) | grep -v "Unsafe character"); \
	[ -z "$$LINT" ] || (echo -e "jslint found errors:\n$$LINT"; false)

all: build install

build: test_jslint
	@# make temporary directories for umc and css
	@#TODO: this should be done with an Apache redirection
	for idir in umc css; do \
		find . -maxdepth 1 -type l -a -name "$${idir}_*" -delete; \
		ln -s $$idir "$${idir}_$$(date +'%Y%d%m%H%M%S')"; \
	done;
	@#./build.sh profileFile=../../../univention.profile.js action=release releaseDir=${D}${INSTDIR} version=${DOJO_VERSION} releaseName='' localeList="de-de,en-us" optimize=shrinksafe.keepLines layerOptimize=shrinksafe cssOptimize=comments.keepLines copyTests=false # mini=true # cssImportIgnore=../dijit.css

clean:
	rm -f umc_* css_*

install:
	@# directories
	for i in $$(find umc css images -type d | grep -v '.svn'); do \
		install -m 0755 -d "$(DESTDIR)$(pkgdir)$$i"; \
	done
	@# js, css, and image files
	for i in $$(find umc css images -type f -name "*.js" -o -name "*.css" -o -name "*.png" -o -name "*.jpg" -o -name "*.gif"); do \
		install -m 0644 "$$i" "$(DESTDIR)$(pkgdir)$$i"; \
	done
	@# index page
	install -m 0644 "index.php" "$(DESTDIR)$(pkgdir)index.php"; \
	
