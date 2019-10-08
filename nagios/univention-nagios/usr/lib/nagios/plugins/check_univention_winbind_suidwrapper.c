#include <signal.h>
#include <stdio.h>
#include <sys/param.h>
#include <pwd.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>

#define COMMAND "/usr/lib/nagios/plugins/check_univention_winbind"


int main ( int argc, char ** argv, char ** envp )
{
	uid_t uid = getuid();
    if( setuid(geteuid()) ) perror( "setuid" );
	execle(COMMAND, COMMAND, (char *)0, (char *)0);
	setuid(uid);
	exit(1);
}
