#include <signal.h>
#include <stdio.h>
#include <sys/param.h>
#include <pwd.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>

#define COMMAND "/usr/share/pyshared/univention/lib/getMailFromMailOrUid.py"


int main ( int argc, char ** argv, char ** envp )
{
    if (argc >= 2) {
        char *cmd[1024] = {COMMAND,argv[1],NULL}; 
        uid_t uid = getuid();
        if( setuid(geteuid()) ) perror( "setuid" );
        execvp(COMMAND,cmd);
        setuid(uid);
        exit(1);
    }
}
