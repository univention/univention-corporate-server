#!/usr/bin/make -f
# simple makefile wrapper to run waf

WAF=WAF_MAKE=1 buildtools/bin/waf

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
