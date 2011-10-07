#include <signal.h>
#include <stdio.h>
#include <sys/param.h>
#include <pwd.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>

#define COMMAND "/usr/share/pyshared/univention/lib/getMailFromMailOrUid.py"


int main ( int argc, char ** argv, char ** envp ) {

	if (argc >= 2) {
		int status = 0;
		int i = 0;
		uid_t uid = getuid();

		if( setgid(getegid()) ) perror( "setgid" );
		if( setuid(geteuid()) ) perror( "setuid" );
		execle(COMMAND, COMMAND, argv[1], (char *)0, (char *)0);
		setuid(uid);
		exit(1);
	}

	exit(0);

}
