/*
 * Univention uvmmd nagios plugin
 *
 * Copyright 2011 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */

#include <unistd.h>
#include <string.h>
#include <signal.h>
#include <stdlib.h>
#include <stdio.h>
#include <sys/wait.h>
#include <fcntl.h>

#define COMMAND "/usr/sbin/uvmm"
#define COMMAND_ARGS1 "nodes"
#define COMMAND_ARGS2 "default"

#define NAGIOS_OK 0
#define NAGIOS_OK_MSG "OK:"

#define NAGIOS_WARNING 1
#define NAGIOS_WARNING_MSG "WARNING:"

#define NAGIOS_CRITICAL 2
#define NAGIOS_CRITICAL_MSG "CRITICAL:"

#define NAGIOS_UNKNOWN 3
#define NAGIOS_UNKNOWN_MSG "UNKNOWN:"

#define MAX_STR_LEN 254

pid_t pid;
int timeout = 10;

/* kill the child and exit with error */
void my_alarm_handler (int signo) {

	kill(pid, 9);
	printf("%s uvmmd timed out after %d seconds!\n", NAGIOS_CRITICAL_MSG, timeout);
	exit(NAGIOS_CRITICAL);
}

void usage() {

	printf("usage: [OPTIONS]\n");
	printf("\t-t SECONDS - uvmmd timout\n");
	printf("\t-h|--help  - help message\n");
	
	exit(1);
}

main (int argc, char ** argv, char ** envp) {

	int i = 0;
	int status;
	uid_t uid = getuid();

	/* get options */
	for (i = 0; i < argc; i++) {

		if ((strcmp("-t", argv[i]) == 0 ) && (i+1 < argc)) {
			timeout = atoi(argv[i+1]);
		}

		if ((strcmp("-h", argv[i]) == 0) || (strcmp("--help", argv[i]) == 0 )) {
			usage();
		}
	}

	/* signal handler */
	signal (SIGALRM, my_alarm_handler);
			
	if( setgid(getegid()) ) perror( "setgid" );
	if( setuid(geteuid()) ) perror( "setuid" );

	pid = fork();

	if (pid == 0) {
		/* child, run command */

		/* redirect output, nagios wants one status line */
		int devnull = open("/dev/null", O_RDWR);
		if (devnull < 0) {
			exit(1);
		}
		dup2(devnull, STDOUT_FILENO);
		dup2(devnull, STDERR_FILENO);
		close(devnull);

		execle(COMMAND, COMMAND, COMMAND_ARGS1, COMMAND_ARGS2, (char *)0, (char *)0);
	} else if (pid < 0) {
		setuid(uid);
		printf("%s fork failed\n", NAGIOS_CRITICAL_MSG);
		exit(NAGIOS_CRITICAL);
	} 
	else {
		/* handle timeouts gracefully... */
		alarm (timeout);

		waitpid(pid, &status, 0);
		setuid(uid);

		/* Stop the timer */
		alarm (0);

		if (WEXITSTATUS(status) != 0) {
			printf("%s %s %s %s failed\n", NAGIOS_CRITICAL_MSG, COMMAND, COMMAND_ARGS1, COMMAND_ARGS2);
			exit(NAGIOS_CRITICAL);
		}
		else {
			printf("%s uvmmd is running\n", NAGIOS_OK_MSG);
			exit(NAGIOS_OK);
		}
	}
	
	printf("%s uvmmd unknown\n", NAGIOS_UNKNOWN_MSG);
	exit(NAGIOS_UNKNOWN);
}
