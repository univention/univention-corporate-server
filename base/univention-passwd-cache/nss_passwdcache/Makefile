all:	libnss_passwdcache.so.2

libnss_passwdcache.so.2:	nss_passwdcache.o
	gcc -shared -o libnss_passwdcache.so.2 -Wl,-soname,libnss_passwdcache.so.2 nss_passwdcache.o

%.o:	%.c
	gcc -fPIC -Wall -D_GNU_SOURCE -c $<

clean:
	rm -f *.o *.so.2
