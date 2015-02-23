#!/usr/bin/make -f
MAIN := release-notes-4.0-1-en release-notes-4.0-1-de
STYLESHEET := univention_extdocs
OPTIONS += --stringparam ulink.show 0

COMMON_DIR := ../../../doc-common/docbook
include $(COMMON_DIR)/Makefile

$(addsuffix .epub,$(MAIN)): %.epub: $(SOURCES)
$(addsuffix .html,$(MAIN)): %.html: $(SOURCES)
$(addsuffix .fo,$(MAIN)): %.fo: $(SOURCES)
$(addsuffix .xml.err,$(MAIN)): %.xml.err: $(SOURCES)

check:: $(addsuffix .xml,$(MAIN))
	XML_CATALOG_FILES="$(COMMON_DIR)/catalog.xml" \
	xsltproc --xinclude $(COMMON_DIR)/stylesheets/check-bug.xsl $^
