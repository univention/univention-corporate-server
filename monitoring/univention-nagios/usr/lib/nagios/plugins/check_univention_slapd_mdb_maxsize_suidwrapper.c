//
// Univention Nagios Plugin
//  wrapper to call script for checking slapd_mdb_maxsize
//
// SPDX-FileCopyrightText: 2015-2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only

#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <getopt.h>

#define COMMAND "/usr/lib/nagios/plugins/check_univention_slapd_mdb_maxsize"

static char *const suid_envp[] = {"PATH=/usr/sbin:/usr/bin:/sbin:/bin", NULL};

int main(int argc, char **argv, char **envp) {
	int i = 0;
	int listener = 0;
	char warning[] = "75";
	char critical[] = "90";
	while ((i = getopt(argc, argv, "lc:w:")) != -1) {
		switch (i) {
		case 'l':
			listener = 1;
			break;
		case 'w':
			strncpy(warning, optarg, 2);
			break;
		case 'c':
			strncpy(critical, optarg, 2);
			break;
		default:
			exit(EXIT_FAILURE);
		}
	}
	if (setgid(getegid())) {
		perror("setgid");
		return EXIT_FAILURE;
	}
	if (setuid(geteuid())) {
		perror("setuid");
		return EXIT_FAILURE;
	}

	if (listener) {
		execle(COMMAND, COMMAND, "-l", "-w", warning, "-c", critical, NULL, &suid_envp);
	} else {
		execle(COMMAND, COMMAND, "-w", warning, "-c", critical, NULL, &suid_envp);
	}
	perror("execle");
	return EXIT_FAILURE;
}
