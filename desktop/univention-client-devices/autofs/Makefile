all:	autofs

autofs:	autofs.o
	gcc -o autofs autofs.o ../fuse/lib/libfuse.a -lpthread

%.o:	%.c
	gcc -Wall -c -I../fuse/include $<

clean:	
	rm -f *.o autofs
