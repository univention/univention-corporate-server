/*
 * Univention Directory Listener
 *  verify that Listener DB and local LDAP match
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

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <fcntl.h>
#include <dirent.h>
#include <pwd.h>
#include <sys/types.h>
#include <ldap.h>

#include <univention/debug.h>

#include "cache.h"
#include "common.h"
#include "utils.h"

int INIT_ONLY = 0;

struct dn {
	char *dn;
	struct dn *next;
};
static struct dn *dns = NULL;


static void add_dn(char *dn) {
	struct dn *new = malloc(sizeof(struct dn));
	new->dn = strdup(dn);
	new->next = dns;
	dns = new;
}


static int has_dn(char *dn) {
	struct dn *cur;
	for (cur = dns; cur != NULL; cur = cur->next) {
		if (strcmp(dn, cur->dn) == 0) {
			return 1;
		}
	}
	return 0;
}


static void compare_entries(char *dn, CacheEntry *entry, LDAP *ld, LDAPMessage *ldap_entry) {
	CacheEntry lentry;
	char **changes;
	char **cur;

	cache_new_entry_from_ldap(NULL, &lentry, ld, ldap_entry);
	changes = cache_entry_changed_attributes(entry, &lentry);

	for (cur = changes; cur != NULL && *cur != NULL; cur++) {
		int i;
		struct berval **values;

		if (changes - cur == 0)
			printf("E: %s:\n", dn);
		printf("E:     %s differs\n", *cur);

		for (i = 0; entry->attributes != NULL && entry->attributes[i] != NULL; i++) {
			if (strcmp(entry->attributes[i]->name, *cur) == 0)
				break;
		}
		if (entry->attributes == NULL || entry->attributes[i] == NULL) {
			printf("E:         CACHE = []\n");
		} else {
			int j;
			printf("E:         CACHE = [");
			for (j = 0; entry->attributes[i]->values && entry->attributes[i]->values[j] != NULL; j++) {
				printf(j == 0 ? "%s" : ", %s", entry->attributes[i]->values[j]);
			}
			printf("]\n");
		}

		printf("E:         LDAP = [");
		values = ldap_get_values_len(ld, ldap_entry, *cur);
		for (i = 0; values != NULL && values[i] != NULL && values[i]->bv_val != NULL; i++) {
			printf(i == 0 ? "%s" : ", %s", values[i]->bv_val);
		}
		ldap_value_free_len(values);
		printf("]\n");
	}

	free(changes);
}


static void usage(void) {
	fprintf(stderr, "Usage: univention-directory-listener-verify [options]\n");
	fprintf(stderr, "Options:\n");
	fprintf(stderr, "   -d   debugging\n");
	fprintf(stderr, "   -c   Listener cache path\n");
	fprintf(stderr, "   -D   LDAP bind dn (should be updatedn)\n");
	fprintf(stderr, "   -w   LDAP bind password\n");
	fprintf(stderr, "   -b   LDAP base dn\n");
}


int main(int argc, char *argv[]) {
	int debugging = 0;
	char *binddn = NULL;
	char *bindpw = NULL;
	char *basedn = NULL;
	int rv;
	MDB_cursor *id2entry_read_cursor_p = NULL;
	MDB_cursor *id2dn_read_cursor_p = NULL;
	char *dn;
	CacheEntry entry;
	LDAP *ld;
	LDAPMessage *res;
	char *attrs[] = {LDAP_ALL_USER_ATTRIBUTES, LDAP_ALL_OPERATIONAL_ATTRIBUTES, NULL};
	int attrsonly0 = 0;
	LDAPControl **serverctrls = NULL;
	LDAPControl **clientctrls = NULL;
	struct timeval timeout = {
	    .tv_sec = ldap_timeout_scans(), .tv_usec = 0,
	};
	int sizelimit0 = 0;
	struct berval cred;
	char cache_mdb_dir[PATH_MAX];

	univention_debug_init("stderr", 1, 1);

	/* parse arguments */
	for (;;) {
		int c;

		c = getopt(argc, argv, "d:c:D:w:b:");
		if (c < 0)
			break;
		switch (c) {
		case 'd':
			debugging = atoi(optarg);
			break;
		case 'c':
			cache_dir = strdup(optarg);
			break;
		case 'D':
			binddn = strdup(optarg);
			break;
		case 'w':
			bindpw = strdup(optarg);
			break;
		case 'b':
			basedn = strdup(optarg);
			break;
		default:
			usage();
			exit(1);
		}
	}
	if (binddn == NULL || bindpw == NULL || basedn == NULL) {
		usage();
		exit(1);
	}

	if (debugging > 1) {
		univention_debug_set_level(UV_DEBUG_LISTENER, UV_DEBUG_ALL);
		univention_debug_set_level(UV_DEBUG_LDAP, UV_DEBUG_ALL);
	} else if (debugging > 0) {
		univention_debug_set_level(UV_DEBUG_LISTENER, UV_DEBUG_INFO);
		univention_debug_set_level(UV_DEBUG_LDAP, UV_DEBUG_INFO);
	} else {
		univention_debug_set_level(UV_DEBUG_LISTENER, UV_DEBUG_ERROR);
		univention_debug_set_level(UV_DEBUG_LDAP, UV_DEBUG_ERROR);
	}

	if (ldap_initialize(&ld, "ldapi:///") != LDAP_SUCCESS) {
		fprintf(stderr, "E: Could not connect to ldapi:///\n");
		ldap_unbind_ext(ld, NULL, NULL);
		exit(1);
	}

	if (bindpw == NULL) {
		cred.bv_val = NULL;
		cred.bv_len = 0;
	} else {
		cred.bv_val = bindpw;
		cred.bv_len = strlen(bindpw);
	}
	if (ldap_sasl_bind_s(ld, binddn, LDAP_SASL_SIMPLE, &cred, serverctrls, clientctrls, NULL) != LDAP_SUCCESS) {
		fprintf(stderr, "E: Could not bind to LDAP server\n");
		exit(1);
	}


	rv = snprintf(cache_mdb_dir, PATH_MAX, "%s/cache", cache_dir);
	if (rv < 0 || rv >= PATH_MAX)
		abort();
	if (cache_init(cache_mdb_dir, MDB_RDONLY) != 0)
		exit(1);

	for (rv = cache_first_entry(&id2entry_read_cursor_p, &id2dn_read_cursor_p, &dn, &entry); rv != MDB_NOTFOUND; rv = cache_next_entry(&id2entry_read_cursor_p, &id2dn_read_cursor_p, &dn, &entry)) {
		if (rv < -1)
			break;

		if (has_dn(dn)) {
			printf("E: duplicate entry: %s\n", dn);
		}

		if ((rv = ldap_search_ext_s(ld, dn, LDAP_SCOPE_BASE, "(objectClass=*)", attrs, attrsonly0, serverctrls, clientctrls, &timeout, sizelimit0, &res)) == LDAP_NO_SUCH_OBJECT) {
			printf("W: %s only in cache\n", dn);
		} else if (rv != LDAP_SUCCESS) {
			printf("E: could not receive %s from LDAP\n", dn);
		} else {
			LDAPMessage *first;
			first = ldap_first_entry(ld, res);
			compare_entries(dn, &entry, ld, first);
			ldap_msgfree(res);
		}
		add_dn(dn);
	}
	cache_free_cursor(id2entry_read_cursor_p, id2dn_read_cursor_p);

	if ((rv = ldap_search_ext_s(ld, basedn, LDAP_SCOPE_SUBTREE, "(objectClass=*)", attrs, attrsonly0, serverctrls, clientctrls, &timeout, sizelimit0, &res)) != LDAP_SUCCESS) {
		printf("E: ldapsearch failed\n");
		exit(1);
	} else {
		LDAPMessage *cur;
		for (cur = ldap_first_entry(ld, res); cur != NULL; cur = ldap_next_entry(ld, cur)) {
			char *dn = ldap_get_dn(ld, cur);
			if (has_dn(dn))
				continue;

			if ((rv = cache_get_entry(dn, &entry)) == MDB_NOTFOUND) {
				printf("E: %s only in LDAP\n", dn);
			} else if (rv != 0) {
				printf("E: error reading %s from cache", dn);
				exit(1);
			}
			compare_entries(dn, &entry, ld, cur);
			ldap_memfree(dn);
			cache_free_entry(NULL, &entry);
		}
		ldap_msgfree(res);
	}

	cache_close();

	return 0;
}
