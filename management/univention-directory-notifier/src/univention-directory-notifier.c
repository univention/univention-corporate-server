/*
 * Univention Directory Notifier
 *
 * Copyright 2004-2019 Univention GmbH
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

#define _GNU_SOURCE

#include <errno.h>
#include <error.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

#include <unistd.h>
#include <sys/ipc.h>



#include <univention/debug.h>

#include "notify.h"
#include "network.h"
#include "cache.h"

Notify_t notify;
NotifyId_t notify_last_id;

long SCHEMA_ID;

long long notifier_cache_size=1000;
long long notifier_lock_count=100;
long long notifier_lock_time=100;

void usage(void)
{
	fprintf(stderr, "Usage: univention-directory-notifier [options]\n");
	fprintf(stderr, "Options:\n");
	fprintf(stderr, "   -F   run in foreground (intended for process supervision)\n");
	fprintf(stderr, "   -o          DEPRECATED\n");
	fprintf(stderr, "   -r          DEPRECATED\n");
	fprintf(stderr, "   -s          DEPRECATED\n");
	fprintf(stderr, "   -d   added debug output\n");
	fprintf(stderr, "   -S   DEPRECATED\n");
	fprintf(stderr, "   -v <version> Minimum supported protocol\n");
}

static int SCHEMA_CALLBACK = 0;
static int LISTENER_CALLBACK = 0;

void set_schema_callback ( int sig, siginfo_t *si, void *data)
{
	    SCHEMA_CALLBACK = 1;
}
void set_listener_callback ( int sig, siginfo_t *si, void *data)
{
	    LISTENER_CALLBACK = 1;
}

int get_schema_callback ()
{
	return SCHEMA_CALLBACK;
}
int get_listener_callback ()
{
	return LISTENER_CALLBACK;
}

void unset_schema_callback ()
{
	    SCHEMA_CALLBACK = 0;
}
void unset_listener_callback ()
{
	    LISTENER_CALLBACK = 0;
}

void create_callback_schema()
{
	int fd;
	struct sigaction act;

	act.sa_sigaction = set_schema_callback;
	sigemptyset(&act.sa_mask);
	act.sa_flags = SA_SIGINFO;
	sigaction(SIGUSR1, &act, NULL);

	fd = open("/var/lib/univention-ldap/schema/id/", O_RDONLY);
	fcntl(fd, F_SETSIG, SIGUSR1);
	fcntl(fd, F_NOTIFY, DN_MODIFY|DN_MULTISHOT);
}

void create_callback_listener()
{
	int fd;
	struct sigaction act;

	act.sa_sigaction = set_listener_callback;
	sigemptyset(&act.sa_mask);
	act.sa_flags = SA_SIGINFO;
	sigaction(SIGRTMIN, &act, NULL);

	fd = open("/var/lib/univention-ldap/listener/", O_RDONLY);
	fcntl(fd, F_SETSIG, SIGRTMIN);
	fcntl(fd, F_NOTIFY, DN_MODIFY|DN_MULTISHOT);
}

int creating_pidfile(char *file)
{
    FILE *fd;

    if( (fd = fopen(file, "w")) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Can't open pidfile \"%s\"",file);
        return -1;
    }

	fprintf(fd, "%d",getpid());
    fclose(fd);

    return 0;
}

int main(int argc, char* argv[])
{

	int foreground = 0;
	int debug = 0;


	SCHEMA_ID=0;

	for (;;) {
		int c;
		char *end;

		c = getopt(argc, argv, "Fosrd:S:C:L:T:v:");
		if (c < 0)
			break;

		switch (c) {
			case 'F':
				foreground = 1;
				break;
			case 'd':
				debug = atoi(optarg);
				break;
			case 'o':
			case 'r':
			case 's':
			case 'S':
				fprintf(stderr, "Ignoring deprecated option -%c\n", c);
				break;
			case 'C':
				notifier_cache_size=atoll(optarg);
				break;
			case 'L':
				notifier_lock_count=atoll(optarg);
				break;
			case 'T':
				notifier_lock_time=atoll(optarg);
				break;
			case 'v':
				network_procotol_version = strtoll(optarg, &end, 10);
				if (!*optarg || *end || network_procotol_version < PROTOCOL_1 || network_procotol_version >= PROTOCOL_LAST)
					error(EXIT_FAILURE, errno, "Invalid argument '-%c %s'", c, optarg);
				break;
			default:
				usage();
				exit(1);
		}
	}

	if ( foreground == 0 ) {
    	daemon(1,1);
	}

	univention_debug_init("/var/log/univention/notifier.log",1,1);
	univention_debug_set_level(UV_DEBUG_TRANSFILE, debug);

	if ( creating_pidfile("/var/run/udsnotifier.pid") != 0 )
	{
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Couldn't create pid file, exit");
		exit (1);
	}

	notify_init ( &notify );

	if ( notify_transaction_get_last_notify_id ( &notify, &notify_last_id )  != 0 ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "Error notify_transaction_get_last_notify_id\n");
	}


	/* DEBUG */
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Last transaction id = %ld\n",notify_last_id.id);

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Fill cache");
	notifier_cache_init(notify_last_id.id);
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "   done");

	network_client_init( 6669 );

		create_callback_listener ();
	create_callback_schema ();

		notify_listener_change_callback ( 0, NULL, NULL);
	notify_schema_change_callback ( 0, NULL, NULL);

	network_client_main_loop( );
	
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Normal exit");

	return 0;
}


