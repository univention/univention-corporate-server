#!/usr/bin/make -f
MAIN_en := app-provider-4.4
MAIN := $(MAIN_en)
STYLESHEET := univention

COMMON_DIR ?= ../doc-common

SOURCES_en := $(shell find . $(COMMON_DIR)/stylesheets -name \*-en.xml -o -name \*-en.ent -o -name \*.xsl)
IMAGES := $(shell find . $(COMMON_DIR)/stylesheets -name \*.png -o -name \*.jpg)

include $(COMMON_DIR)/Makefile
