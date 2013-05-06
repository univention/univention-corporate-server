#!/usr/bin/make -f
MAIN_de := scenarios-de
MAIN_en := scenarios-en
MAIN := $(MAIN_de) $(MAIN_en)

STYLESHEETS_DIR := /usr/share/xml/docbook/stylesheet

SOURCES_de := $(shell find . ../stylesheets -name \*-de.xml -o -name \*-de.ent -o -name \*.xsl)
SOURCES_en := $(shell find . ../stylesheets -name \*-en.xml -o -name \*-en.ent -o -name \*.xsl)
IMAGES := $(shell find . ../stylesheets -name \*.png -o -name \*.jpg)

.PHONY: all
all: html pdf export

.PHONY: epub
epub: $(addsuffix .epub,$(MAIN))
%.epub: %.xml $(IMAGES)
	dbtoepub $< -o $@
$(addsuffix .epub,$(MAIN_de)): %.epub: $(SOURCES_de)
$(addsuffix .epub,$(MAIN_en)): %.epub: $(SOURCES_en)

.PHONY: html
html: $(addsuffix .html,$(MAIN))
%.html: %.xml
	xsltproc \
		--stringparam collect.xref.targets yes \
		--stringparam targets.filename $*.db.tmp \
		--stringparam current.docid $* \
		-o $@ $(OPTIONS) ../stylesheets/univention_html.xsl $<
	if ! diff $@.db $*.db.tmp >/dev/null 2>&1; then mv $*.db.tmp $@.db; else $(RM) $*.db.tmp; fi
$(addsuffix .html,$(MAIN_de)): %.html: $(SOURCES_de)
$(addsuffix .html,$(MAIN_en)): %.html: $(SOURCES_en)

.PHONY: fo
fo: $(addsuffix .fo,$(MAIN))
%.fo: %.xml
	xsltproc \
		--stringparam collect.xref.targets yes \
		--stringparam targets.filename $*.db.tmp \
		--stringparam current.docid $* \
		-o $@ $(OPTIONS) ../stylesheets/univention_fo.xsl $<
	if ! diff $@.db $*.db.tmp >/dev/null 2>&1; then mv $*.db.tmp $@.db; else $(RM) $*.db.tmp; fi
$(addsuffix .fo,$(MAIN_de)): %.fo: $(SOURCES_de)
$(addsuffix .fo,$(MAIN_en)): %.fo: $(SOURCES_en)

.PHONY: pdf
pdf: $(addsuffix .pdf,$(MAIN))
%.pdf: %.fo $(IMAGES)
	fop -pdf $@ -fo $<

.PHONY: export
export: pdf html
	install -m755 -d ../webroot
	install -m755 -d ../webroot/illustrations
	install -m644 -t ../webroot/illustrations illustrations/*.png
	install -m644 -t ../webroot *.pdf
	install -m644 -t ../webroot *.html
#	cp -d symlinks/* ../webroot

.PHONY: clean
clean:
	$(RM) $(addsuffix .epub,$(MAIN))
	$(RM) $(addsuffix .html,$(MAIN))
	$(RM) $(addsuffix .fo,$(MAIN))
	$(RM) $(addsuffix .pdf,$(MAIN))
	$(RM) $(patsubst %,../webroot/%.html,$(MAIN))
	$(RM) -r ../webroot/illustrations
	$(RM) *.db

.PHONY: check
check: $(addsuffix .xml,$(MAIN))
	xmllint --noout --valid $^
