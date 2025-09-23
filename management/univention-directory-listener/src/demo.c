/*
 * Univention Directory Listener
 *  demo program for the notifier client API.
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include <univention/config.h>
#include <univention/debug.h>

#include "network.h"
#include "common.h"
#include "utils.h"

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

	if (NOTIFIER_CLIENT_NEW_RETRY(notifier_client_new(NULL, argv[optind], 1)) != 0) {
		fprintf(stderr, "Could not connect to notifier\n");
		return 1;
	}

	if (strcmp(argv[optind + 1], "get_id") == 0) {
		NOTIFIER_RETRY(notifier_get_id_s(NULL, &id));
		printf("%ld\n", id);
	} else if (strcmp(argv[optind + 1], "get_schema_id") == 0) {
		NOTIFIER_RETRY(notifier_get_schema_id_s(NULL, &id));
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
		NOTIFIER_RETRY(notifier_get_dn_result(NULL, msgid, &entry));

		printf("%ld %s\n", entry.id, entry.dn);
	} else {
		usage(argv[0]);
		return 1;
	}

	return 0;
}
