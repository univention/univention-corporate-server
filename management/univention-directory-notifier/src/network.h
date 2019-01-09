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
#ifndef __NETWORK_H__
#define __NETWORK_H__

#include <stddef.h>
#include <univention/debug.h>

#include "cache.h"

#define NETWORK_MAX 8192

struct network_client;
typedef struct network_client NetworkClient_t;

typedef int (*callback_remove_handler)(int fd);
typedef int (*callback_handler)(NetworkClient_t *client, callback_remove_handler);

struct network_client {
	int fd;
	callback_handler handler;
	int notify;
	int version;
	NotifyId next_id;
	unsigned long msg_id;
	struct network_client *next;
};

int network_client_add(int fd, callback_handler handler, int notify);

typedef void (*callback_check)(void);
int network_client_main_loop(callback_check check_callbacks);
int network_client_init(int port);

void network_client_dump1(NetworkClient_t *client, enum uv_debug_level level);
int network_client_dump();

int network_client_all_write(NotifyId id, char *buf, size_t l_buf);
int network_client_check_clients(NotifyId last_known_id);

#endif
