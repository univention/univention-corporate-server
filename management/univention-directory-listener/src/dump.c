/*
 * Univention Directory Listener
 *  header information for base64.c
 *  tool to dump the cache.
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

#define _GNU_SOURCE /* asprintf */

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

char *cache_dir = "/var/lib/univention-directory-listener";

int INIT_ONLY=0;

void usage(void)
{
	fprintf(stderr, "Usage: univention-directory-listener-dump [options]\n");
	fprintf(stderr, "Options:\n");
	fprintf(stderr, "   -d   debugging\n");
	fprintf(stderr, "   -c   Listener cache path\n");
	fprintf(stderr, "   -r   print broken entries only (as far as that's possible)\n");
	fprintf(stderr, "   -O   dump cache to file (default is stdout)\n");
}

int main(int argc, char* argv[])
{
	int debugging = 0, broken_only = 0, id_only = 0;
	char *output_file = NULL;
	FILE *fp;
	int rv;
	DBC *cur;
	char *dn;
	CacheEntry entry;

	univention_debug_init("stderr", 1, 1);

	/* parse arguments */
	for (;;) {
		int c;

		c = getopt(argc, argv, "d:c:O:ri");
		if (c < 0)
			break;
		switch (c) {
		case 'd':
			debugging=atoi(optarg);
			break;
		case 'c':
			cache_dir=strdup(optarg);
			break;
		case 'O':
			if (strcmp(optarg, "-") != 0)
				output_file=strdup(optarg);
			break;
		case 'r':
			broken_only=1;
			break;
#ifdef WITH_DB42
		case 'i':
			id_only=1;
			break;
#endif
		default:
			usage();
			exit(1);
		}
	}
	
	if (debugging > 1) {
		univention_debug_set_level(UV_DEBUG_LISTENER, UV_DEBUG_ALL);
		univention_debug_set_level(UV_DEBUG_LDAP, UV_DEBUG_ALL);
		univention_debug_set_level(UV_DEBUG_KERBEROS, UV_DEBUG_ALL);
	} else if ( debugging > 0 ) {
		univention_debug_set_level(UV_DEBUG_LISTENER, UV_DEBUG_INFO);
		univention_debug_set_level(UV_DEBUG_LDAP, UV_DEBUG_INFO);
		univention_debug_set_level(UV_DEBUG_KERBEROS, UV_DEBUG_INFO);
	} else {
		univention_debug_set_level(UV_DEBUG_LISTENER, UV_DEBUG_ERROR);
		univention_debug_set_level(UV_DEBUG_LDAP, UV_DEBUG_ERROR);
		univention_debug_set_level(UV_DEBUG_KERBEROS, UV_DEBUG_ERROR);
	}

	if (output_file) {
		fp = fopen(output_file, "w");
	} else {
		fp = stdout;
	}
	if (fp == NULL) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR,
			"Couldn't open dump file");
		exit(1);
	}
	if (cache_init() != 0)
		exit(1);

#ifdef WITH_DB42
	if (id_only) {

		CacheMasterEntry master_entry;
		cache_get_master_entry(&master_entry);

		printf("%ld %ld\n", master_entry.id, master_entry.schema_id);
		
	} else {

	cache_print_entries("uid=b95152,cn=users,dc=olb,dc=de");

	exit(0);
#endif
		
	for (rv=cache_first_entry(&cur, &dn, &entry); rv != DB_NOTFOUND;
			rv=cache_next_entry(&cur, &dn, &entry)) {
		if ((rv == 0 && !broken_only) || (rv == -1 && broken_only)) {
			cache_dump_entry(dn, &entry, fp);
			cache_free_entry(&dn, &entry);
			fprintf(fp, "\n");
		}
		if (rv < -1) break;
	}
	cache_free_cursor(cur);

#ifdef WITH_DB42
	}
#endif
	
	cache_close();

	return 0;
}
