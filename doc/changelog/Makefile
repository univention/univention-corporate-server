#!/usr/bin/make -f

.PHONY: all
all: pdf

.PHONY: pdf
pdf:: release-notes-3.2.pdf release-notes-3.2_en.pdf
release-notes-%.pdf: release-notes-%.tex changelog-%.tex
	./pdf-latex.py $<
release-notes-%_en.pdf: release-notes-%_en.tex changelog-%.tex
	./pdf-latex.py $<

.PHONY: clean
clean:
	$(RM) release-notes-3.2*mtc?
	$(RM) release-notes-3.2*nnx
	$(RM) release-notes-3.2*idx
	$(RM) release-notes-3.2*ilg
	$(RM) release-notes-3.2*nnd
	$(RM) release-notes-3.2*aux
	$(RM) release-notes-3.2*bbl
	$(RM) release-notes-3.2*bmt
	$(RM) release-notes-3.2*blg
	$(RM) release-notes-3.2*toc
	$(RM) release-notes-3.2*ndx
	$(RM) release-notes-3.2*log
	$(RM) changelog*log
	$(RM) release-notes-3.2*out
	$(RM) release-notes-3.2*pdf
