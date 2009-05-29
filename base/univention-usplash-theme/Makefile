CC=gcc
CFLAGS=-g -Wall -fPIC
LDFLAGS=
INCLUDES=

COMPILE = $(CC) $(INCLUDES) $(CFLAGS)
LINK = $(CC) $(CFLAGS) $(LDFLAGS)

INSTALL = /usr/bin/install -c
INSTALL_DATA = $(INSTALL) -m 644
INSTALL_PROGRAM = $(INSTALL) -m 755

all: theme.so

theme.so: silent-splash-640x480.png.c.o silent-splash-800x600.png.c.o silent-splash-1024x768.png.c.o silent-splash-1280x1024.png.c.o silent-splash-1600x1200.png.c.o throbber_fore.png.c.o throbber_back.png.c.o theme.c.o
	$(COMPILE) -shared -o $@ $^
	#cp theme.so /usr/lib/usplash/usplash-artwork.so
#cmap.gif:
#	convert +dither originals/cmap.png cmap.gif

%.png.c: %.png cmap.gif
	convert $< +dither -map cmap.gif gif:- | convert gif:- $<
	pngtousplash $< > $@

%.png:
	cp originals/$@ .

%.o: %.c
	$(COMPILE) -o $@ -c $<

%.c.o: %.c
	$(COMPILE) -o $@ -c $<

%.bdf.c: %.bdf
	bdftousplash $< > $@

install: theme.so
	$(INSTALL_DATA) -D $< $(DESTDIR)/usr/lib/usplash/univention-theme.so
clean:
	rm -f  *.o *.so *.png 

