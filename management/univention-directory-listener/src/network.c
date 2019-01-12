/*
 * Univention Directory Listener
 *  an asyncronous notifier client API.
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


#define _GNU_SOURCE /* strndup */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include <sys/time.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <stdio.h>
#include <netdb.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <errno.h>

#include <univention/debug.h>
#include <univention/config.h>

#include "common.h"
#include "network.h"

#define NOTIFIER_PORT_PROTOCOL1 6668
#define NOTIFIER_PORT_PROTOCOL2 6669

static NotifierClient global_client;

/* Free notifier entry. */
void notifier_entry_free(NotifierEntry *entry) {
	free(entry->dn);
	entry->dn = NULL;
	entry->id = 0;
	entry->command = 0;
}


/* parses "<ID> <DN> [amdrn]" line into NotifierEntry */
static int parse_get_dn(const char *line, NotifierEntry *entry) {
	char *tmp;
	char *p, *q;
	size_t len;

	len = strlen(line);
	if (line[len - 1] == '\n')
		--len;
	tmp = strndup(line, len);

	if (tmp == NULL)
		return 1;

	if ((p = strchr(tmp, ' ')) == NULL) {
		free(tmp);
		return 1;
	}
	*p = '\0';
	entry->id = atoi(tmp);

	++p;
	q = strrchr(p, ' ');
	if (q != NULL && *(q + 1) != '\0' && *(q + 2) == '\0') {
		*q = '\0';
		entry->command = *(q + 1);
	} else {
		entry->command = 'm';
	}
	entry->dn = strdup(p);

	free(tmp);
	return 0;
}


/* Send buffer in blocking mode. */
static int send_block(NotifierClient *client, const char *buf, size_t len) {
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, ">>>%s", buf);
	return write(client->fd, buf, len);
}


/* Receive data in blocking mode. */
static int recv_block(NotifierClient *client, char **back, time_t timeout) {
	char buf[BUFSIZ];
	char *result, *pos;
	size_t len;
	int rv;

	/* receive block containing \n\n */
	if (client->buf != NULL) {
		result = client->buf;
		len = strlen(result);
	} else {
		result = NULL;
		len = 0;
	}

	/* read from network until string contains \n\n;
	   XXX: we could probably also check that \n\n is at the end of
	   the buffer; if it isn't, it's probably the beginning of a further
	   message; */
	while (result == NULL || (pos = strstr(result, "\n\n")) == NULL) {
		ssize_t r;

		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "RESULT: [%s]", result);
		if ((rv = notifier_wait(client, timeout)) == 0) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "timeout when receiving data");
			return 0;
		} else if (rv < 0)
			return 0;

		r = read(client->fd, buf, BUFSIZ);
		if (r == 0) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "connection to notifier was closed");
			return 0;
		} else if (r < 0) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "error %d: %s while receiving from notifier", errno, strerror(errno));
			return 0;
		}

		result = realloc(result, len + r + 1);
		result[len] = '\0';
		strncat(result, buf, r);
		len += r;
		result[len] = '\0';
	}

	/* *(pos+1) is the second \n; split string there */
	*(pos + 1) = '\0';
	*back = result;

	if (*(pos + 2) != '\0') {
		client->buf = strdup(pos + 2);
	} else {
		client->buf = NULL;
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "<<<%s", *back);
	return strlen(*back);
}


/* Send notifier command. */
static int notifier_send_command(NotifierClient *client, const char *msg) {
	char buf[BUFSIZ];
	int msgid;
	ssize_t len;

	assert(client->fd > -1);
	msgid = ++client->last_msgid;
	len = snprintf(buf, BUFSIZ, "MSGID: %d\n%s", msgid, msg);
	assert(len < BUFSIZ - 1);
	send_block(client, buf, len);
	return msgid;
}


