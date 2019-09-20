/*
 * Univention Directory Listener
 *  header information for base64.c
 *  tool to dump the cache.
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

#include <univention/debug.h>

#include "cache.h"
#include "common.h"

int INIT_ONLY = 0;


static void usage(void) {
	fprintf(stderr, "Usage: univention-directory-listener-dump [options]\n");
	fprintf(stderr, "Options:\n");
	fprintf(stderr, "   -d   debugging\n");
	fprintf(stderr, "   -c   Listener cache path\n");
	fprintf(stderr, "   -r   print broken entries only (as far as that's possible)\n");
	fprintf(stderr, "   -O   dump cache to file (default is stdout)\n");
	fprintf(stderr, "   -i   ID only\n");
}


int main(int argc, char *argv[]) {
	int debugging = 0, broken_only = 0;
	int id_only = 0;
	char *output_file = NULL;
	FILE *fp;
	int rv;
	MDB_cursor *id2entry_read_cursor_p = NULL;
	MDB_cursor *id2dn_read_cursor_p = NULL;
	char *dn = NULL;
	CacheEntry entry;
	char cache_mdb_dir[PATH_MAX];

	univention_debug_init("stderr", 1, 1);

	/* parse arguments */
	for (;;) {
		int c;

		c = getopt(argc, argv, "d:c:O:ri");
		if (c < 0)
			break;
		switch (c) {
		case 'd':
			debugging = atoi(optarg);
			break;
		case 'c':
			cache_dir = strdup(optarg);
			break;
		case 'O':
			if (strcmp(optarg, "-") != 0)
				output_file = strdup(optarg);
			break;
		case 'r':
			broken_only = 1;
			break;
		case 'i':
			id_only = 1;
			break;
		default:
			usage();
			exit(1);
		}
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

	if (output_file) {
		fp = fopen(output_file, "w");
	} else {
		fp = stdout;
	}
	if (fp == NULL) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Couldn't open dump file");
		exit(1);
	}
	rv = snprintf(cache_mdb_dir, PATH_MAX, "%s/cache", cache_dir);
	if (rv < 0 || rv >= PATH_MAX)
		abort();
	if (cache_init(cache_mdb_dir, MDB_RDONLY) != 0)
		exit(1);

	if (id_only) {
		cache_get_master_entry(&cache_master_entry);

		printf("%ld %ld\n", cache_master_entry.id, cache_master_entry.schema_id);
	} else {
		for (rv = cache_first_entry(&id2entry_read_cursor_p, &id2dn_read_cursor_p, &dn, &entry); rv != MDB_NOTFOUND; rv = cache_next_entry(&id2entry_read_cursor_p, &id2dn_read_cursor_p, &dn, &entry)) {
			if ((rv == 0 && !broken_only) || (rv == -1 && broken_only)) {
				cache_dump_entry(dn, &entry, fp);
				fprintf(fp, "\n");
			}
			cache_free_entry(&dn, &entry);
			if (rv < -1)
				break;
		}
		cache_free_cursor(id2entry_read_cursor_p, id2dn_read_cursor_p);
	}

	cache_close();

	return 0;
}
