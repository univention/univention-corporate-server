/*
 * Univention Client Login
 *  this file is part of the Univention thin client tools
 *
 * Copyright (C) 2004, 2005, 2006 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Binary versions of this file provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <unistd.h>

#include "debug.h"
#include "signals.h"
#include "connection.h"
#include "protocol.h"
#include "script.h"
#include "process.h"
#include "security.h"
#include "command.h"
#include "alive.h"
#include "select_loop.h"
#include "command_socket.h"

/* command line args */
int debug_level = 0;
char * session_script = NULL;
char * prog_name = NULL;
char * server_host = NULL;
char * server_prog = NULL;
char * script_name = NULL;

static void usage(const char *exeName)
{
  fprintf(stderr, "\nusage: %s [options]\n\n", exeName);
  fprintf(stderr, "options:\n");
  fprintf(stderr, "   -s host  set the name of the server\n");
  fprintf(stderr, "   -r prog  set the name of the remote server program\n");
  fprintf(stderr, "   -p prog  set the name of the local session setup script\n");
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
	    case 's':
	      if ( argv[i+1] == NULL ) {
		usage ( prog_name );
		exit(1);
	      }
	      server_host = strdup ( argv[i+1] );
	      i++;
	      break;
	    case 'p':
	      if ( argv[i+1] == NULL ) {
		usage ( prog_name );
		exit(1);
	      }
	      script_name = strdup ( argv[i+1] );
	      i++;
	      break;
	    case 'r':
	      if ( argv[i+1] == NULL ) {
		usage ( prog_name );
		exit(1);
	      }
	      server_prog = strdup ( argv[i+1] );
	      i++;
	      break;
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
    parse_args( argc, argv );
    init_security ();
    signal_init();
    // atexit(kill_childs); // FIXME, zu schreiben
    connect_to_server();
    start_script( "start" );
    //    atexit(run_stop_script);
    client_keep_alive_init();

    command_socket_client_init(server_host);
    command_socket_server_init(server_host);

    select_loop();

    return 0;

}
