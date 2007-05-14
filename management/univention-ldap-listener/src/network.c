/*
 * Univention LDAP Listener
 *  an asyncronous notifier client API.
 *
 * Copyright (C) 2004, 2005, 2006 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Binary versions of this file provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
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
#include <arpa/inet.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/stat.h>
#include <errno.h>

#include <univention/debug.h>

#include "common.h"
#include "network.h"

#define NOTIFIER_PORT_PROTOCOL1 6668
#define NOTIFIER_PORT_PROTOCOL2 6669

static NotifierClient global_client;

void notifier_entry_free(NotifierEntry *entry)
{
	free(entry->dn);
	entry->dn = NULL;
	entry->id = 0;
	entry->command = 0;
}

/* parses "<ID> <DN> [amd]" line into NotifierEntry */
static int parse_entry(const char *line, NotifierEntry *entry)
{
	char *tmp;
	char *p, *q;
	size_t len;

	len = strlen(line);
	if (line[len-1] == '\n')
		--len;
	tmp = strndup(line, len);
	
	if (tmp == NULL)
		return 0;

	if ((p = strchr(tmp, ' ')) == NULL) {
		free(tmp);
		return 1;
	}
	*p = '\0';
	entry->id = atoi(tmp);
	
	++p;
	q=strrchr(p, ' ');
	if (q != NULL && *(q+1) != '\0' && *(q+2) == '\0') {
		*q = '\0';
		entry->command = *(q+1);
	} else {
		entry->command = 'm';
	}
	entry->dn = strdup(p);

	free(tmp);
	return 2;
}


static int send_block(NotifierClient *client, const char *buf, size_t len)
{
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, ">>>\n%s\n", buf);
	return write(client->fd, buf, len);
}

static int recv_block(NotifierClient *client, char **back, time_t timeout)
{
	char	 buf[BUFSIZ];
	char	*result, *pos;
	size_t	 len;
	int	 rv;

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
	while(result == NULL || (pos = strstr(result, "\n\n")) == NULL) {
		ssize_t r;
		
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "RESULT: [%s]\n", result);
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
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "error %d while receiving from notifier", r);
			return 0;
		}

		result = realloc(result, len+r+1);
		result[len] = '\0';
		strncat(result, buf, r);
		len += r;
		result[len] = '\0';
	}

	/* *(pos+1) is the second \n; split string there */
	*(pos+1) = '\0';
	*back = result;
	
	if (*(pos+2) != '\0') {
		client->buf = strdup(pos+2);
	} else {
		client->buf = NULL;
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "<<<\n%s\n", *back);
	return strlen(*back);
}

static int notifier_send_command(NotifierClient *client, const char *msg)
{
	char	buf[BUFSIZ];
	int	msgid;
	ssize_t	len;
	
	assert(client->fd > -1);
	msgid = ++client->last_msgid;
	len = snprintf(buf, BUFSIZ, "MSGID: %d\n%s\n", msgid, msg);
	assert(len < BUFSIZ-1);
	send_block(client, buf, len);
	return msgid;
}

int notifier_recv_result(NotifierClient *client, time_t timeout)
{
	NotifierMessage *msg;
	char		*result, *tmp;
	int		 rv;

	if (client == NULL)
		client = &global_client;
	assert(client->fd > -1);
	
	if ((rv = notifier_wait(client, timeout)) == 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "no data is available (i.e. timeout elasped)");
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
	
	msg->result = strdup(tmp+1);
	free(result);

	/* insert into list */
	msg->next = client->messages;
	client->messages = msg;

	return msg->id;
}

