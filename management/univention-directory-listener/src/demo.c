/*
 * Univention Directory Listener
 *  demo program for the notifier client API.
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
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include <univention/debug.h>

#include "network.h"
#include "common.h"

int INIT_ONLY = 0;


static void usage(const char *name) {
	fprintf(stderr, "Usage: %s <HOST> get_id\n"
	                "       %s <HOST> get_schema_id\n"
	                "       %s <HOST> get_dn <ID>\n",
	        name, name, name);
}


int main(int argc, char *argv[]) {
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

	if (optind > argc - 2) {
		fprintf(stderr, "Missing arguments\n");
		usage(argv[0]);
		return 1;
	}

	if (notifier_client_new(NULL, argv[optind], 1) != 0) {
		fprintf(stderr, "Could not connect to notifier\n");
		return 1;
	}

	if (strcmp(argv[optind + 1], "get_id") == 0) {
		notifier_get_id_s(NULL, &id);
		printf("%ld\n", id);
	} else if (strcmp(argv[optind + 1], "get_schema_id") == 0) {
		notifier_get_schema_id_s(NULL, &id);
		printf("%ld\n", id);
	} else if (strcmp(argv[optind + 1], "get_dn") == 0) {
		int msgid;
		long getid;

		if (optind > argc - 3) {
			usage(argv[0]);
			return 1;
		}

		if (argv[optind + 2][strlen(argv[optind + 2]) - 1] == '-') {
			notifier_get_id_s(NULL, &id);
			getid = id - atoi(argv[optind + 2]);
		} else {
			getid = atoi(argv[optind + 2]);
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
