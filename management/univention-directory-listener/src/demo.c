/*
 * Univention Directory Listener
 *  demo program for the notifier client API.
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
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include <univention/debug.h>

#include "network.h"
#include "common.h"

int INIT_ONLY=0;

void usage(const char *name)
{
	fprintf(stderr, "Usage: %s <HOST> get_id\n"
			"       %s <HOST> get_schema_id\n"
			"       %s <HOST> get_dn <ID>\n",
			name, name, name);
}

int main(int argc, char *argv[])
{
	NotifierID id;
	NotifierEntry entry;
	int c;

	while ((c = getopt(argc, argv, "d")) != -1) {
		switch (c) {
		case 'd':
			univention_debug_init("stderr", 0, 0);
			univention_debug_set_level(UV_DEBUG_LISTENER, UV_DEBUG_ALL);
			break;
		default:
			usage(argv[0]);
			return 1;
		}
	}
	
	if (optind > argc-2) {
		printf("x\n");
		usage(argv[0]);
		return 1;
	}
	
	if (notifier_client_new(NULL, argv[optind], 1) != 0) {
		fprintf(stderr, "Could not connect to notifier\n");
		return 1;
	}

	if (strcmp(argv[optind+1], "get_id") == 0) {
		notifier_get_id_s(NULL, &id);
		printf("%ld\n", id);
	} else if (strcmp(argv[optind+1], "get_schema_id") == 0) {
		notifier_get_schema_id_s(NULL, &id);
		printf("%ld\n", id);
	} else if (strcmp(argv[optind+1], "get_dn") == 0) {
		int msgid;
		long getid;

		if (optind > argc-3) {
			usage(argv[0]);
			return 1;
		}

		if (argv[optind+2][strlen(argv[optind+2])-1] == '-') {
			notifier_get_id_s(NULL, &id);
			getid = id-atoi(argv[optind+2]);
		} else {
			getid = atoi(argv[optind+2]);
		}
		
		msgid = notifier_get_dn(NULL, getid);
		notifier_get_dn_result(NULL, msgid, &entry);

		printf("%ld %s\n", entry.id, entry.dn);
	} else {
		usage(argv[0]);
		return 1;
	}
	
	return 0;
}
