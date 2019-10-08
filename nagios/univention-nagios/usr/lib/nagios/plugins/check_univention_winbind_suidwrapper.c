#include <signal.h>
#include <stdio.h>
#include <sys/param.h>
#include <pwd.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>

#define COMMAND "/usr/lib/nagios/plugins/check_univention_winbind"

static char *const suid_envp[] = {
	"PATH=/usr/sbin:/usr/bin:/sbin:/bin",
	NULL
};

int main ( int argc, char ** argv, char ** envp )
{
	if (setgid(getegid())) {
		perror("setgid");
		return EXIT_FAILURE;
	}
	if (setuid(geteuid())) {
		perror("setuid");
		return EXIT_FAILURE;
	}
	execle(COMMAND, COMMAND, NULL, &suid_envp);
	perror("execle");
	return EXIT_FAILURE;
}
