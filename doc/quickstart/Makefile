#!/usr/bin/make -f
MAIN := quickstart-de-4.0 quickstart-en-4.0
STYLESHEET := univention_extdocs
quickstart-de%: lang := de

COMMON_DIR := ../../../doc-common/docbook
include $(COMMON_DIR)/Makefile

$(addsuffix .epub,$(MAIN)): %.epub: $(SOURCES)
$(addsuffix .html,$(MAIN)): %.html: $(SOURCES)
$(addsuffix .fo,$(MAIN)): %.fo: $(SOURCES)
$(addsuffix .xml.err,$(MAIN)): %.xml.err: $(SOURCES)
