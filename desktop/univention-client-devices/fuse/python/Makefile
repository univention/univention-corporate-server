_fusemodule.so: _fusemodule.c
<<<<<<< Makefile
	gcc -g3 -I/usr/include/python1.5 -I../include -L../lib _fusemodule.c -Wl,-shared -o _fusemodule.so -Wimplicit -lfuse && python1.5 -c 'import _fuse'
=======
	gcc -g3 -I/usr/include/python2.1 _fusemodule.c -Wl,-shared -o _fusemodule.so -Wimplicit -lfuse && python -c 'import _fuse'
>>>>>>> 1.3

clean:
	rm -f _fusemodule.so *.pyc *.pyo
