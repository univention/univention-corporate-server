#
# Univention Client Login
#  Makefile for the session handler
#
# Copyright 2004-2010 Univention GmbH
#
# http://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <http://www.gnu.org/licenses/>.

PROGS	= client server client-run uniclient
SRCS 	= signals.c connection.c script.c command.c protocol.c \
	process.c debug.c pipe.c security.c alive.c select_loop.c \
	session.c command_socket.c channels.c cmd_handler.c \
	uniclient_main.c

CL_SRCS		= client_main.c
SRV_SRCS	= server_main.c
CLR_SRCS	= client_run_main.c
UNI_SRCS	= uniclient_main.c

LIB	= libcs.a

CFLAGS	= -g -Wall
CC	= gcc

all:	${PROGS}

OBJS		= $(SRCS:.c=.o)
CL_OBJS		= $(CL_SRCS:.c=.o)
SRV_OBJS	= $(SRV_SRCS:.c=.o)
CLR_OBJS	= $(CLR_SRCS:.c=.o)
UNI_OBJS	= $(UNI_SRCS:.c=.o)


${LIB}: ${OBJS}
	ar rcu ${LIB} ${OBJS}

client:	${LIB} ${CL_OBJS}
	$(CC) -o client ${CL_OBJS} ${LIB} $(LIBS) $(LDFLAGS)

server:	${LIB} ${SRV_OBJS}
	$(CC) -o server ${SRV_OBJS} ${LIB} $(LIBS) $(LDFLAGS)

client-run:	${LIB} ${CLR_OBJS}
	$(CC) -o client-run ${CLR_OBJS} ${LIB} $(LIBS) $(LDFLAGS)

uniclient:	${LIB} ${CLR_OBJS}
	$(CC) -o uniclient ${UNI_OBJS} ${LIB} $(LIBS) $(LDFLAGS)

install:	${PROGS}
	install -d ${DESTDIR}/usr/bin \
		${DESTDIR}/var/lib/univention-client-root/bin/usr/bin
	install -m 4755 uniclient ${DESTDIR}/usr/bin/univention-session
	install -m 4755 uniclient ${DESTDIR}/var/lib/univention-client-root/usr/bin/univention-login
	install -m 755 client-run ${DESTDIR}/usr/bin/univention-client-run

clean:
	rm -f ${OBJS} ${OBJS} ${SRV_OBJS} ${CL_OBJS} {$CLR_OBJS} *~ ${PROGS} ${LIB}
