

PROGS	= client server client-run
SRCS 	= signals.c connection.c script.c command.c protocol.c \
		process.c debug.c pipe.c security.c alive.c select_loop.c \
		session.c command_socket.c command_socket.c

CL_SRCS		= client_main.c
SRV_SRCS	= server_main.c
CLR_SRCS	= client_run_main.c

LIB	= libcs.a
LIBS = -luniventionconfig -luniventiondebug

CFLAGS	= -O2 -Wall -g
CC	= gcc

all:	${PROGS}

OBJS		= $(SRCS:.c=.o)
CL_OBJS		= $(CL_SRCS:.c=.o)
SRV_OBJS	= $(SRV_SRCS:.c=.o)
CLR_OBJS	= $(CLR_SRCS:.c=.o)

${LIB}: ${OBJS}
	ar rcu ${LIB} ${OBJS}

client:	${LIB} ${CL_OBJS}
	$(CC) -o client ${CL_OBJS} ${LIB} $(LIBS) $(LDFLAGS)

server:	${LIB} ${SRV_OBJS}
	$(CC) -o server ${SRV_OBJS} ${LIB} $(LIBS) $(LDFLAGS)

client-run:	${LIB} ${CLR_OBJS}
	$(CC) -o client-run ${CLR_OBJS} ${LIB} -lpthread $(LIBS) $(LDFLAGS)

install:	${PROGS}
	install -d ${DESTDIR}/usr/bin \
		${DESTDIR}/var/lib/univention-client-root/bin/usr/bin
	install -m 4755 server ${DESTDIR}/usr/bin/univention-session
	install -m 4755 client ${DESTDIR}/var/lib/univention-client-root/usr/bin/univention-login
	install -m 755 client-run ${DESTDIR}/usr/bin/univention-client-run

clean:
	rm -f ${OBJS} ${OBJS} ${SRV_OBJS} ${CL_OBJS} {$CLR_OBJS} *~ ${PROGS} ${LIB} 