/* Receive result of notifier command. */
int notifier_recv_result(NotifierClient *client, time_t timeout) {
	NotifierMessage *msg;
	char *result, *tmp;
	int rv;

	if (client == NULL)
		client = &global_client;
	assert(client->fd > -1);

	if ((rv = notifier_wait(client, timeout)) == 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "no data is available (i.e. timeout elapsed)");
		return 0;
	} else if (rv < 0)
		return 0;

	if (recv_block(client, &result, NOTIFIER_TIMEOUT) < 10)
		return 0;

	if ((msg = malloc(sizeof(NotifierMessage))) == NULL)
		return 0;

	/* strip MSGID: %d\n and copy the rest to msg->result */
	tmp = strchr(result, '\n');
	if (tmp == NULL) {
		free(msg);
		return 0;
	}
	*tmp = '\0';

	/* parse msgid */
	sscanf(result, "MSGID: %d", &msg->id);
	if (msg->id <= 0) {
		free(msg);
		return 0;
	}

	msg->result = strdup(tmp + 1);
	free(result);

	/* insert into list */
	msg->next = client->messages;
	client->messages = msg;

	return msg->id;
}


/* Remove message from queue of received messages. */
static NotifierMessage *notifier_remove_msg(NotifierClient *client, int msgid) {
	NotifierMessage *cur, *prev;

	if (client == NULL)
		client = &global_client;

	for (cur = client->messages, prev = NULL; cur != NULL; prev = cur, cur = cur->next) {
		if (cur->id == msgid) {
			if (cur == client->messages)
				client->messages = cur->next;
			else
				prev->next = cur->next;
			return cur;
		}
	}
	return NULL;
}


/* Wait for and return specific message. */
static NotifierMessage *notifier_wait_msg(NotifierClient *client, int msgid, time_t timeout) {
	NotifierMessage *msg;
	int resid;

	if ((msg = notifier_remove_msg(client, msgid)) != NULL)
		return msg;

	do {
		resid = notifier_recv_result(client, timeout);
		if (resid == 0)
			return NULL;
	} while (resid != msgid);

	return notifier_remove_msg(client, msgid);
}


/* Free message object. */
static void notifier_msg_free(NotifierMessage *msg) {
	free(msg->result);
	free(msg);
}


/* Return specific message. */
NotifierMessage *notifier_get_msg(NotifierClient *client, int msgid) {
	NotifierMessage *cur;

	if (client == NULL)
		client = &global_client;

	for (cur = client->messages; cur != NULL; cur = cur->next) {
		if (cur->id == msgid)
			return cur;
	}
	return NULL;
}


/* Try to connect to notifier running on @server.
 *
 * @param client client data structure pointer.
 * @param server DNS name of notifier host.
 * @param starttls 0=no encryption, 2=require TLS (not supported)
 * @return 0 on success, 1 on (TLS, DNS, timeout, protocol) errors, 2 on connection-error.
 */
