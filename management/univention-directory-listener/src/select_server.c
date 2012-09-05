/*
 * Univention Directory Listener
 *  select_server.c
 *
 * Copyright 2004-2012 Univention GmbH
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
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <time.h>
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

int select_server(univention_ldap_parameters_t *lp)
{
	char *server_role;
	char *ldap_master;
	char *ldap_backups = NULL;
	char *notify_master;
	int nbackups = 0;
	int randval = 0;
	int port = 0;

	notify_master = univention_config_get_string("notifier/server");

	if ( notify_master  != NULL ) {
		lp->host = notify_master;
		port = univention_config_get_int("notifier/server/port");
		if (port > 0)
			lp->port = port;
		return 0;
	}

	free (notify_master);

	server_role = univention_config_get_string("server/role");
	ldap_master = univention_config_get_string("ldap/master");

	/* if this is a master or backup return ldap/master */
	if (!strcmp(server_role, "domaincontroller_master")) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
				 "We are %s, select ldap/master as LDAP-Server",
				 server_role);
		lp->host = strdup(ldap_master);
		port = univention_config_get_int("ldap/master/port");
		if (port > 0)
			lp->port = port;
	} else if (!strcmp(server_role, "domaincontroller_backup")) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
				 "We are %s, select ldap/master as LDAP-Server",
				 server_role);
		lp->host = strdup(ldap_master);
		port = univention_config_get_int("ldap/master/port");
		if (port > 0)
			lp->port = port;
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

			int i;
			for(i=0;i<nbackups;i++) {
				fprintf(stderr, "%d: %s\n", i, server_list[i].server_name);
			}
			/* randomize start point of server search */
			unsigned seed = getpid() * time(NULL);
			srandom(seed);
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
					 "rands with seed %ud ", seed);
			randval = random() % server_list_entries;
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
					 "randval = %d ", randval);

			lp->host = strdup(server_list[randval].server_name);
			if ( !strcmp(lp->host, ldap_master) ){
				port = univention_config_get_int("ldap/master/port");
				if (port > 0)
					lp->port = port;
			} else {
				port = univention_config_get_int("ldap/backup/port");
				if (port > 0)
					lp->port = port;
			}
			free(ldap_backups);
		} else {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
					 "No Backup found, server is ldap/master");
			lp->host = strdup(ldap_master);
			port = univention_config_get_int("ldap/master/port");
			if (port > 0)
				lp->port = port;
		}

	}

	if (ldap_master != NULL)
		free(ldap_master);
	if (server_role != NULL)
		free(server_role);

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "LDAP-Server is %s", lp->host);
	return 1;
}
