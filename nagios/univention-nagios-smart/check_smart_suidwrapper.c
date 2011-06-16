#include <signal.h>
#include <sys/param.h>
#include <pwd.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>


#define COMMAND "/usr/lib/nagios/plugins/check_smart.pl"

main( int argc, char ** argv, char ** envp )
{
    int status = 0;
    int i = 0;
    uid_t uid = getuid();
    char device[50] = "";
    char interface[50] = "";


    if( setgid(getegid()) ) perror( "setgid" );
    if( setuid(geteuid()) ) perror( "setuid" );
	for(i=0; i<argc; i++) {
	  if (( strcmp("-d", argv[i]) == 0 ) && (i+1 < argc)) {
		strcat(device, argv[i+1]);
	  }
	  if (( strcmp("-i", argv[i]) == 0 ) && (i+1 < argc)) {
		strcat(interface, argv[i+1]);
	  }
	}
	execle(COMMAND, COMMAND, "-d", device, "-i", interface, (char *)0, (char *)0);
	setuid(uid);
	exit(1);
}
