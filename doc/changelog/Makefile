#!/usr/bin/make -f
MAIN := release-notes-3.2-en release-notes-3.2-de
STYLESHEET := univention_extdocs

COMMON_DIR := ../../../doc-common/docbook
include $(COMMON_DIR)/Makefile

$(addsuffix .epub,$(MAIN)): %.epub: $(SOURCES)
$(addsuffix .html,$(MAIN)): %.html: $(SOURCES)
$(addsuffix .fo,$(MAIN)): %.fo: $(SOURCES)
