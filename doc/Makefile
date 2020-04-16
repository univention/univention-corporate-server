#!/usr/bin/make -f
GREP := $(SHELL) -c '! grep -n "$$0" "$$@"'
FGREP := $(SHELL) -c '! grep -n -F "$$0" "$$@"'
Q := @
DIRS := $(filter-out doc-common/,$(dir $(wildcard */Makefile)))

.PHONY: fast
fast::
	${Q}find -name doc-common -prune -o \
		\( -name \*-de.xml -exec $(FGREP) '/macros-en.ent' {} + -o -true \) -o \
		\( -name \*.xml -exec $(FGREP) '/macros-de.ent' {} + \)
fast::
	${Q}find -mindepth 1 -maxdepth 2 -name doc-common -prune -o -name \*.xml -exec $(FGREP) '"../../stylesheets/' {} +
fast::
	${Q}find -mindepth 3 -maxdepth 3 -name \*.xml -exec $(FGREP) '"../stylesheets/' {} +
fast::
	${Q}find -name doc-common -prune -o -name \*.xml -exec $(FGREP) 'https\?://forge.univention.org/bugzilla/show_bug.cgi' {} +
fast::
	${Q}find -name doc-common -prune -o -name \*.xml -exec $(GREP) 'url="https\?://sdb.univention.de/[1-9]' {} +
fast::
	${Q}find */illustrations?? -type f -printf '%f\n' | sort | uniq -d

check: fast

%:
	for d in $(DIRS);do make -C "$$d" $@; done
# vim:set bkc=auto:
