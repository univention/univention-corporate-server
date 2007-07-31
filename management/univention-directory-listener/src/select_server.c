/*
 * Univention Directory Listener
 *  select_server.c
 *
 * Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include "select_server.h"
#include <univention/debug.h>
#include <univention/ldap.h>
#include <univention/config.h>

extern char *current_server_list;
extern struct server_list *server_list;
extern int server_list_entries;
extern int backup_notifier;
int maxnbackups = 128;


/* returns true, if all servers in [list] have been contacted same often */
int suspend_connect(struct server_list *list, int entries)
{
	int i = 0;
	int retval = 1;

	if (server_list != NULL) {
		if (entries < 2)
			retval = 1;

		for (i=1; i<entries; i++) {
			if (list[i].conn_attemp != list[i-1].conn_attemp) {
				retval = 0;
				break;
			}
		}
	}

	return retval;
}

char *select_server()
{
	char *server_hostname;
	char *server_role;
	char *ldap_master;
	char *ldap_backups = NULL;
	char *notify_master;
	int nbackups = 0;
	int i = 0;
	int randval = 0;
	struct server_list *retval = NULL;

	server_role = univention_config_get_string("server/role");
	ldap_master = univention_config_get_string("ldap/master");
	notify_master = univention_config_get_string("notifier/server");

	if ( notify_master  != NULL ) {
		return notify_master;
	}

	/* if this is a master or backup return ldap/master */
	if (!strcmp(server_role, "domaincontroller_master")) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
				 "We are %s, select ldap/master as LDAP-Server",
				 server_role);
		server_hostname = strdup(ldap_master);
	} else if (!strcmp(server_role, "domaincontroller_backup")) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
				 "We are %s, select ldap/master as LDAP-Server",
				 server_role);
		server_hostname = strdup(ldap_master);
	} else {
		ldap_backups = univention_config_get_string("ldap/backup");

		/* list of backups and master still up-to-date? */
		if ((current_server_list != NULL) && (strcmp(ldap_backups, current_server_list) != 0)) {
			free(current_server_list);
			current_server_list = NULL;
		}

		if ( ldap_backups != NULL ) {
			if ( current_server_list == NULL ) {
				/* rebuild list and initialize */
				current_server_list = strdup(ldap_backups);
				memset(server_list, 0, sizeof(struct server_list[maxnbackups+1]));

				server_list[nbackups].server_name = strtok(ldap_backups, " ");

				while (server_list[nbackups].server_name != NULL) {
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
							"Backup found: %s",
							server_list[nbackups].server_name);
					nbackups++;
					server_list[nbackups].server_name = strtok(NULL, " ");

					if ( nbackups >= maxnbackups-1 ) {
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR,
								"Too many (more than %d) backup-servers found",
								maxnbackups);
						break;
					}
				}

				if ( backup_notifier == 0 ) {
					/* last element in list is the master */
					server_list[nbackups].server_name = strdup(ldap_master);
					server_list_entries = nbackups + 1;
				} else {
					server_list_entries = nbackups;
				}
			}

			/* randomize start point of server search */
			unsigned seed = getpid() * time(NULL);
			srandom(seed);
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
					 "rands with seed %ud ", seed);
			randval = random() % server_list_entries;
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
					 "randval = %d ", randval);

			server_hostname = strdup(server_list[randval].server_name);
		} else {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
					 "No Backup found, server is ldap/master");
			server_hostname = strdup(ldap_master);
		}

	}

	free(ldap_master);
	free(server_role);

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "LDAP-Server is %s",
			 server_hostname);
	return server_hostname;
}
