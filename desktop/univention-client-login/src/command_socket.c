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
#include <unistd.h>
#include <string.h>
#include <limits.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/un.h>

#include "debug.h"
#include "protocol.h"
#include "select_loop.h"
#include "command.h"
#include "session.h"

#define UNIX_MAX_PATH 108 /* man 7 unix (where is this defined?) */

int sock_fd = 0;
struct sockaddr_un sock_name;

int command_socket_client_handler ( int fd )
{
  int cmd;
  char *argv[MAX_CMD_ARGS];
  char **p=argv;

  char buf[MAX_CMD_LEN];
  char * buffer = buf;
  int r;

  if ( debug_level )
    debug_printf ( "command_socket_client_handler\n" );
  /*recv_command_fd ( buf, MAX_CMD_LEN, fd, fd );*/
  r = recv ( fd, buf, MAX_CMD_LEN, 0 );

  if ( debug_level )
    debug_printf ( "received command: %s\n", buf );

  if ( r == 0 ) {
    if ( debug_level )
      debug_printf ( "no data on socket (%d), closing...", fd );
    close ( fd );
    remove_read_fd ( fd );
    return -1;
  }

  cmd = get_command_id_by_name ( &buffer );
  if ( debug_level )
    debug_printf ( "received cmd %d\n", cmd );

  get_command_args ( buffer, p, MAX_CMD_ARGS );

  if (debug_level && argv )
    {
      int i;
      debug_printf ( "args: ");
      for (i = 0; argv[i]; i++)
	debug_printf ( "%s ", argv[i]);
      debug_printf ( "\n" );
    }

  send_command_by_id ( cmd, argv );

  return 0;
}

/* create a new connection */
int command_socket_handler ( int fd )
{
  int len = sizeof ( sock_name );
  int new_fd = accept ( sock_fd, (struct sockaddr*) &sock_name, &len );
  if (new_fd != -1) {
    add_read_fd ( new_fd, command_socket_client_handler );
    if ( debug_level )
      debug_printf( "accepted new connection (fd=%d) on socket\n", new_fd );
  }
  return 0;
}

void command_socket_init ( const char* path )
{
  memset ( &sock_name, 0, sizeof ( struct sockaddr_un ) );
  sock_name.sun_family = AF_UNIX;
  strncpy ( sock_name.sun_path, path, UNIX_MAX_PATH );
  sock_fd = socket ( PF_UNIX, SOCK_STREAM, 0 );
}

void command_socket_server_init ( void )
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
  bind ( sock_fd, (struct sockaddr*) &sock_name, sizeof ( sock_name ) );
  listen ( sock_fd, 2 ); /* listen with max. backlog of 2 */
  add_read_fd ( sock_fd, command_socket_handler );
}

void command_socket_server_remove ( void )
{
  remove_read_fd ( sock_fd );
  close ( sock_fd );
  unlink ( sock_name.sun_path );
}


void command_socket_client_init ( const char* path )
{
  command_socket_init ( path );
  connect ( sock_fd, (struct sockaddr*) &sock_name, sizeof ( sock_name ) );
}
