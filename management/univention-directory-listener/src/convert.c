/*
 * Univention Directory Listener
 *  tool to convert the cache.
 *
 * Copyright 2016-2019 Univention GmbH
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
#include <fcntl.h>
#include <dirent.h>
#include <pwd.h>
#include <sys/types.h>

#include <univention/debug.h>

#include "cache_bdb.h"
#include "cache.h"
#include "common.h"

static void exit_if_cache_mdb_exists(void) {
	int rv;
	char cache_mdb_filename[PATH_MAX];

	rv = snprintf(cache_mdb_filename, PATH_MAX, "%s/cache/data.mdb", cache_dir);
	if (rv < 0 || rv >= PATH_MAX)
		abort();

	if (access(cache_mdb_filename, F_OK) != -1) {
		LOG(ERROR, "%s already exists", cache_mdb_filename);
		exit(EXIT_FAILURE);
	}
}

static void usage(void) {
	fprintf(stderr, "Usage: univention-directory-listener-convert [options]\n");
	fprintf(stderr, "Options:\n");
	fprintf(stderr, "   -d   debugging\n");
	fprintf(stderr, "   -c   Listener cache path\n");
}


int main(int argc, char *argv[]) {
	int debugging = 0;
	int rv;
	DBC *cur;
	char *dn = NULL;
	CacheEntry entry;
	char cache_mdb_dir[PATH_MAX];

	univention_debug_init("stderr", 1, 1);

	/* parse arguments */
	for (;;) {
		int c;

		c = getopt(argc, argv, "d:c:");
		if (c < 0)
			break;
		switch (c) {
		case 'd':
			debugging = atoi(optarg);
			break;
		case 'c':
			cache_dir = strdup(optarg);
			bdb_cache_dir = strdup(optarg);
			break;
		default:
			usage();
			exit(1);
		}
	}

	if (debugging > 1) {
		univention_debug_set_level(UV_DEBUG_LISTENER, UV_DEBUG_ALL);
		univention_debug_set_level(UV_DEBUG_LDAP, UV_DEBUG_ALL);
		univention_debug_set_level(UV_DEBUG_KERBEROS, UV_DEBUG_ALL);
	} else if (debugging > 0) {
		univention_debug_set_level(UV_DEBUG_LISTENER, UV_DEBUG_INFO);
		univention_debug_set_level(UV_DEBUG_LDAP, UV_DEBUG_INFO);
		univention_debug_set_level(UV_DEBUG_KERBEROS, UV_DEBUG_INFO);
	} else {
		univention_debug_set_level(UV_DEBUG_LISTENER, UV_DEBUG_ERROR);
		univention_debug_set_level(UV_DEBUG_LDAP, UV_DEBUG_ERROR);
		univention_debug_set_level(UV_DEBUG_KERBEROS, UV_DEBUG_ERROR);
	}

	exit_if_cache_mdb_exists();

	rv = bdb_cache_lock();
	rv = cache_lock();

	if (bdb_cache_init() != 0)
		exit(1);

	printf("Converting listener cache to LMDB\n");
	rv = snprintf(cache_mdb_dir, PATH_MAX, "%s/cache", cache_dir);
	if (rv < 0 || rv >= PATH_MAX)
		abort();
	if (cache_init(cache_mdb_dir, 0) != 0)
		exit(1);

	rv = bdb_cache_get_master_entry(&cache_master_entry);
	if (rv) {
		printf("notifier_id not found in BDB cache, falling back to notifier_id file\n");
		cache_get_int("notifier_id", &cache_master_entry.id, -1);
		if (cache_master_entry.id == -1) {
			LOG(ERROR, "cannot determine current ID");
			LOG(ERROR, "Aborting conversion");
			return 1;
		}

		printf("schema_id not found in BDB cache, falling back to schema/id/id file\n");
		cache_get_schema_id(&cache_master_entry.schema_id, 0);
	}
	printf("cached notifier_id:\t%ld\n", cache_master_entry.id);
	printf("cached schema_id:\t%ld\n", cache_master_entry.schema_id);
	rv = cache_update_master_entry(&cache_master_entry);

	for (rv = bdb_cache_first_entry(&cur, &dn, &entry); rv != DB_NOTFOUND; rv = bdb_cache_next_entry(&cur, &dn, &entry)) {
		if (rv != 0) {
			LOG(ERROR, "error while reading database");
		} else if ((rv = cache_update_entry_lower(0, dn, &entry)) != MDB_SUCCESS) {
			LOG(ERROR, "error while writing to database");
		}
		cache_free_entry(&dn, &entry);
		if (rv < -1)
			break;
	}

	bdb_cache_free_cursor(cur);

	bdb_cache_close();
	cache_close();

	return 0;
}
