#!/usr/bin/make -f
MAIN_de := bestpractice-de
MAIN_en := bestpractice-en
MAIN := $(MAIN_de) $(MAIN_en)
STYLESHEET := univention
bestpractice-de%: lang := de

COMMON_DIR := ../../../doc-common/docbook
include $(COMMON_DIR)/Makefile

SOURCES_de := $(shell find . $(COMMON_DIR)/stylesheets -name \*-de.xml -o -name \*-de.ent -o -name \*.xsl)
SOURCES_en := $(shell find . $(COMMON_DIR)/stylesheets -name \*-en.xml -o -name \*-en.ent -o -name \*.xsl)
IMAGES := $(shell find . $(COMMON_DIR)/stylesheets -name \*.png -o -name \*.jpg)

$(addsuffix .epub,$(MAIN_de)): %.epub: $(SOURCES_de)
$(addsuffix .epub,$(MAIN_en)): %.epub: $(SOURCES_en)

$(addsuffix .html,$(MAIN_de)): %.html: $(SOURCES_de)
$(addsuffix .html,$(MAIN_en)): %.html: $(SOURCES_en)

$(addsuffix .fo,$(MAIN_de)): %.fo: $(SOURCES_de)
$(addsuffix .fo,$(MAIN_en)): %.fo: $(SOURCES_en)

$(addsuffix .xml.err,$(MAIN_de)): %.xml.err: $(SOURCES_de)
$(addsuffix .xml.err,$(MAIN_en)): %.xml.err: $(SOURCES_en)