int notifier_client_new(NotifierClient *client, const char *server, int starttls) {
	struct sockaddr_in address4;
	struct sockaddr_in6 address6;
	struct sockaddr *address;
	socklen_t addrlen;
	struct addrinfo hints, *res, *result_addrinfo;
	char *ucrvalue;
	char addrstr[100];
	int err;

	if (client == NULL)
		client = &global_client;

	if (starttls >= 2) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "This version does not support TLS");
		return 1;
	}

	client->server = strdup(server);
	client->protocol = 0;
	client->starttls = 0;
	client->messages = NULL;
	client->last_msgid = 0;
	client->buf = NULL;

	memset(&hints, 0, sizeof(hints));
	hints.ai_family = AF_UNSPEC; /* Allow IPv4 or IPv6 */
	hints.ai_socktype = SOCK_STREAM;
	hints.ai_flags = 0;
	hints.ai_protocol = 0; /* Any protocol */

	/* limit address resolution to IPv4 XOR IPv6 */
	ucrvalue = univention_config_get_string("listener/network/protocol");
	if (ucrvalue) {
		if (!strcmp(ucrvalue, "ipv4")) {
			hints.ai_family = AF_INET;
		} else if (!strcmp(ucrvalue, "ipv6")) {
			hints.ai_family = AF_INET6;
		}
		free(ucrvalue);
	}

	address4.sin_family = AF_INET;
	address4.sin_port = htons(NOTIFIER_PORT_PROTOCOL2);
	address6.sin6_family = AF_INET6;
	address6.sin6_port = htons(NOTIFIER_PORT_PROTOCOL2);

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "connecting to notifier %s:%d", client->server, NOTIFIER_PORT_PROTOCOL2);

	err = getaddrinfo(client->server, NULL, &hints, &result_addrinfo);
	if (err != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "address resolution of %s failed with errorcode %d: %s", client->server, err, gai_strerror(err));
		free(client->server);
		client->server = NULL;
		return 1;
	}

	/* process all results */
	for (res = result_addrinfo; res != NULL; res = res->ai_next) {
		switch (res->ai_family) {
		case AF_INET:
			if ((client->fd = socket(AF_INET, SOCK_STREAM, 0)) == -1) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "creating IPv4 socket descriptor failed with errorcode %d: %s", errno, strerror(errno));
				continue;
			}
			memcpy(&address4.sin_addr, &((struct sockaddr_in *)res->ai_addr)->sin_addr, sizeof(address4.sin_addr));
			/* convert IPv4 address to string */
			inet_ntop(res->ai_family, &((struct sockaddr_in *)res->ai_addr)->sin_addr, addrstr, 100);
			address = (struct sockaddr *)&address4;
			addrlen = sizeof(address4);
			break;

		case AF_INET6:
			if ((client->fd = socket(AF_INET6, SOCK_STREAM, 0)) == -1) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "creating IPv6 socket descriptor failed with errorcode %d: %s", errno, strerror(errno));
				continue;
			}
			memcpy(&address6.sin6_addr, &((struct sockaddr_in6 *)res->ai_addr)->sin6_addr, sizeof(address6.sin6_addr));
			/* convert IPv6 address to string */
			inet_ntop(res->ai_family, &((struct sockaddr_in6 *)res->ai_addr)->sin6_addr, addrstr, 100);
			address = (struct sockaddr *)&address6;
			addrlen = sizeof(address6);
			break;

		default:
			/* unknown protocol */
			continue;
		}

		{
			struct timeval timeout = {
			    .tv_sec = NOTIFIER_TIMEOUT * 2, .tv_usec = 0,
			};
			int ret;
			ret = setsockopt(client->fd, SOL_SOCKET, SO_RCVTIMEO, &timeout, sizeof(timeout));
			if (ret < 0)
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "Failed to set SO_RCVTIMEO");
			ret = setsockopt(client->fd, SOL_SOCKET, SO_SNDTIMEO, &timeout, sizeof(timeout));
			if (ret < 0)
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "Failed to set SO_SNDTIMEO");

			const int enable = 1;
			ret = setsockopt(client->fd, SOL_SOCKET, SO_KEEPALIVE, &enable, sizeof(enable));
			if (ret < 0)
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "Failed to enable TCP KEEPALIVE");
			const int idle = 60;
			ret = setsockopt(client->fd, SOL_TCP, TCP_KEEPIDLE, &idle, sizeof(idle));
			if (ret < 0)
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "Failed to set TCP_KEEPIDLE");
			const int probes = 12;
			ret = setsockopt(client->fd, SOL_TCP, TCP_KEEPCNT, &probes, sizeof(probes));
			if (ret < 0)
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "Failed to set TCP_KEEPCNT");
			const int interval = 5;
			ret = setsockopt(client->fd, SOL_TCP, TCP_KEEPINTVL, &interval, sizeof(interval));
			if (ret < 0)
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "Failed to set TCP_KEEPINTVL");
		}

		if (connect(client->fd, address, addrlen) == -1) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "connection to %s failed with errorcode %d: %s", addrstr, errno, strerror(errno));
			close(client->fd);
			client->fd = -1;
			continue;
		}
		break;
	}
	freeaddrinfo(result_addrinfo);

	if (client->fd == -1) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to connect to any notifier");
		free(client->server);
		client->server = NULL;
		return 2;
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "established connection to %s port %d", addrstr, NOTIFIER_PORT_PROTOCOL2);

	const char *header = "Version: 2\nCapabilities: \n\n";
	const size_t len = strlen(header);
	char *result, *tok;

	if (send_block(client, header, len) != len) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "couldn't send header");
		free(client->server);
		client->server = NULL;
		return 1;
	}
	if (recv_block(client, &result, NOTIFIER_TIMEOUT) < 1) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "couldn't receive header");
		free(client->server);
		client->server = NULL;
		return 1;
	}

	/* strtok modifies result, but we shouldn't need to care */
	for (tok = strtok(result, "\n"); tok != NULL; tok = strtok(NULL, "\n")) {
		char *val;
		if ((val = strchr(tok, ':')) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "ignoring bad header: [%s]", tok);
			continue;
		}
		*val++ = '\0';
		while (*val == ' ')
			++val;

		if (strcmp(tok, "Version") == 0) {
			client->protocol = atoi(val);
		}
	}

	free(result);

	if (client->protocol != 2) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Protocol version %d is not supported", client->protocol);
		free(client->server);
		client->server = NULL;
		return 1;
	}

	return 0;
}


