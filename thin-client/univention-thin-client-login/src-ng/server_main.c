/*
 * Univention Client Login
 *  this file is part of the Univention thin client tools
 *
 * Copyright 2004-2010 Univention GmbH
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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>

#include "debug.h"
#include "signals.h"
#include "protocol.h"
#include "script.h"
#include "process.h"
#include "security.h"
#include "alive.h"
#include "connection.h"
#include "command_socket.h"
#include "select_loop.h"
#include "session.h"
#include "command.h"
#include "cmd_handler.h"

/* command line args */
int debug_level = 0;
char * prog_name = NULL;
char * server_host = "foo";
char * server_prog = "bar";
char * script_name = "baz";

static void usage(const char *exeName)
{
  fprintf(stderr, "\nusage: %s [options]\n\n", exeName);
  fprintf(stderr, "options:\n");
  fprintf(stderr, "   -d<n>    set debug level to <n>\n");
  fprintf(stderr, "   -h       display this help message\n");
  fprintf(stderr, "\n");
}

static void parse_args( int argc, char *argv[] )
{
  int i;

  prog_name = strdup ( argv[0] );

  for (i = 1; i < argc; i++)
    {
      if (argv[i][0] == '-')
        {
	  switch(argv[i][1])
            {
            case 'd':
	      if (isdigit(argv[i][2])) debug_level = atoi( argv[i] + 2 );
	      else debug_level++;
	      break;
            case 'h':
	      usage( prog_name );
	      exit(0);
	      break;
            default:
	      fprintf( stderr, "Unknown option '%s'\n", argv[i] );
	      usage( prog_name );
	      exit(1);
            }
        }
      else
	{
	  usage( prog_name );
	  exit(1);
	}
    }
}


int main( int argc, char *argv[] )
{
    /* get command line args */
    parse_args( argc, argv );

    /* drop root rights */
    init_security ();

    /* become a session leader */
    setsid();

    /* initialize the server */
    init_server_pipes();

    /* setup signals */
    signal_init();

    /* kill all childs when exiting */
    atexit(call_cleanup_script);
    atexit(process_killall);
    atexit(command_socket_server_remove);

    server_keep_alive_init();

    /* create a temporary session working directory */
    setup_session_directory();

    command_socket_server_init(server_host);
    command_socket_client_init(server_host);
    select_loop();

    return 0;
}
