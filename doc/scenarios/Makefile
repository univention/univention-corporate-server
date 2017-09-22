#!/usr/bin/make -f
MAIN_de := scenarios-de
MAIN_en := scenarios-en
MAIN := $(MAIN_de) $(MAIN_en)
STYLESHEET := univention
scenarios-de%: lang := de

COMMON_DIR ?= ../doc-common

SOURCES_de := $(shell find . $(COMMON_DIR)/stylesheets -name \*-de.xml -o -name \*-de.ent -o -name \*.xsl)
SOURCES_en := $(shell find . $(COMMON_DIR)/stylesheets -name \*-en.xml -o -name \*-en.ent -o -name \*.xsl)
IMAGES := $(shell find . $(COMMON_DIR)/stylesheets -name \*.png -o -name \*.jpg)

include $(COMMON_DIR)/Makefile