/* Free notifier client data. */
void notifier_client_destroy(NotifierClient *client) {
	if (client == NULL)
		client = &global_client;

	if (client->fd > -1)
		close(client->fd);
	client->fd = -1;
}


/* Wait for data from notifier. */
int notifier_wait(NotifierClient *client, time_t timeout) {
	fd_set fds;
	struct timeval tv;
	int rv;

	if (client == NULL)
		client = &global_client;
	assert(client->fd > -1);

	FD_ZERO(&fds);
	FD_SET(client->fd, &fds);

	do {
		if (timeout >= 0) {
			tv.tv_sec = timeout;
			tv.tv_usec = 0;
			rv = select(client->fd + 1, &fds, NULL, NULL, &tv);
		} else {
			rv = select(client->fd + 1, &fds, NULL, NULL, NULL);
		}
	} while (rv == -1 && errno == EINTR);
	if (rv == -1) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "select: %s", strerror(errno));
	}

	return rv;
}


/* Send message to retrieve DN of given transaction from notifier. */
int notifier_get_dn(NotifierClient *client, NotifierID id) {
	char request[BUFSIZ];

	if (client == NULL)
		client = &global_client;

	snprintf(request, BUFSIZ, "GET_DN %ld\n", id);
	return notifier_send_command(client, request);
}


/* Resend message to retrieve DN from notifier. */
int notifier_resend_get_dn(NotifierClient *client, int msgid, NotifierID id) {
	char buf[BUFSIZ];
	ssize_t len;

	if (client == NULL)
		client = &global_client;

	assert(client->fd > -1);
	len = snprintf(buf, BUFSIZ, "MSGID: %d\nGET_DN %ld\n\n", msgid, id);
	assert(len < BUFSIZ - 1);
	send_block(client, buf, len);

	return 0;
}


/* Wait for and return DN of transaction from notifier. */
int notifier_get_dn_result(NotifierClient *client, int msgid, NotifierEntry *entry) {
	NotifierMessage *msg;
	int rc = 0;

	if (client == NULL)
		client = &global_client;

	if ((msg = notifier_wait_msg(client, msgid, NOTIFIER_TIMEOUT)) == NULL)
		return 1;

	rc = parse_get_dn(msg->result, entry);
	notifier_msg_free(msg);
	return rc;
}


/* Retrieve current transaction ID from notifier. */
int notifier_get_id_s(NotifierClient *client, NotifierID *id) {
	int msgid;
	NotifierMessage *msg;

	if (client == NULL)
		client = &global_client;

	msgid = notifier_send_command(client, "GET_ID\n");
	if ((msg = notifier_wait_msg(client, msgid, NOTIFIER_TIMEOUT)) == NULL)
		return 1;

	*id = atoi(msg->result);

	notifier_msg_free(msg);
	return 0;
}


/* Retrieve current Schema-ID from notifier. */
int notifier_get_schema_id_s(NotifierClient *client, NotifierID *id) {
	int msgid;
	NotifierMessage *msg;

	if (client == NULL)
		client = &global_client;

	msgid = notifier_send_command(client, "GET_SCHEMA_ID\n");
	if ((msg = notifier_wait_msg(client, msgid, NOTIFIER_TIMEOUT)) == NULL)
		return 1;

	*id = atoi(msg->result);

	notifier_msg_free(msg);
	return 0;
}


/* Send keep-alive message to notifier. */
int notifier_alive_s(NotifierClient *client) {
	int msgid;
	NotifierMessage *msg;

	if (client == NULL)
		client = &global_client;

	msgid = notifier_send_command(client, "ALIVE\n");
	if ((msg = notifier_wait_msg(client, msgid, NOTIFIER_TIMEOUT)) == NULL)
		return 1;

	notifier_msg_free(msg);
	return 0;
}
