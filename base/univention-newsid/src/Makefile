PROG=		univention-newsid
OBJS=		memory.o util_pw.o md4.o genrand.o newsid.o

BINDIR=		$(SUFFIX)/usr/local/bin

CC=		gcc
CFLAGS=		-Wall -O2

$(PROG):	$(OBJS)
	$(CC) $(CFLAGS) -o $(PROG) $(OBJS);

install: 
	cp $(PROG) $(BINDIR)/$(PROG)
	chmod 0644 $(BINDIR)/$(PROG)

clean:
	rm -f $(OBJS) *~
