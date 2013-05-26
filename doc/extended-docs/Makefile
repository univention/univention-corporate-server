#!/usr/bin/make -f
MAIN := installation-3.1 performance-guide-3.1 computers-3.1 networks-3.1
STYLESHEET := univention_extdocs

COMMON_DIR := ../../../doc-common/docbook
include $(COMMON_DIR)/Makefile

$(addsuffix .epub,$(MAIN)): %.epub: $(SOURCES)
$(addsuffix .html,$(MAIN)): %.html: $(SOURCES)
$(addsuffix .fo,$(MAIN)): %.fo: $(SOURCES)
