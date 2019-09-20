/*
 * Univention uvmmd nagios plugin
 *
 * Copyright 2011-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */

#include <stdlib.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <signal.h>
#include <fcntl.h>
#include <limits.h>
#include <sys/wait.h>

#define NAGIOS_OK 0
#define NAGIOS_OK_MSG "OK:"

#define NAGIOS_WARNING 1
#define NAGIOS_WARNING_MSG "WARNING:"

#define NAGIOS_CRITICAL 2
#define NAGIOS_CRITICAL_MSG "CRITICAL:"

#define NAGIOS_UNKNOWN 3
#define NAGIOS_UNKNOWN_MSG "UNKNOWN:"

static char *uvmm_argv[] = {
	"/usr/sbin/uvmm",
	"nodes",
	"default",
	NULL,
};
static char *uvmm_envp[] = {
	NULL
};

static char *command;
static pid_t pid;
static unsigned int timeout = 10;

/* kill the child and exit with error */
static void my_alarm_handler(int signo) {
	kill(pid, SIGKILL);
	printf(NAGIOS_CRITICAL_MSG " uvmmd timed out after %d seconds!\n", timeout);
	exit(NAGIOS_CRITICAL);
}

static void usage(int status) {
	FILE *stream = status ? stderr : stdout;
	fprintf(stream, "usage: %s [OPTIONS]\n", command);
	fprintf(stream, "\t-t SECONDS - uvmmd timeout\n");
	fprintf(stream, "\t-h|--help  - help message\n");
	exit(status);
}

int main(int argc, char *argv[], char *envp[]) {
	int i = 0;
	int status;
	uid_t uid = getuid();

	/* get options */
	command = argv[0];
	for (i = 1; i < argc; i++) {
		if (strcmp("-t", argv[i]) == 0) {
			if (i + 1 < argc) {
				char *endptr;
				errno = 0;
				timeout = strtoul(argv[++i], &endptr, 10);
				if ((errno == ERANGE) && (timeout == ULONG_MAX)) {
					perror("ERROR: strtoul");
					usage(EXIT_FAILURE);
				} else if ((errno != 0) && (timeout == 0)) {
					fprintf(stderr, "ERROR: invalid timeout: %s\n", argv[i]);
					usage(EXIT_FAILURE);
				} else if (*endptr != '\0') {
					fprintf(stderr, "ERROR: invalid timeout: %s\n", argv[i]);
					usage(EXIT_FAILURE);
				}
			} else {
				fprintf(stderr, "ERROR: missing timeout.\n");
				usage(EXIT_FAILURE);
			}
		} else if ((strcmp("-h", argv[i]) == 0) || (strcmp("--help", argv[i]) == 0 )) {
			usage(EXIT_SUCCESS);
		} else {
			fprintf(stderr, "ERROR: unknown option: %s", argv[i]);
			usage(EXIT_FAILURE);
		}
	}

	/* signal handler */
	signal(SIGALRM, my_alarm_handler);

	if (setgid(getegid()))
		perror("setgid");
	if (setuid(geteuid()))
		perror("setuid");

	pid = fork();

	if (pid == 0) {
		/* child, run command */

		/* redirect output, nagios wants one status line */
		int devnull = open("/dev/null", O_RDWR);
		if (devnull < 0) {
			exit(EXIT_FAILURE);
		}
		dup2(devnull, STDOUT_FILENO);
		dup2(devnull, STDERR_FILENO);
		close(devnull);

		execve(uvmm_argv[0], uvmm_argv, uvmm_envp);
		exit(NAGIOS_CRITICAL);
	} else if (pid < 0) {
		setuid(uid);
		printf(NAGIOS_CRITICAL_MSG " fork failed\n");
		exit(NAGIOS_CRITICAL);
	} else {
		/* handle timeouts gracefully... */
		alarm(timeout);

		waitpid(pid, &status, 0);
		setuid(uid);

		/* Stop the timer */
		alarm(0);

		if (WEXITSTATUS(status) != 0) {
			printf(NAGIOS_CRITICAL_MSG);
			for (i = 0; uvmm_argv[i]; i++)
				printf(" %s", uvmm_argv[i]);
			printf(" failed\n");
			exit(NAGIOS_CRITICAL);
		} else {
			printf(NAGIOS_OK_MSG " uvmmd is running\n");
			exit(NAGIOS_OK);
		}
	}

	printf(NAGIOS_UNKNOWN_MSG " uvmmd unknown\n");
	exit(NAGIOS_UNKNOWN);
}
