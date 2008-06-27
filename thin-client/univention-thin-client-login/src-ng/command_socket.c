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
#include <unistd.h>
#include <string.h>
#include <limits.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>
#include <errno.h>

#include "debug.h"
#include "protocol.h"
#include "select_loop.h"
#include "command.h"
#include "session.h"
#include "cmd_handler.h"

#define UNIX_MAX_PATH 108 /* man 7 unix (where is this defined?) */

int socket_fd = 0;
int new_fd = 0;
struct sockaddr_un sock_name;

// handler function that reads a script command from the given
// filedescriptor and generates a PDU that is send on the
// currently active connection
int command_socket_client_handler ( int fd )
{
  //  int cmd;
  char *argv[MAX_CMD_ARGS];
  char **p=argv;

  char buf[MAX_CMD_LEN];
  char * buffer = buf;
  int r;

  char *complete = malloc (MAX_CMD_LEN * sizeof (char ));

  memset ( &buf, 0, MAX_CMD_LEN );
  //  memset ( &complete, 0, MAX_CMD_LEN );

  if ( debug_level )
    debug_printf ( "command_socket_client_handler activity on cmd socket %i\n", fd );

  r = recv ( fd, buf, MAX_CMD_LEN, 0 );

  int argcount = get_command_args ( buffer, p, MAX_CMD_ARGS );

  //  if ( debug_level )
  debug_printf("received command from command socket: %s (%i bytes buffer size, %i elements) \n", buf, r, argcount);

  if ( r == 0 ) {
    if ( debug_level )
      debug_printf ( "no data on socket (%d), closing...", fd );
    close ( fd );
    remove_read_fd ( fd );
    return -1;
  }

  int argslength = 0;

  /*
  if ( argv )
    {
      int i;
      debug_printf ( "args: ");
      //      if (argcount > 0)
	{
	  for (i = 2; argv[i]; i++)
	    {
	      debug_printf("CMD-SOCK:%i  %s\n", i, argv[i]);
	      strcat(complete, argv[i]);
	      strcat(complete, " ");
	    }
	}
    }
  */

  if ( debug_level )
    debug_printf ( "command from command socket: %s (%d args) \n", complete, argcount );

  argslength=strlen(complete);

  struct message sendpacket;
  sendpacket.args = argv;
  sendpacket.args_length = argslength;   //sizeof(argv);
  sendpacket.data = NULL;
  sendpacket.data_length = 0;

  if      (strcmp(argv[0], "alive") == 0)
    sendpacket.command = COMMAND_ALIVE;
  else if (strcmp(argv[0], "setenv") == 0)
    sendpacket.command = COMMAND_SETTING_SETENV;
  else if (strcmp(argv[0], "run") == 0)
    sendpacket.command = COMMAND_EXEC;
  else if (strcmp(argv[0], "start") == 0)
    sendpacket.command = COMMAND_START;
  else if (strcmp(argv[0], "exit") == 0)
    sendpacket.command = COMMAND_END_EXIT;
  else if (strcmp(argv[0], "error") == 0)
    sendpacket.command = COMMAND_ERROR;
  else if (strcmp(argv[0], "cleanup") == 0)
    sendpacket.command = COMMAND_END_CLEANUP;
  else if (strcmp(argv[0], "stdout") == 0)
    sendpacket.command = COMMAND_RED_STDOUT;
  else if (strcmp(argv[0], "stderr") == 0)
    sendpacket.command = COMMAND_RED_STDERR;
  else if (strcmp(argv[0], "exit_on_last_child") == 0)
    sendpacket.command = COMMAND_END_WAITCHILD;
  else if (strcmp(argv[0], "mount") == 0)
    sendpacket.command = COMMAND_MOUNT;
  else if (strcmp(argv[0], "unsetenv") == 0)
    sendpacket.command = COMMAND_SETTING_UNSETENV;

  //  get_command_args ( buffer, p, MAX_CMD_ARGS );

  /*  if (debug_level && argv )
    {
      int i;
      debug_printf("args");
      for (i = 0; argv[i]; i++)
	debug_printf ( "%s ", argv[i]);
      debug_printf ( "\n" );
    }
  */

  protocol_send_message(&sendpacket);

  return 0;
}

// This handler function accepts a new incoming connection inside the select()-Loop
int command_socket_handler ( int fd )
{
  int len = sizeof ( sock_name );
  new_fd = accept ( socket_fd, (struct sockaddr*) &sock_name, &len );

  if (new_fd != -1) {
    add_read_fd ( new_fd, command_socket_client_handler );
    if ( debug_level )
      debug_printf( "accepted new connection (fd=%d) on socket\n", new_fd );
  }
  return 0;
}

// create a new command socket, returns the created filedescriptor
void command_socket_init ( const char* path )
{
  memset ( &sock_name, 0, sizeof ( struct sockaddr_un ) );
  sock_name.sun_family = AF_UNIX;
  strncpy ( sock_name.sun_path, path, UNIX_MAX_PATH );
  socket_fd = socket ( PF_UNIX, SOCK_STREAM, 0 );

  if (socket_fd != -1)
    debug_printf ( "Command socket initialized on FD %d\n", socket_fd );
  else
    {
      debug_printf ( "Command socket initialization failed\n" );
      debug_printf ( "%s\n", strerror(errno) );
    }

}

