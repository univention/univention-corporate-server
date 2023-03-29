#!/usr/bin/make -f
# simple makefile wrapper to run waf

WAF_BINARY=$(PYTHON) ./buildtools/bin/waf
WAF=PYTHONHASHSEED=1 WAF_MAKE=1 WAFLOCK=.lock-waf $(WAF_BINARY)

all: build;
everything: all;
testsuite: all;
check: test;
installcheck: test;

%:
	$(WAF) $@

dist dictcheck: WAFLOCK=/dev/null

show_waf_options:
	$(WAF) --help
