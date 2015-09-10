#!/usr/bin/make -f

.PHONY: all clean install

crudesaml: crudesaml-*.tar.gz
	tar xvzf $< --transform s/crudesaml-1.5/crudesaml/g && \
		cd crudesaml && \
		patch -p1 < ../01fix_destdir.patch \
		patch -p1 < ../02fix_manpage_typos.patch

all: crudesaml
	cd crudesaml && \
		export cyrus_sasl2_prefix=/usr && \
		./configure --prefix '/' --datarootdir /usr/share --libdir=/lib && \
		make all

install: crudesaml all
	cd crudesaml && DESTDIR="$(BUILDDIR)/build" make install

clean:
	cd crudesaml && make clean || true
