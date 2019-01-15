/*
 * Univention Directory Notifier
 *
 * Copyright 2004-2019 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */
#define _GNU_SOURCE

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/select.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#include "cache.h"
#include "callback.h"
#include "network.h"
#include "notify.h"

static NetworkClient_t client_head = { .next = &client_head };
#define for_each(client, p, n) \
	for (p = &client_head.next, client = client_head.next, n = client->next; \
		client != &client_head; \
		p = *p == client ? &(client->next) : p, client = n, n = client->next)
static int server_socketfd_listener;
static fd_set readfds;

enum network_protocol network_procotol_version = PROTOCOL_2;

/*
 * Open TCP network port.
 * :param port: TCP port number.
 * :returns: a socket file descriptor.
 */
int network_create_socket(int port) {
	int server_socketfd;
	struct sockaddr_in6 server_address;
	int i;

	server_socketfd = socket(PF_INET6, SOCK_STREAM, 0);

	i = 1;
	setsockopt(server_socketfd, SOL_SOCKET, SO_REUSEADDR, &i, sizeof(i));

	server_address.sin6_family = AF_INET6;
	server_address.sin6_addr = in6addr_any;
	server_address.sin6_port = htons(port);

	if (bind(server_socketfd, (struct sockaddr *)&server_address, sizeof(server_address)) == -1) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "bind cannot connect via AF_INET6, trying AF_INET");
		close(server_socketfd);
		struct sockaddr_in server_address;
		server_socketfd = socket(PF_INET, SOCK_STREAM, 0);
		i = 1;
		setsockopt(server_socketfd, SOL_SOCKET, SO_REUSEADDR, &i, sizeof(i));
		server_address.sin_family = AF_INET;
		server_address.sin_addr.s_addr = htonl(INADDR_ANY);
		server_address.sin_port = htons(port);
		if (bind(server_socketfd, (struct sockaddr *)&server_address, sizeof(server_address)) == -1) {
			perror("bind");
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "bind failed with AF_INET6 and also with AF_INET, exit");
			exit(1);
		}
	}

	if (listen(server_socketfd, 5) == -1) {
		perror("listen");
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "listen failed, exit");
		exit(1);
	}

	return server_socketfd;
}

/*
 * Add network connection for new client.
 * :param fd: The per-client socket file descriptor.
 * :param handler: The handler function.
 * :param notify: the initial notify status.
 * :returns: 0
 */
int network_client_add(int fd, callback_handler handler, int notify) {
	NetworkClient_t *client;

	client = calloc(1, sizeof(NetworkClient_t));
	client->fd = fd;
	client->handler = handler;
	client->notify = notify;
	client->next = client_head.next;

	client_head.next = client;

	return 0;
}

/*
 * Close network connection for client.
 * :param ptr: Indirect reference to client connection object.
 */
static void network_client_free(NetworkClient_t **ptr) {
	NetworkClient_t *client = *ptr;
	int fd = client->fd;

	FD_CLR(fd, &readfds);
	shutdown(fd, 2);
	close(fd);

	*ptr = client->next;

	free(client);
}

/*
 * Remove network connection for client.
 * :param fd: The per-client socket file descriptor.
 * :returns: 0
 */
static int network_client_del(int fd) {
	NetworkClient_t *client, **p, *n;

	for_each(client, p, n) {
		if (client->fd == fd) {
			network_client_free(p);
			break;
		}
	}

	return 0;
}

/*
 * Setup network connection for new client.
 * :param client: The per-client object.
 * :param remove: UNUSED.
 * :returns: 0
 */
static int new_connection(NetworkClient_t *client, callback_remove_handler remove) {
	struct sockaddr_in client_address;
	int client_socketfd;
	socklen_t client_l;
	int fd = client->fd;

	client_l = sizeof(client_address);

	if ((client_socketfd = accept(fd, (struct sockaddr *)&client_address, &client_l)) == -1) {
		return 1;
	}

	FD_SET(client_socketfd, &readfds);

	network_client_add(client_socketfd, data_on_connection, 0);

	return 0;
}

/*
 * Setup network server socket.
 * :param port: TCP port number.
 * :return 0
 */
int network_client_init(int port) {
	server_socketfd_listener = network_create_socket(port);
	network_client_add(server_socketfd_listener, new_connection, 0);

	return 0;
}

/*
 * Handle network and file notification events.
 * :param check_callbacks: Function to call after each event.
 * :return: never
 */
