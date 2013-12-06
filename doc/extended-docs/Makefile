#!/usr/bin/make -f
MAIN := installation-3.2 performance-guide-3.2 networks-3.2 printers-3.2 computers-3.2
MAIN += domain-3.2 windows-3.2 uvmm-3.2
STYLESHEET := univention_extdocs

COMMON_DIR := ../../../doc-common/docbook
include $(COMMON_DIR)/Makefile

$(addsuffix .epub,$(MAIN)): %.epub: $(SOURCES)
$(addsuffix .html,$(MAIN)): %.html: $(SOURCES)
$(addsuffix .fo,$(MAIN)): %.fo: $(SOURCES)
