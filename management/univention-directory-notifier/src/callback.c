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
#define __USE_GNU

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/ioctl.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <univention/debug.h>

#include "cache.h"
#include "network.h"
#include "notify.h"

/*
 * handle data from network.
 * :param client: The per-client object.
 * :param remove: Function to call to close connection.
 * :returns: 0
 */
int data_on_connection(NetworkClient_t *client, callback_remove_handler remove) {
	int nread;
	int rc;
	char network_data[NETWORK_MAX + 1], *head, *tail;
	char *end;
	NotifyId id;
	char string[1024];
	unsigned long msg_id = UINT32_MAX;
	enum network_protocol version = client->version;
	int fd = client->fd;

	ioctl(fd, FIONREAD, &nread);

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "new connection data = %d", nread);

	if (nread == 0) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "%d failed, got 0. close connection to listener", fd);
		goto close;
	}
	if (nread >= NETWORK_MAX) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "%d failed, more than %d. close connection to listener", fd, NETWORK_MAX);
		goto close;
	}

	/* read the whole package */
	nread = read(fd, network_data, nread);
	network_data[nread] = '\0';

	for (head = network_data; head < network_data + nread; head = tail + 1) {
		tail = index(head, '\n');
		if (tail)
			*tail = '\0';
		else
			tail = network_data + nread;

		if (tail > head) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "line = [%s]", head);
		} else {
			continue;
		}

		if (!strncmp(head, "MSGID: ", 7)) {
			/* read message id  */
			msg_id = strtoul(head + 7, &end, 10);
			if (!head[7] || *end)
				goto failed;
		} else if (!strncmp(head, "Version: ", 9)) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: VERSION");

			version = strtoul(head + 9, &end, 10);
			if (!head[9] || *end)
				goto failed;
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "VERSION=%d", version);

			if (version < network_procotol_version) {
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "Forbidden VERSION=%d < %d, close connection to listener", version, network_procotol_version);
				goto close;
			} else if (version >= PROTOCOL_LAST) {
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "Future VERSION=%d", version);
				version = PROTOCOL_LAST - 1;
			}
			client->version = version;

			/* reset message id */
			msg_id = UINT32_MAX;
		} else if (!strncmp(head, "Capabilities: ", 14)) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: Capabilities");

			if (version > PROTOCOL_UNKNOWN) {
				snprintf(string, sizeof(string), "Version: %d\nCapabilities: \n\n", version);
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "SEND: %s", string);
				rc = send(fd, string, strlen(string), 0);
				if (rc < 0)
					goto failed;
			} else {
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "Capabilities recv, but no version line");
			}
		} else if (!strncmp(head, "GET_DN ", 7) && msg_id != UINT32_MAX && version > PROTOCOL_UNKNOWN && network_procotol_version < PROTOCOL_3) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: GET_DN");

			id = strtoul(head + 7, &end, 10);
			if (!head[7] || *end)
				goto failed;
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "id: %ld", id);

			if (id <= notify_last_id.id) {
				char *dn_string = NULL;

				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "try to read %ld from cache", id);

				/* try to read from cache */
				if ((dn_string = notifier_cache_get(id)) == NULL) {
					univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "%ld not found in cache", id);

					/* read from transaction file, because not in cache */
					if ((dn_string = notify_transcation_get_one_dn(id)) == NULL) {
						univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "%ld failed", id);
						/* TODO: maybe close connection? */

						univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "%d failed, close connection to listener", fd);
						goto close;
					}
				}

				if (dn_string != NULL) {
					snprintf(string, sizeof(string), "MSGID: %ld\n%s\n\n", msg_id, dn_string);
					univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "--> %d: [%s]", fd, string);
					rc = send(fd, string, strlen(string), 0);
					free(dn_string);
					if (rc < 0)
						goto failed;
				}
			} else {
				/* set wanted id */
				client->next_id = id;
				client->notify = 1;
				client->msg_id = msg_id;
			}

			msg_id = UINT32_MAX;
		} else if (!strncmp(head, "WAIT_ID ", 8) && msg_id != UINT32_MAX && version >= PROTOCOL_3) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: WAIT_ID");
			id = strtoul(head + 8, &end, 10);
			if (!head[8] || *end)
				goto failed;
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "id: %ld", id);

			if (id <= notify_last_id.id) {
				snprintf(string, sizeof(string), "MSGID: %ld\n%ld\n\n", msg_id, notify_last_id.id);
				rc = send(fd, string, strlen(string), 0);
				if (rc < 0)
					goto failed;
			} else {
				/* set wanted id */
				client->next_id = id;
				client->notify = 1;
				client->msg_id = msg_id;
			}

			msg_id = UINT32_MAX;
		} else if (!strcmp(head, "GET_ID") && msg_id != UINT32_MAX && version > 0) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: GET_ID");

			snprintf(string, sizeof(string), "MSGID: %ld\n%ld\n\n", msg_id, notify_last_id.id);
			rc = send(fd, string, strlen(string), 0);
			if (rc < 0)
				goto failed;

			msg_id = UINT32_MAX;
		} else if (!strcmp(head, "GET_SCHEMA_ID") && msg_id != UINT32_MAX && version > 0) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: GET_SCHEMA_ID");

			snprintf(string, sizeof(string), "MSGID: %ld\n%ld\n\n", msg_id, SCHEMA_ID);
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "--> %d: [%s]", fd, string);
			rc = send(fd, string, strlen(string), 0);
			if (rc < 0)
				goto failed;

			msg_id = UINT32_MAX;
		} else if (!strcmp(head, "ALIVE") && msg_id != UINT32_MAX && version > 0) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: ALIVE");

			snprintf(string, sizeof(string), "MSGID: %ld\nOKAY\n\n", msg_id);
			rc = send(fd, string, strlen(string), 0);
			if (rc < 0)
				goto failed;

			msg_id = UINT32_MAX;
		} else {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "Drop package [%s]", head);
		}
	}

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "END Package");

	return 0;

failed:
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "Failed [%s]", head);
close:
	network_client_dump1(client, UV_DEBUG_PROCESS);
	remove(fd);
	return 0;
}
