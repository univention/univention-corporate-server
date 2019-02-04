#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

static const char COMMAND[] = "/usr/lib/nagios/plugins/check_univention_ldap";

int main(int argc, char **argv, char **envp)
{
	if (setgid(getegid())) {
		perror("setgid");
		return EXIT_FAILURE;
	}
	if (setuid(geteuid())) {
		perror("setuid");
		return EXIT_FAILURE;
	}
	execle(COMMAND, COMMAND, NULL, NULL);
	perror("execle");
	return EXIT_FAILURE;
}
