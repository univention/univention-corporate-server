#include <signal.h>
#include <sys/param.h>
#include <pwd.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define COMMAND "/usr/lib/nagios/plugins/check_univention_nscd"

static char *const suid_envp[] = {
	"PATH=/usr/sbin:/usr/bin:/sbin:/bin",
	NULL
};

int main( int argc, char ** argv, char ** envp )
{
	int i = 0;
	if (setgid(getegid())) {
		perror("setgid");
		return EXIT_FAILURE;
	}
	if (setuid(geteuid())) {
		perror("setuid");
		return EXIT_FAILURE;
	}
	for(i=0; i<argc; i++) {
	  if (( strcmp("-L", argv[i]) == 0 ) && (i+1 < argc)) {
		execle(COMMAND, COMMAND, "-L", argv[i+1], NULL, &suid_envp);
	  }
	}
	execle(COMMAND, COMMAND, NULL, &suid_envp);
	perror("execle");
	return EXIT_FAILURE;
}