static NotifierMessage* notifier_remove_msg(NotifierClient *client, int msgid)
{
	NotifierMessage *cur, *prev;

	if (client == NULL)
		client = &global_client;

	for (cur = client->messages, prev = NULL; cur != NULL;
			prev = cur, cur = cur->next) {
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

static NotifierMessage *notifier_wait_msg(NotifierClient *client, int msgid, time_t timeout)
{
	NotifierMessage *msg;
	int		 resid;

	
	if ((msg = notifier_remove_msg(client, msgid)) != NULL)
		return msg;
	
	do {
		resid = notifier_recv_result(client, timeout);
		if (resid == 0)
			return NULL;
	} while (resid != msgid);

	return notifier_remove_msg(client, msgid);
}

static void notifier_msg_free(NotifierMessage *msg)
{
	free(msg->result);
	free(msg);
}

NotifierMessage* notifier_get_msg(NotifierClient *client, int msgid)
{
	NotifierMessage *cur;
	
	if (client == NULL)
		client = &global_client;

	for (cur = client->messages; cur != NULL; cur = cur->next) {
		if (cur->id == msgid)
			return cur;
	}
	return NULL;
}


int notifier_client_new(NotifierClient *client,
		const char *server, int starttls)
{
	struct hostent		*host;
	struct sockaddr_in	 address;
	
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
	client->buf = NULL ;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "connecting to notifier %s", client->server);
	
	if ((host = gethostbyname(client->server)) == NULL) {
		free(client->server);
		client->server = NULL;
		return 1;
	}
	if ((client->fd = socket(PF_INET, SOCK_STREAM, 0)) == -1) {
		free(client->server);
		client->server = NULL;
		return 1;
	}
	address.sin_family = AF_INET;
	memcpy(&address.sin_addr, host->h_addr_list[0], sizeof(address.sin_addr));

	/* protocol 2 */
	address.sin_port = htons(NOTIFIER_PORT_PROTOCOL2);
	if (connect(client->fd, (struct sockaddr*)&address, sizeof(address)) != -1) {
		const char	*header = "Version: 2\nCapabilities: \n\n";
		char		*result,
				*tok;
		
		send_block(client, header, strlen(header));
		if (recv_block(client, &result, NOTIFIER_TIMEOUT) < 1) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "couldn't receive header");
			free(client->server);
			client->server = NULL;
			return 1;
		}

		/* strtok modifies result, but we shouldn't need to care */
		for(tok=strtok(result, "\n"); tok != NULL; tok=strtok(NULL, "\n")) {
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
	} else {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to connect to notifier");
		free(client->server);
		client->server = NULL;
		return 2;
	}

	if (client->protocol != 2) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Protocol version %d is not supported", client->protocol);
		free(client->server);
		client->server = NULL;
		return 1;
	}

	return 0;
}

void notifier_client_destroy(NotifierClient * client)
{
	if (client == NULL)
		client = &global_client;

	if (client->fd > -1)
		close(client->fd);
	client->fd = -1;
}

int notifier_wait(NotifierClient *client, time_t timeout)
{
	fd_set         fds;
	struct timeval tv;
	int            rv;

	if (client == NULL)
		client = &global_client;
	assert(client->fd > -1);
	
	FD_ZERO(&fds);
	FD_SET(client->fd, &fds);

	do {
		if (timeout >= 0) {	
			tv.tv_sec = timeout;
			tv.tv_usec = 0;
			rv = select(client->fd+1, &fds, NULL, NULL, &tv);
		} else {
			rv = select(client->fd+1, &fds, NULL, NULL, NULL);
		}
	} while (rv == -1 && errno == EINTR);
	if (rv == -1) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "select: %s", strerror(errno));
	}

	return rv;
}

int notifier_get_dn(NotifierClient *client, NotifierID id)
{
	char request[BUFSIZ];
	
	if (client == NULL)
		client = &global_client;

	snprintf(request, BUFSIZ, "GET_DN %ld\n", id);
	return notifier_send_command(client, request);
}

int notifier_resend_get_dn(NotifierClient *client, int msgid, NotifierID id)
{
	char buf[BUFSIZ];
	ssize_t len;

	if (client == NULL)
		client = &global_client;

	assert(client->fd > -1);
	len = snprintf(buf, BUFSIZ, "MSGID: %d\nGET_DN %ld\n\n", msgid, id);
	assert(len < BUFSIZ-1);
	send_block(client, buf, len);

	return 0;
}

int notifier_get_dn_result(NotifierClient *client, int msgid, NotifierEntry *entry)
{
	NotifierMessage	*msg;
	
	if (client == NULL)
		client = &global_client;

	if ((msg = notifier_wait_msg(client, msgid, NOTIFIER_TIMEOUT)) == NULL)
		return 1;

	parse_entry(msg->result, entry);
	notifier_msg_free(msg);
	return 0;
}

int notifier_get_id_s(NotifierClient *client, NotifierID *id)
{
	int		 msgid;
	NotifierMessage	*msg;
	
	if (client == NULL)
		client = &global_client;

	msgid = notifier_send_command(client, "GET_ID\n");
	if ((msg = notifier_wait_msg(client, msgid, NOTIFIER_TIMEOUT)) == NULL)
		return 1;

	*id = atoi(msg->result);
	
	notifier_msg_free(msg);
	return 0;
}

int notifier_get_schema_id_s(NotifierClient *client, NotifierID *id)
{
	int		 msgid;
	NotifierMessage	*msg;
	
	if (client == NULL)
		client = &global_client;

	msgid = notifier_send_command(client, "GET_SCHEMA_ID\n");
	if ((msg = notifier_wait_msg(client, msgid, NOTIFIER_TIMEOUT)) == NULL)
		return 1;

	*id = atoi(msg->result);
	
	notifier_msg_free(msg);
	return 0;
}

int notifier_alive_s(NotifierClient *client)
{
	int		 msgid;
	NotifierMessage	*msg;

	if (client == NULL)
		client = &global_client;

	msgid = notifier_send_command(client, "ALIVE\n");
	if ((msg = notifier_wait_msg(client, msgid, NOTIFIER_TIMEOUT)) == NULL)
		return 1;

	notifier_msg_free(msg);
	return 0;
}
