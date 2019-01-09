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
#include <sys/select.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <univention/debug.h>

#include "cache.h"
#include "network.h"
#include "notify.h"

static int VERSION = 2;

extern fd_set readfds;

extern NotifyId_t notify_last_id;

extern unsigned long SCHEMA_ID;

/* read one line from network packages
 * :param packet: The network data.
 * :param network_line: Return buffer for line.
 * :returns: 0 on success, 1 on short lines.
 */
static int get_network_line(char *packet, char *network_line) {
	int i = 0;

	while (packet[i] != '\0' && packet[i] != '\n') {
		network_line[i] = packet[i];
		i += 1;
	}

	if (packet[i] == '\0') {
		return 0;
	}

	if (i == 0) {
		network_line[i] = '\0';
	}

	network_line[i + 1] = '\0';

	return 1;
}

/*
 * handle data from network.
 * :param client: The per-client object.
 * :param remove: Function to call to close connection.
 * :returns: 0
 */
int data_on_connection(NetworkClient_t *client, callback_remove_handler remove) {
	int nread;
	char *network_packet;
	char network_line[NETWORK_MAX];
	char *p;
	unsigned long id;
	char string[1024];
	unsigned long msg_id = UINT32_MAX;
	int version = client->version, fd = client->fd;

	ioctl(fd, FIONREAD, &nread);

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "new connection data = %d\n", nread);

	if (nread == 0) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "%d failed, got 0 close connection to listener ", fd);
		network_client_dump();
		goto close;
	}
	if (nread >= NETWORK_MAX) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "%d failed, more than %d close connection to listener ", fd, NETWORK_MAX);
		goto close;
	}

	/* read the whole package */
	network_packet = malloc((nread + 1) * sizeof(char));
	read(fd, network_packet, nread);
	network_packet[nread] = '\0';

	p = network_packet;

	while (get_network_line(p, network_line)) {
		if (strlen(network_line) > 0) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "line = [%s]", network_line);
		}

		if (!strncmp(network_line, "MSGID: ", strlen("MSGID: "))) {
			/* read message id  */
			msg_id = strtoul(&(network_line[strlen("MSGID: ")]), NULL, 10);

			p += strlen(network_line);
		} else if (!strncmp(network_line, "Version: ", strlen("Version: "))) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: VERSION");

			id = strtoul(&(network_line[strlen("Version: ")]), NULL, 10);

			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "VERSION=%ld", id);

			version = id < VERSION ? id : VERSION;
			client->version = version;

			/* reset message id */
			msg_id = UINT32_MAX;

			p += strlen(network_line);
		} else if (!strncmp(network_line, "Capabilities: ", strlen("Capabilities: "))) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: Capabilities");

			if (version > -1) {
				snprintf(string, sizeof(string), "Version: %d\nCapabilities: \n\n", version);

				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "SEND: %s", string);

				write(fd, string, strlen(string));
			} else {
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "Capabilities recv, but no version line");
			}

			p += strlen(network_line);
		} else if (!strncmp(network_line, "GET_DN ", strlen("GET_DN ")) && msg_id != UINT32_MAX && version > 0) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: GET_DN");

			id = strtoul(&(network_line[strlen("GET_DN ")]), NULL, 10);

			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "id: %ld", id);

			if (id <= notify_last_id.id) {
				char *dn_string = NULL;

				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "try to read %ld from cache", id);

				/* try to read from cache */
				if ((dn_string = notifier_cache_get(id)) == NULL) {
					univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "%ld not found in cache", id);

					univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "%ld get one dn", id);

					/* read from transaction file, because not in cache */
					if ((dn_string = notify_transcation_get_one_dn(id)) == NULL) {
						univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "%ld failed ", id);
						/* TODO: maybe close connection? */

						univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "%d failed, close connection to listener ", fd);
						goto close;
					}
				}

				if (dn_string != NULL) {
					snprintf(string, sizeof(string), "MSGID: %ld\n%s\n\n", msg_id, dn_string);

					univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "--> %d: [%s]", fd, string);

					write(fd, string, strlen(string));

					free(dn_string);
				}
			} else {
				/* set wanted id */
				client->next_id = id;
				client->notify = 1;
				client->msg_id = msg_id;
			}

			p += strlen(network_line) + 1;
			msg_id = UINT32_MAX;
		} else if (!strncmp(network_line, "GET_ID", strlen("GET_ID")) && msg_id != UINT32_MAX && version > 0) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: GET_ID");

			snprintf(string, sizeof(string), "MSGID: %ld\n%ld\n\n", msg_id, notify_last_id.id);

			write(fd, string, strlen(string));

			p += strlen(network_line) + 1;
			msg_id = UINT32_MAX;
		} else if (!strncmp(network_line, "GET_SCHEMA_ID", strlen("GET_SCHEMA_ID")) && msg_id != UINT32_MAX && version > 0) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: GET_SCHEMA_ID");

			snprintf(string, sizeof(string), "MSGID: %ld\n%ld\n\n", msg_id, SCHEMA_ID);

			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "--> %d: [%s]", fd, string);

			write(fd, string, strlen(string));

			p += strlen(network_line) + 1;
			msg_id = UINT32_MAX;
		} else if (!strncmp(network_line, "ALIVE", strlen("ALIVE")) && msg_id != UINT32_MAX && version > 0) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: ALIVE");

			snprintf(string, sizeof(string), "MSGID: %ld\nOKAY\n\n", msg_id);

			write(fd, string, strlen(string));

			p += strlen(network_line) + 1;
			msg_id = UINT32_MAX;
		} else {
			p += strlen(network_line);

			if (strlen(network_line) == 0) {
				p += 1;
			} else {
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Drop package [%s]", network_line);
			}
		}
	}

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "END Package");

	network_client_dump();

	return 0;

close:
	close(fd);
	FD_CLR(fd, &readfds);
	remove(fd);
	return 0;
}
