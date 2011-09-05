#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

#define COMMAND "/usr/lib/nagios/plugins/check_univention_ldap"

main(int argc, char ** argv, char ** envp)
{
	uid_t uid = getuid();
	char* args[2];
	if (setgid(getegid())) {
		perror("setgid");
	}
	if (setuid(geteuid())) {
		perror("setuid");
	}
	args[0] = COMMAND;
	args[1] = NULL;
	execv(COMMAND, args);
	setuid(uid);
	exit(1);
}
