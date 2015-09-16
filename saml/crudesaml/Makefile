#!/usr/bin/make -f

.PHONY: all clean install

crudesaml: crudesaml-*.tar.gz
	tar xvzf $< --transform s/crudesaml-1.5/crudesaml/g && \
		cd crudesaml && \
		patch -p1 < ../01fix_destdir.patch && \
		patch -p0 < ../02fix_manpage_typos.patch && \
		patch -p1 < ../03_fix_information_leak_and_missing_break.patch && \
		patch -p1 < ../04_reduce_segfault_risk.patch

all: crudesaml
	cd crudesaml && \
		export cyrus_sasl2_prefix=/usr && \
		./configure --prefix '/' --datarootdir /usr/share --libdir=/lib && \
		make all

install: crudesaml all
	cd crudesaml && DESTDIR="$(BUILDDIR)/build" make install

clean:
	cd crudesaml && make clean || true
	rm -rf crudesaml
