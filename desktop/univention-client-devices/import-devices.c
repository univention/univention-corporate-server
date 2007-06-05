/*
 * Univention Client Devices
 *	imports local devices of a thin client
 *
 * Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006 Univention GmbH
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
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>
#include <sys/types.h>
#include <pwd.h>

int main(int argc, char* argv[])
{
	struct passwd* pwd;
	char *args[4];
	char *env[3];
	char *p;

	pwd = getpwuid(getuid());
	if (pwd == NULL) {
		fprintf(stderr, "failed to determine username\n");
		exit(1);
	}

	if (argc != 3) {
		fprintf(stderr, "invalid number of arguments\n");
		exit(1);
	}

	if (strcmp(argv[1], "start") != 0 && strcmp(argv[1], "stop") != 0) {
		fprintf(stderr, "invalid action\n");
		exit(1);
	}

	for (p = argv[2]; *p != '\0'; ++p) {
		if (!isalnum(*p)) {
			fprintf(stderr, "hostname seems bad\n");
			exit(1);
		}
	}

	args[0] = "/usr/sbin/import-devices.sh";
	args[1] = argv[1];
	args[2] = pwd->pw_name;
	args[3] = argv[2];
	args[4] = NULL;

	env[0] = "PATH=/sbin:/usr/sbin:/bin:/usr/bin";
	env[1] = malloc(sizeof(char) * 256);
	if (env[1] == NULL) {
		perror("malloc");
		exit(1);
	}
	snprintf(env[1], 256, "PASSWD=%s", getenv("PASSWD"));
	env[2] = NULL;

	setuid(0);
	execve(args[0], args, env);

	perror("execv"); /* we shouldn't get here */
	return 1;
}
