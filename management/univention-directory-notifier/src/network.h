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

#ifndef __NETWORK_H__
#define __NETWORK_H__

typedef int (*callback_remove_handler)(int fd);
typedef int (*callback_handler)(int fd, callback_remove_handler);

enum network_protocol {
	PROTOCOL_UNKNOWN = 0,
	PROTOCOL_1,
	PROTOCOL_2,
	PROTOCOL_3,
	PROTOCOL_LAST  // must always be last entry
};

typedef struct network_client {
	int fd;

	callback_handler handler;

	int notify;

	enum network_protocol version;

	unsigned long next_id;

	unsigned long msg_id;

	struct network_client *next;

}NetworkClient_t;

int network_create_socket( int port );

int network_client_del ( int fd );

int network_client_main_loop ( );
int network_client_init ( int port );

int network_client_dump ( );

int network_client_all_write ( unsigned long id, char *buf, long l_buf);
int network_client_set_next_id( int fd, unsigned long id );
int network_client_set_msg_id( int fd, unsigned long msg_id );
int network_client_set_version( int fd, int version );
int network_client_get_version( int fd );
int network_client_check_clients ( unsigned long last_known_id ) ;

extern enum network_protocol network_procotol_version;

#endif

