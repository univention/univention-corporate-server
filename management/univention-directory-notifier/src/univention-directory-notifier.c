/*
 * Univention Directory Notifier
 *
 * Copyright 2004-2019 Univention GmbH
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
#define _GNU_SOURCE

#include <errno.h>
#include <error.h>
#include <fcntl.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <univention/debug.h>

#include "cache.h"
#include "network.h"
#include "notify.h"

Notify_t notify;
NotifyId_t notify_last_id;

NotifyId SCHEMA_ID;

long long notifier_lock_count = 100;
long long notifier_lock_time = 100;

/*
 * Print usage information.
 */
static void usage(void) {
	fprintf(stderr, "Usage: univention-directory-notifier [options]\n");
	fprintf(stderr, "Options:\n");
	fprintf(stderr, "   -F   run in foreground (intended for process supervision)\n");
	fprintf(stderr, "   -D   run in foreground debug mode\n");
	fprintf(stderr, "   -o          DEPRECATED\n");
	fprintf(stderr, "   -r          DEPRECATED\n");
	fprintf(stderr, "   -s          DEPRECATED\n");
	fprintf(stderr, "   -d <level>  added debug output\n");
	fprintf(stderr, "   -S <delay>  DEPRECATED\n");
	fprintf(stderr, "   -C <size>   Number of entries to cache\n");
	fprintf(stderr, "   -L <count>  Number of lock attempts\n");
	fprintf(stderr, "   -T <time>   Delay between lock attempts\n");
	fprintf(stderr, "   -p <port>   TCP port number (6669)\n");
}

static int SCHEMA_CALLBACK = 0;
static int LISTENER_CALLBACK = 0;

/*
 * Callback function to signal pending LDAP schema change.
 * :param sig: signal number.
 * :param si: signal information.
 * :param data: Opaque data.
 */
static void set_schema_callback(int sig, siginfo_t *si, void *data) {
	SCHEMA_CALLBACK = 1;
}

/*
 * Callback function to signal pending transaction from slapd transaction log overlay.
 * :param sig: signal number.
 * :param si: signal information.
 * :param data: Opaque data.
 */
static void set_listener_callback(int sig, siginfo_t *si, void *data) {
	LISTENER_CALLBACK = 1;
}

/*
 * Setup signal handler for SIGUSR1 to handle LDAP schema changes.
 */
static void create_callback_schema() {
	int fd;
	struct sigaction act;

	act.sa_sigaction = set_schema_callback;
	sigemptyset(&act.sa_mask);
	act.sa_flags = SA_SIGINFO;
	sigaction(SIGUSR1, &act, NULL);

	fd = open("/var/lib/univention-ldap/schema/id/", O_RDONLY);
	fcntl(fd, F_SETSIG, SIGUSR1);
	fcntl(fd, F_NOTIFY, DN_MODIFY | DN_MULTISHOT);
}

/*
 * Setup signal handler for SIGRTMIN to handle transactions from slapd transaction log overlay.
 */
static void create_callback_listener() {
	int fd;
	struct sigaction act;

	act.sa_sigaction = set_listener_callback;
	sigemptyset(&act.sa_mask);
	act.sa_flags = SA_SIGINFO;
	sigaction(SIGRTMIN, &act, NULL);

	fd = open("/var/lib/univention-ldap/listener/", O_RDONLY);
	fcntl(fd, F_SETSIG, SIGRTMIN);
	fcntl(fd, F_NOTIFY, DN_MODIFY | DN_MULTISHOT);
}

/*
 * Check status of callbacks and execute functions as needed.
 */
static void check_callbacks() {
	if (SCHEMA_CALLBACK) {
		notify_schema_change_callback(0, NULL, NULL);
		SCHEMA_CALLBACK = 0;
	}
	if (LISTENER_CALLBACK) {
		notify_listener_change_callback(0, NULL, NULL);
		LISTENER_CALLBACK = 0;
	}
}

/*
 * Create file with process identifier.
 * :param file: The file name of the file.
 * :returns: -1 on error, 0 on success.
 */
static int creating_pidfile(char *file) {
	FILE *fd;

	if ((fd = fopen(file, "w")) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Can't open pidfile \"%s\"", file);
		return -1;
	}

	fprintf(fd, "%d", getpid());
	fclose(fd);

	return 0;
}

/*
 * Univention Directory Notifier daemon.
 * :param argc: Number of command line arguments.
 * :param argv: Array of command line arguments.
 */
int main(int argc, char *argv[]) {
	int foreground = 0;
	int debug = 0;
	int port = 6669;
	const char *logfile = "/var/log/univention/notifier.log";

	SCHEMA_ID = 0;

	for (;;) {
		int c;
		char *end;

		c = getopt(argc, argv, "Fosrd:S:C:L:T:p:D");
		if (c < 0)
			break;

		switch (c) {
		case 'D':
			logfile = "stderr";
			/* fall through */
		case 'F':
			foreground = 1;
			break;
		case 'd':
			debug = strtol(optarg, &end, 10);
			if (!*optarg || *end || debug < 0)
				error(EXIT_FAILURE, errno, "Invalid argument '-%c %s'", c, optarg);
			break;
		case 'o':
		case 'r':
		case 's':
		case 'S':
			fprintf(stderr, "Ignoring deprecated option -%c\n", c);
			break;
		case 'C':
			notifier_cache_size = strtoll(optarg, &end, 10);
			if (!*optarg || *end || notifier_cache_size < 1)
				error(EXIT_FAILURE, errno, "Invalid argument '-%c %s'", c, optarg);
			break;
		case 'L':
			notifier_lock_count = strtoll(optarg, &end, 10);
			if (!*optarg || *end || notifier_lock_count < 1)
				error(EXIT_FAILURE, errno, "Invalid argument '-%c %s'", c, optarg);
			break;
		case 'T':
			notifier_lock_time = strtoll(optarg, &end, 10);
			if (!*optarg || *end || notifier_lock_time < 1)
				error(EXIT_FAILURE, errno, "Invalid argument '-%c %s'", c, optarg);
			break;
		case 'p':
			port = strtol(optarg, &end, 10);
			if (!*optarg || *end || port < 1 || port > 65535)
				error(EXIT_FAILURE, errno, "Invalid argument '-%c %s'", c, optarg);
			break;
		default:
			usage();
			exit(1);
		}
	}

	if (foreground == 0) {
		daemon(1, 1);
	}

	univention_debug_init(logfile, UV_DEBUG_FLUSH, UV_DEBUG_FUNCTION);
	univention_debug_set_level(UV_DEBUG_TRANSFILE, debug);

	if (creating_pidfile("/var/run/udsnotifier.pid") != 0) {
		exit(1);
	}

	notify_init(&notify);

	if (!notify_transaction_get_last_notify_id(&notify, &notify_last_id))
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Last transaction id = %ld", notify_last_id.id);

	notifier_cache_init(notify_last_id.id);

	network_client_init(port);

	create_callback_listener();
	create_callback_schema();

	notify_listener_change_callback(0, NULL, NULL);
	notify_schema_change_callback(0, NULL, NULL);

	network_client_main_loop(check_callbacks);

	return 0;
}
