#!/usr/bin/make -f
MAIN := installation-3.1 performance-guide-3.1 computers-3.1 networks-3.1

STYLESHEETS_DIR := /usr/share/xml/docbook/stylesheet

SOURCES := $(shell find . ../stylesheets -name \*.xml -o -name \*.ent -o -name \*.xsl)
IMAGES := $(shell find . ../stylesheets -name \*.png -o -name \*.jpg)

.PHONY: all
all: html pdf export

.PHONY: epub
epub: $(addsuffix .epub,$(MAIN))
%.epub: %.xml $(SOURCES) $(IMAGES)
	dbtoepub $< -o $@

.PHONY: html
html: $(addsuffix .html,$(MAIN))
%.html: %.xml $(SOURCES)
	xsltproc -o $@ $(OPTIONS) ../stylesheets/univention_extdocs_html.xsl $<

.PHONY: fo
fo: $(addsuffix .fo,$(MAIN))
%.fo: %.xml $(SOURCES)
	xsltproc -o $@ $(OPTIONS) ../stylesheets/univention_extdocs_fo.xsl $<

.PHONY: pdf
pdf: $(addsuffix .pdf,$(MAIN))
%.pdf: %.fo $(IMAGES)
	fop -pdf $@ -fo $<

.PHONY: export
export: pdf html
	install -m755 -d ../webroot
	install -m755 -d ../webroot/illustrations
	install -m644 -t ../webroot/illustrations illustrations/*.jpg illustrations/*.svg
	install -m644 -t ../webroot *.pdf
	install -m644 -t ../webroot *.html
	cp -d symlinks/* ../webroot

.PHONY: clean
clean:
	$(RM) $(addsuffix .epub,$(MAIN))
	$(RM) $(addsuffix .html,$(MAIN))
	$(RM) $(addsuffix .fo,$(MAIN))
	$(RM) $(addsuffix .pdf,$(MAIN))
	$(RM) $(patsubst %,../webroot/%.html,$(MAIN))

.PHONY: check
check: $(addsuffix .xml,$(MAIN))
	xmllint --noout --valid $^
