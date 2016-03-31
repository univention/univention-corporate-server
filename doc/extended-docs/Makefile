#!/usr/bin/make -f
MAIN := installation-3.3 performance-guide-3.3 networks-3.3 printers-3.3
MAIN += domain-3.3 windows-3.3 uvmm-3.3
STYLESHEET := univention_extdocs

COMMON_DIR := ../../../doc-common/docbook
include $(COMMON_DIR)/Makefile

$(addsuffix .epub,$(MAIN)): %.epub: $(SOURCES)
$(addsuffix .html,$(MAIN)): %.html: $(SOURCES)
$(addsuffix .fo,$(MAIN)): %.fo: $(SOURCES)
