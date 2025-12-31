/*
 * Univention Directory Listener
 *  select_server.c
 *
 * SPDX-FileCopyrightText: 2004-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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


/* Select LDAP server and notifier daemon.
 * 1. notifier/server : notifier/server/port
 * 2. @Primary|Backup: ldap/master : ldap/master/port
 * 2. @*: ldap/backup[?] : ldap/backup/port, fallback: ldap/master : ldap/master/port
 * @param lp LDAP configuration object.
 *
 * .. warning::
 *
 *    notifier and LDAP server must belong to the same host. Otherwise the
 *    notifier might reference entries, which are not yet correctly replicated
 *    to the LDAP server. This leads to inconsistencies.
 */
void select_server(univention_ldap_parameters_t *lp) {
	static unsigned seed = 0;
	char *server_role = NULL;
	char *ldap_master = NULL;
	int ldap_master_port;

	if (lp->host) {
		free(lp->host);
		lp->host = NULL;
	}

	char *notify_master = univention_config_get_string("notifier/server");
	if (notify_master != NULL) {
		lp->host = notify_master;
		int notify_port = univention_config_get_int("notifier/server/port");
		if (notify_port > 0)
			lp->port = notify_port;
		goto result;
	}

	server_role = univention_config_get_string("server/role");
	if (!server_role) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "UCRV 'server/role' is not set");
		abort();
	}
	ldap_master = univention_config_get_string("ldap/master");
	if (!ldap_master) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "UCRV 'ldap/master' is not set");
		abort();
	}
	ldap_master_port = univention_config_get_int("ldap/master/port");

	/* if this is a Primary or Backup return ldap/master */
	if (!strcmp(server_role, "domaincontroller_master") || !strcmp(server_role, "domaincontroller_backup")) {
		lp->host = strdup(ldap_master);
		if (ldap_master_port > 0)
			lp->port = ldap_master_port;
		goto result;
	} else {
		char *ldap_backups = univention_config_get_string("ldap/backup");

		/* list of Backups and Primary still up-to-date? */
		if (current_server_list && ldap_backups && (strcmp(ldap_backups, current_server_list) != 0)) {
			free(current_server_list);
			current_server_list = NULL;
		}

		if (ldap_backups && !current_server_list) {
			char *str, *saveptr = NULL;
			/* rebuild list and initialize */
			current_server_list = strdup(ldap_backups);
			while (server_list_entries > 0)
				free(server_list[--server_list_entries].server_name);
			memset(server_list, 0, sizeof(server_list));
			for (str = ldap_backups; server_list_entries < ARRAY_SIZE(server_list); str = NULL) {
				char *name = strtok_r(str, " ", &saveptr);
				if (!name)
					break;
				if (!name[0])
					continue;
				server_list[server_list_entries++].server_name = strdup(name);
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "Backup found: %s", name);
			}
			if (server_list_entries >= ARRAY_SIZE(server_list))
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Too many (more than %zd) backup-servers found", ARRAY_SIZE(server_list));
			/* Append notifier on Primary Directory Node unless explicitly disabled */
			if (server_list_entries < ARRAY_SIZE(server_list) && !backup_notifier)
				server_list[server_list_entries++].server_name = strdup(ldap_master);
		}
		free(ldap_backups);

		if (server_list_entries) {
			/* dump server list */
			int i;
			for (i = 0; i < server_list_entries; i++) {
				fprintf(stderr, "%d: %s\n", i, server_list[i].server_name);
			}
			/* randomize start point of server search */
			if (!seed) {
				seed = getpid() * time(NULL);
				srandom(seed);
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "rands with seed %ud ", seed);
			}
			int randval = random() % server_list_entries;
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "randval = %d ", randval);

			lp->host = strdup(server_list[randval].server_name);
			if (!strcmp(lp->host, ldap_master)) {
				if (ldap_master_port > 0)
					lp->port = ldap_master_port;
			} else {
				int backup_port = univention_config_get_int("ldap/backup/port");
				if (backup_port > 0)
					lp->port = backup_port;
			}
		} else {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "No Backup found, server is ldap/master");
			lp->host = strdup(ldap_master);
			if (ldap_master_port > 0)
				lp->port = ldap_master_port;
		}
	}

result:
	free(ldap_master);
	free(server_role);

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "Notifier/LDAP server is %s:%d", lp->uri ? lp->uri : lp->host ? lp->host : "NULL", lp->port);
}
