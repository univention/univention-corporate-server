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
#include <ctype.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>
#include <pwd.h>
#include <errno.h>

#include "pipe.h"
#include "protocol.h"
#include "command_socket.h"
#include "session.h"

int send_fd;
int recv_fd;
extern int sock_fd;

/* command line args */
int debug_level = 0;
char * prog_name = NULL;
char * server_host = "foo";
char * server_prog = "bar";
char * script_name = "baz";

static void usage(const char *exeName)
{
  fprintf(stderr, "\nusage: %s targethost [options]\n\n", exeName);
  fprintf(stderr, "options:\n");
  fprintf(stderr, "   -d<n>    set debug level to <n>\n");
  fprintf(stderr, "   -h       display this help message\n");
  fprintf(stderr, "\n");
}

static void parse_args( int argc, char *argv[] )
{
  int i;

  prog_name = strdup ( argv[0] );

  for (i = 1; i < argc-1; i++)
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
      //      else
      //	{
      //	  usage( prog_name );
      //	  exit(1);
      //	}
    }
}


int main ( int argc, char* argv[] )
{
  char path[UNIX_MAX_PATH];
  char *complete = malloc (MAX_CMD_LEN * sizeof (char ));

  parse_args( argc, argv );
  if (argc<2)
    usage(prog_name);

  struct passwd* pwd = getpwuid(getuid());
  snprintf (path, UNIX_MAX_PATH, "/tmp/.univention-session-%s/%s/socket", pwd->pw_name, argv[1]);

  int sock_fd = command_socket_connect (path);

  char* commandtosend = malloc(MAX_CMD_LEN * sizeof(char));

  int commandlength = 0;

  int i;
  for (i=2; i<argc; i++)
    {
      debug_printf("%d %s\n", i, argv[i]);
      strcat(commandtosend, argv[i]);
      strcat(commandtosend, " ");
    }









  int sent = send (sock_fd, commandtosend, strlen(commandtosend)+1, 0);

  //  debug_printf("arg :%s\n", commandtosend);
  //  debug_printf("argl: %d    %d\n", commandlength, strlen(commandtosend));

  if (sent == -1)
    fprintf(stderr, "Sending failed: %s (%d)\n", strerror(errno), errno);

  return 0;
}
