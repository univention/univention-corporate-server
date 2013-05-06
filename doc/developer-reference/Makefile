#!/usr/bin/make -f
MAIN := developer-reference-3.1
OPTIONS += --stringparam draft.mode yes
OPTIONS += --stringparam show.comments 0

STYLESHEETS_DIR := /usr/share/xml/docbook/stylesheet

SOURCES := $(shell find . ../stylesheets -name \*.xml -o -name \*.ent -o -name \*.xsl)
IMAGES := $(shell find . ../stylesheets -name \*.png -o -name \*.jpg)

.PHONY: all
all: html pdf

.PHONY: epub
epub: $(addsuffix .epub, $(MAIN))
%.epub: %.xml $(SOURCES) $(IMAGES)
	dbtoepub $< -o $@

# <http://www.sagehill.net/docbookxsl/Olinking.html#LinkBetweenDocs>
%.html.db: %.xml $(SOURCES)
	xsltproc --xinclude \
		--stringparam collect.xref.targets only \
		--stringparam targets.filename $@.tmp \
		../stylesheets/univention_html.xsl $<
	if ! diff $@ $@.tmp >/dev/null 2>&1; then mv $@.tmp $@; else $(RM) $@.tmp; fi
%.fo.db: %.xml $(SOURCES)
	xsltproc --xinclude \
		--stringparam collect.xref.targets only \
		--stringparam targets.filename $@.tmp \
		../stylesheets/univention_fo.xsl $<
	if ! diff $@ $@.tmp >/dev/null 2>&1; then mv $@.tmp $@; else $(RM) $@.tmp; fi

.PHONY: html
html: $(addsuffix .html, $(MAIN))
%.html: %.xml %.html.db $(SOURCES)
	xsltproc --xinclude \
		--stringparam collect.xref.targets yes \
		--stringparam targets.filename $@.db.tmp \
		--stringparam target.database.document olinkdb.xml \
		--stringparam current.docid $* \
		-o $@ $(OPTIONS) ../stylesheets/univention_html.xsl $<
	if ! diff $@.db $@.db.tmp >/dev/null 2>&1; then mv $@.db.tmp $@.db; else $(RM) $@.db.tmp; fi

.PHONY: fo
fo: $(addsuffix .fo, $(MAIN))
%.fo: %.xml %.fo.db $(SOURCES)
	xsltproc --xinclude \
		--stringparam collect.xref.targets yes \
		--stringparam targets.filename $@.db.tmp \
		--stringparam target.database.document olinkdb.xml \
		--stringparam current.docid $* \
		-o $@ $(OPTIONS) ../stylesheets/univention_fo.xsl $<
	if ! diff $@.db $@.db.tmp >/dev/null 2>&1; then mv $@.db.tmp $@.db; else $(RM) $@.db.tmp; fi

.PHONY: pdf
pdf: $(addsuffix .pdf, $(MAIN))
%.pdf: %.fo $(IMAGES)
	fop -pdf $@ -fo $<

.PHONY: export
export: pdf html
	install -m755 -d ../webroot
	if [ -d illustrations ]; then \
	    install -m755 -d ../webroot/illustrations; \
	    install -m644 -t ../webroot/illustrations illustrations/*.jpg; \
	fi
	install -m644 -t ../webroot *.pdf
	install -m644 -t ../webroot *.html
	if [ -d symlinks ]; then \
	    cp -d symlinks/* ../webroot; \
	fi

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
check: $(SOURCES)
	@xmllint -noout -xinclude -postvalid $(MAIN).xml
	@#xmllint -noout --dtdvalid $(STYLESHEETS_DIR)/../schema/dtd/5.0/docbook.dtd $(MAIN).xml
	@#xmllint -noout --schematron $(STYLESHEETS_DIR)/../schema/schematron/5.0/docbook.sch $(MAIN).xml
	@#xmllint -noout --relaxng $(STYLESHEETS_DIR)/../schema/rng/5.0/docbook.rng $(MAIN).xml
	@#xmllint -noout --schema $(STYLESHEETS_DIR)/../schema/xsd/5.0/docbook.xsd $(MAIN).xml
