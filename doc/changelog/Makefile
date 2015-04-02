#!/usr/bin/make -f
MAIN := release-notes-4.0-1-en release-notes-4.0-1-de
STYLESHEET := univention_extdocs
OPTIONS += --stringparam ulink.show 0
release-notes-4.0-1-de%: lang := de

COMMON_DIR := ../../../doc-common/docbook
include $(COMMON_DIR)/Makefile

check:: $(addsuffix .xml,$(MAIN))
	XML_CATALOG_FILES="$(subst $(SPACE),%20,$(XML_CATALOG_FILES))" \
	xsltproc --xinclude "$(COMMON_DIR)/stylesheets/check-bug.xsl" $^
