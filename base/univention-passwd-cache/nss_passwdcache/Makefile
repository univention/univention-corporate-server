all:	libnss_passwdcache.so.2

libnss_passwdcache.so.2:	nss_passwdcache.o
	gcc -shared -o libnss_passwdcache.so.2 -W1,soname,libnss_passwdcache.so.2 nss_passwdcache.o

%.o:	%.c
	gcc -Wall -D_GNU_SOURCE -D_IO_MTSAFE_IO -c $<

clean:
	rm -f *.o *.so.2