int network_client_main_loop(callback_check check_callbacks) {
	NetworkClient_t *client, **p, *n;
	fd_set testfds;

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Starting main loop");
	/* create listener socket */

	FD_ZERO(&readfds);
	FD_SET(server_socketfd_listener, &readfds);

	/* main loop */
	while (1) {
		testfds = readfds;
		if (select(FD_SETSIZE, &testfds, NULL, NULL, NULL) < 1) {
			/*FIXME */
			if (errno == EINTR || errno == 29) {
				/* Ignore signal */
				check_callbacks();
				continue;
			}
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "select() error: %s. exit", strerror(errno));
			exit(1);
		}

		for_each(client, p, n) {
			if (FD_ISSET(client->fd, &testfds)) {
				client->handler(client, network_client_del);
				break;
			}
		}
		check_callbacks();
	}

	return 0;
}

/*
 * Dump statof of one client connection to debug.
 * :param client: The per-client object.
 * :param level: Debug level.
 */
void network_client_dump1(NetworkClient_t *client, enum uv_debug_level level) {
	union {
		struct sockaddr generic;
		struct sockaddr_in ipv4;
		struct sockaddr_in6 ipv6;
	} peer;
	socklen_t len = sizeof(peer);
	char ipstr[INET6_ADDRSTRLEN] = "<unknown>";
	const char *addr = ipstr;
	int port = 0;

	if (client->fd == server_socketfd_listener) {
		addr = "<accept>";
	} else if (!getpeername(client->fd, &peer.generic, &len)) {
		switch (peer.generic.sa_family) {
		case AF_INET:
			port = peer.ipv4.sin_port;
			inet_ntop(AF_INET, &peer.ipv4.sin_addr, ipstr, sizeof(ipstr));
			break;
		case AF_INET6:
			port = peer.ipv6.sin6_port;
			inet_ntop(AF_INET6, &peer.ipv6.sin6_addr, ipstr, sizeof(ipstr));
			break;
		}
	}

	univention_debug(UV_DEBUG_TRANSFILE, level, "fd:%d addr=%s port=%d version=%d notify=%d next=%ld msg=%ld", client->fd, addr, port, client->version, client->notify, client->next_id, client->msg_id);
}

/*
 * Dump status of client connections to debug.
 * :return: 0
 */
int network_client_dump() {
	NetworkClient_t *client, **p, *n;

	if (univention_debug_get_level(UV_DEBUG_TRANSFILE) < UV_DEBUG_ALL)
		return 0;

	for_each(client, p, n)
		network_client_dump1(client, UV_DEBUG_ALL);

	return 0;
}

/*
 * Walk over all network clients and send notifications.
 * :param last_known_id: transaction ID.
 * :return: 0
 */
int network_client_check_clients(NotifyId last_known_id) {
	NetworkClient_t *client, **p, *n;
	char string[NETWORK_MAX];

	for_each(client, p, n) {
		if (client->notify) {
			if (client->next_id <= last_known_id) {
				char *dn_string = NULL;

				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "try to read %ld from cache", client->next_id);

				/* try to read from cache */
				if ((dn_string = notifier_cache_get(client->next_id)) == NULL) {
					univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "%ld not found in cache", client->next_id);

					/* read from transaction file, because not in cache */
					if ((dn_string = notify_transcation_get_one_dn(client->next_id)) == NULL) {
						univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "%ld failed", client->next_id);
						/* TODO: maybe close connection? */
					}
				}

				if (dn_string != NULL) {
					snprintf(string, sizeof(string), "MSGID: %ld\n%s\n\n", client->msg_id, dn_string);

					univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "--> %d: [%s]", client->fd, string);

					write(client->fd, string, strlen(string));

					free(dn_string);
				}
				client->notify = 0;
				client->msg_id = 0;
			}
		}
	}
	return 0;
}

/*
 * Walk over all network client and data to those waiting for specified transaction.
 * :param id: transaction ID.
 * :param buf: a buffer containing data.
 * :param l_buf: the length of the buffer.
 * :returns: -1 on errors, 0 on success.
 */
int network_client_all_write(NotifyId id, char *buf, size_t l_buf) {
	NetworkClient_t *client, **p, *n;
	int rc = 0;
	char string[NETWORK_MAX];

	if (l_buf == 0) {
		return 0;
	}

	for_each(client, p, n) {
		network_client_dump1(client, UV_DEBUG_ALL);
		if (client->notify) {
			if (client->next_id == id) {
				switch (client->version) {
					case PROTOCOL_2:
						snprintf(string, sizeof(string), "MSGID: %ld\n%.*s\n", client->msg_id, (int)l_buf, buf);
						break;
					case PROTOCOL_3:
						snprintf(string, sizeof(string), "MSGID: %ld\n%ld\n\n", client->msg_id, notify_last_id.id);
						break;
					default:
						univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "v%d not implemented fd=%d", client->version, client->fd);
						continue;
				}
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "Wrote to Listener fd = %d[%s]", client->fd, string);
				rc = write(client->fd, string, strlen(string));
				// rc = write(client->fd, buf, l_buf );
				client->notify = 0;
				client->msg_id = 0;
			}
		}
	}

	return rc;
}
