#!/usr/bin/make -f

.PHONY: all clean install

crudesaml: crudesaml-*.tar.gz
	tar xvzf $< --transform s/crudesaml-1.5/crudesaml/g

all: crudesaml
	cd crudesaml && ./configure --prefix '/' --datarootdir /usr/share && make all

install: crudesaml all
	cd crudesaml && DESTDIR="$(BUILDDIR)/build" make install
	mv "$(DESTDIR)/$(DESTDIR)/lib/security" "$(DESTDIR)/lib"
	rm -rf "$(DESTDIR)/$(shell echo "$(DESTDIR)" | cut -d '/' -f 2)"
	mkdir -p "$(DESTDIR)/usr/lib/"
	mv "$(DESTDIR)/lib/sasl2/" "$(DESTDIR)/usr/lib/"

clean:
	cd crudesaml && make clean || true
