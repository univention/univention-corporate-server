build: license.so

license.so: py_license.c
	gcc -Wall py_license.c -c -fpic -I/usr/include/python2.4 -I../include -L../lib/.libs/ -I -luniventionlicense -o py_license.o
	gcc -shared py_license.o  -o license.so -L../lib/.libs/ -luniventionlicense
	rm -f py_license.o

clean:
	rm -f license.so
