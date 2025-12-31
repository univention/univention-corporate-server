// Univention Nagios Plugin
//
// SPDX-FileCopyrightText: 2016-2026 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only
//

#include <unistd.h>
#include <errno.h>
#include <stdlib.h>

#define COMMAND "/usr/lib/nagios/plugins/check_univention_samba_drs_failures"

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
