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

#define ARRAY_SIZE(x) (sizeof(x) / sizeof(*(x)))
static char *current_server_list;
static struct server_list server_list[128];
static int server_list_entries = 0;
extern int backup_notifier;


/* returns true, if all servers in [list] have been contacted same often.
 * BUG: Connection attempts are currently not counted, so this always return 1.
 */
int suspend_connect(void)
{
	int i;
	for (i = 1; i < server_list_entries; i++) {
		if (server_list[i].conn_attemp != server_list[i-1].conn_attemp) {
			return 0;
		}
	}
	return 1;
}


/* Select LDAP server and notifier daemon.
 * 1. notifier/server : notifier/server/port
 * 2. @Master|Backup: ldap/master : ldap/master/port
 * 2. @*: ldap/backup[?] : ldap/backup/port, fallback: ldap/master : ldap/master/port
 * @param lp LDAP configuration object.
 */
int select_server(univention_ldap_parameters_t *lp)
{
	char *server_role;
	char *ldap_master;
	char *ldap_backups = NULL;
	char *notify_master;
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
		if (current_server_list && (strcmp(ldap_backups, current_server_list) != 0)) {
			free(current_server_list);
			current_server_list = NULL;
		}

		if (ldap_backups && !current_server_list) {
			char *str, *saveptr;
			/* rebuild list and initialize */
			current_server_list = strdup(ldap_backups);
			memset(server_list, 0, sizeof(server_list));
			server_list_entries = 0;
			for (str = ldap_backups; server_list_entries < ARRAY_SIZE(server_list); str = NULL) {
				char *name = strtok_r(str, " ", &saveptr);
				if (!name)
					break;
				if (!name[0])
					continue;
				server_list[server_list_entries++].server_name = name;
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "Backup found: %s", name);
			}
			if (server_list_entries >= ARRAY_SIZE(server_list))
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR,
						"Too many (more than %d) backup-servers found",
						ARRAY_SIZE(server_list));
			/* Append notifier on DC Master unless explicitly disabled */
			if (server_list_entries < ARRAY_SIZE(server_list) && !backup_notifier)
				server_list[server_list_entries++].server_name = strdup(ldap_master);
		}
		free(ldap_backups);

		if (server_list_entries) {
			/* dump server list */
			int i;
			for(i = 0; i < server_list_entries; i++) {
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

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "LDAP-Server is %s:%d", lp->host, lp->port);
	return 1;
}