// This function creates a new command socket for communication and listens for connection requests
// on the server socket.
void command_socket_server_init ( const char* server_host )
{
  // Old version:
  //  snprintf ( path, UNIX_MAX_PATH, "%s/ucs-sock-server-%s-%d", session_directory,
  //  	     server_hostname, getpid() );

  struct passwd* pwd = getpwuid(getuid());

  //  char server_hostname[128];
  char path[UNIX_MAX_PATH];
  char sub1[UNIX_MAX_PATH];
  char sub2[UNIX_MAX_PATH];

  if ( session_directory == NULL )
    fatal_perror ( "session_directory not defined\n" );
  //  char server_hostname[128];
  //  if ( gethostname ( server_hostname, 128 ) == -1 )
  //    fatal_perror ( "could not determine host name\n" );

  snprintf (sub1, UNIX_MAX_PATH, "/tmp/.univention-session-%s/", pwd->pw_name);
  mkdir(sub1, S_IRWXU);

  snprintf (sub2, UNIX_MAX_PATH, "/tmp/.univention-session-%s/%s/", pwd->pw_name, server_host);
  mkdir(sub2, S_IRWXU);

  snprintf ( path, UNIX_MAX_PATH, "/tmp/.univention-session-%s/%s/socket", pwd->pw_name,
  	     server_host);

  if ( debug_level )
    debug_printf ( "accepting commands on %s\n", path );
  unlink ( path ); /* delete socket if it exists */
  command_socket_init ( path );
  if (bind ( socket_fd, (struct sockaddr*) &sock_name, sizeof ( sock_name )) == -1)
    debug_printf("bind() of socket failed with error %d\n", errno);

  listen ( socket_fd, 2 ); /* listen with max. backlog of 2 */
  add_read_fd ( socket_fd, command_socket_handler );
  if ( debug_level )
    debug_printf( "initialized command socket (fd=%d)\n", new_fd );
}

void command_socket_comm_init ( void )
{
  char server_hostname[128];
  char path[UNIX_MAX_PATH];
  if ( session_directory == NULL )
    fatal_perror ( "session_directory not defined\n" );
  if ( gethostname ( server_hostname, 128 ) == -1 )
    fatal_perror ( "could not determine host name\n" );
  snprintf ( path, UNIX_MAX_PATH, "%s/socket-%s-%d", session_directory,
	     server_hostname, getpid() );
  if ( debug_level )
    debug_printf ( "accepting commands on %s\n", path );
  unlink ( path ); /* delete socket if it exists */

  command_socket_init ( path );

  bind ( socket_fd, (struct sockaddr*) &sock_name, sizeof ( sock_name ) );
  listen ( socket_fd, 2 ); /* listen with max. backlog of 2 */
  add_read_fd ( socket_fd, command_socket_handler );
  if ( debug_level )
    debug_printf( "initialized command socket (fd=%d)\n", new_fd );
}


void command_socket_server_remove ( void )
{
  remove_read_fd ( socket_fd );
  close ( socket_fd );
  unlink ( sock_name.sun_path );
}

// Create a command socket in ~/.univention-session-USER/HOST
void command_socket_client_init ( const char* client_host )
{
  char path[UNIX_MAX_PATH];
  char sub1[UNIX_MAX_PATH];
  char sub2[UNIX_MAX_PATH];

  struct passwd* pwd = getpwuid(getuid());

  if ( session_directory == NULL )
    fatal_perror ( "session_directory not defined\n" );

  snprintf (sub1, UNIX_MAX_PATH, "/tmp/.univention-session-%s/", pwd->pw_name);
  mkdir(sub1, S_IRWXU);

  snprintf (sub2, UNIX_MAX_PATH, "/tmp/.univention-session-%s/%s/", pwd->pw_name, client_host);
  mkdir(sub2, S_IRWXU);

  snprintf ( path, UNIX_MAX_PATH, "/tmp/.univention-session-%s/%s/socket", pwd->pw_name, client_host);

  if ( debug_level )
    debug_printf ( "accepting commands on %s\n", path );
  unlink ( path ); /* delete socket if it exists */
  command_socket_init ( path );
  bind ( socket_fd, (struct sockaddr*) &sock_name, sizeof ( sock_name ) );
  listen ( socket_fd, 2 ); /* listen with max. backlog of 2 */
  add_read_fd ( socket_fd, command_socket_handler );
  if ( debug_level )
    debug_printf( "initialized command socket (fd=%d)\n", new_fd );

  // ??
  // connect ( socket_fd, (struct sockaddr*) &sock_name, sizeof ( sock_name ) );

}


// Connect to an existing command socket to submit a command
int command_socket_connect ( const char* path )
{
  command_socket_init ( path );
  //  bind ( socket_fd, (struct sockaddr*) &sock_name, sizeof ( sock_name ) );
  connect ( socket_fd, (struct sockaddr*) &sock_name, sizeof ( sock_name ) );
  return socket_fd;
}
