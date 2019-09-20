/*
 * Univention Directory Notifier
 *
 * Copyright 2004-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */

#define __USE_GNU

#include <sys/types.h>
#include <sys/socket.h>
#include <stdio.h>
#include <netinet/in.h>
#include <sys/time.h>
#include <sys/ioctl.h>
#include <sys/un.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdint.h>

#include <univention/debug.h>

#include "notify.h"
#include "network.h"
#include "cache.h"

extern fd_set readfds;

extern NotifyId_t notify_last_id;

extern unsigned long SCHEMA_ID;


/* read one line from network packages*/

int get_network_line(char *packet, char *network_line)
{
	int i=0;

	memset(network_line, 0, 8192);

	while ( packet[i] != '\0' && packet[i] != '\n' ) {

		network_line[i]=packet[i];
		i+=1;
	}

	if ( packet[i] == '\0' ) {
		return 0;
	}

	if ( i == 0 ) {
		network_line[i]='\0';
	}

	network_line[i+1]='\0';

	return 1;
}

int data_on_connection(int fd, callback_remove_handler remove)
{
	int nread;
	int rc;
	char *network_packet;
	char network_line[8192];
	char *p;
	unsigned long id;

	char string[1024];
	unsigned long msg_id = UINT32_MAX;
	enum network_protocol version = network_client_get_version(fd);

	ioctl(fd, FIONREAD, &nread);

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "new connection data = %d\n",nread);

	if(nread == 0)
	{
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "%d failed, got 0 close connection to listener ", fd);
		close(fd);
		FD_CLR(fd, &readfds);
		remove(fd);
		network_client_dump ();
		return 0;
	}


	if ( nread >= 8192 ) {

		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "%d failed, more than 8192 close connection to listener ", fd);
		close(fd);
		FD_CLR(fd, &readfds);
		remove(fd);

		return 0;
	}

	/* read the whole package */
	network_packet=malloc((nread+1) * sizeof(char));
	read(fd, network_packet, nread);
	network_packet[nread]='\0';

	memset(network_line, 0, 8192);
	p=network_packet;

	while ( get_network_line(p, network_line) ) {

		if ( strlen(network_line) > 0 ) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "line = [%s]",network_line);
		}

		
		if ( !strncmp(network_line, "MSGID: ", strlen("MSGID: ")) ) {
			/* read message id  */

			msg_id=strtoul(&(network_line[strlen("MSGID: ")]), NULL, 10);

			p+=strlen(network_line);


		} else if ( !strncmp(network_line, "Version: ", strlen("Version: ")) ) {
			char *head = network_line, *end;

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
			network_client_set_version(fd, version);
			
			/* reset message id */
			msg_id = UINT32_MAX;

			p+=strlen(network_line);


		} else if ( !strncmp(network_line, "Capabilities: ", strlen("Capabilities: ")) ) {

			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: Capabilities");

			if ( version > PROTOCOL_UNKNOWN ) {

				memset(string, 0, sizeof(string));
				
				snprintf(string, sizeof(string), "Version: %d\nCapabilities: \n\n", version);

				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "SEND: %s", string);
				rc = send(fd, string, strlen(string), 0);
				if (rc < 0)
					goto failed;
			} else {
				
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "Capabilities recv, but no version line");
				
			}

			p+=strlen(network_line);


		} else if ( !strncmp(network_line, "GET_DN ", strlen("GET_DN ")) && msg_id != UINT32_MAX && version > PROTOCOL_UNKNOWN && version < PROTOCOL_3) {

			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: GET_DN");

			id=strtoul(&(network_line[strlen("GET_DN ")]), NULL, 10);

			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "id: %ld",id);

			if ( id <= notify_last_id.id) {

				char *dn_string = NULL;

				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "try to read %ld from cache", id);

				/* try to read from cache */
				if ( (dn_string = notifier_cache_get(id)) == NULL ) {

					univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "%ld not found in cache", id);

					univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "%ld get one dn", id);

					/* read from transaction file, because not in cache */
					if( (dn_string=notify_transcation_get_one_dn ( id )) == NULL ) {

						univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "%ld failed ", id);
						/* TODO: maybe close connection? */

						univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "%d failed, close connection to listener ", fd);
						close(fd);
						FD_CLR(fd, &readfds);
						remove(fd);

						return 0;
					}
				}

				if ( dn_string != NULL ) {

					snprintf(string, sizeof(string), "MSGID: %ld\n%s\n\n",msg_id,dn_string);

					univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "--> %d: [%s]",fd, string);
					rc = send(fd, string, strlen(string), 0);
					free(dn_string);
					if (rc < 0)
						goto failed;
				}


			} else {
				/* set wanted id */

				network_client_set_next_id(fd, id);
				network_client_set_msg_id(fd, msg_id);

			}

			p+=strlen(network_line)+1;
			msg_id = UINT32_MAX;

		} else if (!strncmp(p, "WAIT_ID ", 8) && msg_id != UINT32_MAX && version >= PROTOCOL_3) {
			char *head = network_line, *end;
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
				network_client_set_next_id(fd, id);
				network_client_set_msg_id(fd, msg_id);
			}

			p += strlen(network_line) + 1;
			msg_id = UINT32_MAX;

		} else if ( !strncmp(network_line, "GET_ID", strlen("GET_ID")) && msg_id != UINT32_MAX  && network_client_get_version(fd) > 0) {

			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: GET_ID");

			memset(string, 0, sizeof(string));

			snprintf(string, sizeof(string), "MSGID: %ld\n%ld\n\n",msg_id,notify_last_id.id);
			rc = send(fd, string, strlen(string), 0);
			if (rc < 0)
				goto failed;

			p+=strlen(network_line)+1;
			msg_id = UINT32_MAX;


		} else if ( !strncmp(network_line, "GET_SCHEMA_ID", strlen("GET_SCHEMA_ID")) && msg_id != UINT32_MAX  && network_client_get_version(fd) > 0) {

			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: GET_SCHEMA_ID");

			memset(string, 0, sizeof(string));

			snprintf(string, sizeof(string), "MSGID: %ld\n%ld\n\n",msg_id,SCHEMA_ID);

			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "--> %d: [%s]",fd, string);
			rc = send(fd, string, strlen(string), 0);
			if (rc < 0)
				goto failed;

			p+=strlen(network_line)+1;
			msg_id = UINT32_MAX;


		} else if ( !strncmp(network_line, "ALIVE", strlen("ALIVE")) && msg_id != UINT32_MAX  && network_client_get_version(fd) > 0) {

			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "RECV: ALIVE");

			snprintf(string, sizeof(string), "MSGID: %ld\nOKAY\n\n",msg_id);
			rc = send(fd, string, strlen(string), 0);
			if (rc < 0)
				goto failed;

			p+=strlen(network_line)+1;
			msg_id = UINT32_MAX;

		} else {

			p+=strlen(network_line);

			if (strlen(network_line) == 0 ) {
				p+=1;
 			} else {
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Drop package [%s]", network_line);
			}

		}
	}

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "END Package");
	

	network_client_dump ();

	return 0;

failed:
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "Failed parsing [%s]", p);
close:
	close(fd);
	FD_CLR(fd, &readfds);
	remove(fd);
	return 0;
}

