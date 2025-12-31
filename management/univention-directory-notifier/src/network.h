/*
 * Univention Directory Notifier
 *
 * SPDX-FileCopyrightText: 2004-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
} NetworkClient_t;

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
