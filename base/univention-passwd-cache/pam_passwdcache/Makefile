all:	pam_passwdcache.so

pam_passwdcache.so:	pam_passwdcache.o
	gcc -shared -Wl,-x -lcrypt -lpamc -lpam -o $@ pam_passwdcache.o

#%.o:	%.c
#	gcc -Wall -O2 -D_GNU_SOURCE -D_REENTRANT -DLINUX_PAM -fPIC -Dlinux -DPAM_DYNAMIC -Di386 -c $< -o $@

pam_passwdcache.o:	pam_passwdcache.c
	gcc -Wall -O2 -D_GNU_SOURCE -D_REENTRANT -DLINUX_PAM -fPIC -Dlinux -DPAM_DYNAMIC -Di386 -c $< -o $@

clean:
	rm -f pam_passwdcache.o pam_passwdcache.so

