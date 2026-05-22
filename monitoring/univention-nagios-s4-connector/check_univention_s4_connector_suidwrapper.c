//
// Univention Nagios Plugin
//  check_univention_s4_connector_suidwrapper:
//  wrapper to call script for checking s4 connector status
//
// SPDX-FileCopyrightText: 2015-2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only
//

#include <stdio.h>
#include <unistd.h>
#include <sys/types.h>

#define COMMAND "/usr/lib/nagios/plugins/check_univention_s4_connector"

int main(int argc, char **argv, char **envp) {
	uid_t uid = getuid();

	if (setgid(getegid())) {
		perror("setgid");
		return 1;
	}

	if (setuid(geteuid())) {
		perror("setuid");
		return 1;
	}

	execle(COMMAND, COMMAND, (char *)0, (char *)0);
	if (setuid(uid)) {
		perror("setuid afterwards");
		return 1;
	}
	return 0;
}
