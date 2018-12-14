#!/usr/bin/make -f
MAIN_de := handbuch-4.4
MAIN_en := manual-4.4
MAIN := $(MAIN_de) $(MAIN_en)
STYLESHEET := univention
handbuch%: lang := de

COMMON_DIR ?= ../doc-common

SOURCES_de := $(shell find . $(COMMON_DIR)/stylesheets -name \*-de.xml -o -name \*-de.ent -o -name \*.xsl)
SOURCES_en := $(shell find . $(COMMON_DIR)/stylesheets -name \*-en.xml -o -name \*-en.ent -o -name \*.xsl)

include $(COMMON_DIR)/Makefile
