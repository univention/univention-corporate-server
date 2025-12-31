//
// Univention Nagios Plugin
//  check_univention_s4_connector_suidwrapper:
//  wrapper to call script for checking s4 connector status
//
// SPDX-FileCopyrightText: 2015-2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only
//

#include <unistd.h>
#include <errno.h>
#include <stdlib.h>

#define COMMAND "/usr/lib/nagios/plugins/check_univention_s4_connector"

main( int argc, char ** argv, char ** envp )
{
	uid_t uid = getuid();
	if (setgid(getegid()))
		perror("setgid");
	if (setuid(geteuid()))
		perror("setuid");
	execle(COMMAND, COMMAND, (char *)0, (char *)0);
	setuid(uid);
	exit(0);
}
