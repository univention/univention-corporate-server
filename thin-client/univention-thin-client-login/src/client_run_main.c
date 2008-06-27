/*
 * Univention Client Login
 *	this file is part of the Univention thin client tools
 *
 * Copyright (C) 2001, 2002, 2003, 2004, 2005, 2006 Univention GmbH
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
#include <unistd.h>

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
char * socket_name = "/tmp/univention-client.sock";
char * message = NULL;

static void usage(const char *exeName)
{
  fprintf(stderr, "\nusage: %s [options]\n\n", exeName);
  fprintf(stderr, "options:\n");
  fprintf(stderr, "   -d<n>    set debug level to <n>\n");
  fprintf(stderr, "   -h       display this help message\n");
  fprintf(stderr, "   -m       send message to univention-client\n");
  fprintf(stderr, "   -f file  socket name\n");
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
            case 'm':
	      if ( argv[i+1] == NULL ) {
	        usage ( prog_name );
	        exit(1);
	      }
	      message = strdup ( argv[i+1] );
	      i++;
	      break;
            case 'f':
	      if ( argv[i+1] == NULL ) {
	        usage ( prog_name );
	        exit(1);
	      }
	      socket_name = strdup ( argv[i+1] );
	      i++;
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

  if (!message)
    {
      usage( prog_name );
      exit(1);
    }
}


int main ( int argc, char* argv[] )
{
  /* get command line args */
  parse_args( argc, argv );
  command_socket_client_init ( socket_name );

  /*send_command_fd ( argv[argc-1], sock_fd, sock_fd );*/
  /*send ( sock_fd, argv[argc-1], strlen(argv[argc-1])+1, 0 ); */
  if (debug_level)
    fprintf( stderr, "sending message: %s\n", message );
  send(sock_fd, message, strlen(message)+1, 0);

  close(sock_fd);

  return 0;
}
