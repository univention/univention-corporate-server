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

#include <stdlib.h>
#include <stdio.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/select.h>
#include <signal.h>
#include <unistd.h>
#include <wait.h>
#include <errno.h>

extern int errno;

#include "debug.h"
#include "process.h"
#include "protocol.h"
#include "command.h"
#include "select_loop.h"

extern int should_exit;


int send_fd = -1;
int recv_fd = -1;

int rsh_pid = -1;

int connection_read_handler ( int fd )
{
	char buf[MAX_CMD_LEN];

	if ( debug_level )
		debug_printf ( "connection_read_handler\n" );
	recv_command ( buf, MAX_CMD_LEN );
	if ( debug_level )
		debug_printf ( "received command: %s\n", buf );
	execute_command ( buf );

	return 0;
}

void init_server_pipes ( void )
{
	/* FIXME: what is fd 3? maybe use dup() instead */
	send_fd = dup2 ( STDOUT_FILENO, 3 );
	if ( send_fd < 0 )
		fatal_perror ( "dup failed" );
	close ( STDOUT_FILENO );
	if ( debug_level )
		debug_printf ( "to_client fd=%d\n", send_fd );
	/* FIXME: see above */
	recv_fd = dup2 ( STDIN_FILENO, 4);
	if ( recv_fd < 0 )
		fatal_perror ( "dup failed" );
	close ( STDIN_FILENO );
	add_read_fd ( recv_fd, connection_read_handler );
	if ( debug_level )
		debug_printf ( "from_client fd=%d\n", recv_fd );
	return;
}

/* pipes should be closed in remove_process() (process.c) */
void client_connection_exit_handler ( void )
{
	rsh_pid = -1;
	debug_printf ( "connection to server died\n" );
	should_exit = 0;
	return;
}

void connect_to_server ( void )
{
	char *argv[10];
	char **p = argv;
	char * session_rsh, * session_server, * my_server;
	int to_fd, from_fd;
	char * ssh_debug = "-v"; /* XXX: this doesn't work with krsh */
	char * krsh_debug = "-d"; /* XXX: this doesn't work with krsh */
	char * server_debug = "-d2";
	char * krsh_forward = "-f";
	int fd;

	extern char * server_host;
	extern char * server_prog;

	session_rsh = getenv ( "SESSION_RSH" );
	if ( !session_rsh ) session_rsh = "rsh";

	session_server = server_prog;
	if ( !session_server ) session_server = getenv ( "SESSION_SERVER" );
	if ( !session_server ) session_server = "univention-session";
	my_server = server_host;
	if ( !my_server ) my_server = getenv ( "SESSION_HOST" );
	if ( !my_server ) fatal_error ( "no server\n" );

	*p++ = session_rsh;
	if ( strncmp( "krsh",session_rsh, 4)==0) {
		*p++ = krsh_forward;
		if ( debug_level > 1 ) {
			*p++ = krsh_debug;
		}
	} else if ( debug_level > 1 ) {
		*p++ = ssh_debug;
	}
	*p++ = my_server;
	*p++ = session_server;
	if ( debug_level )
		*p++ = server_debug;
	*p++ = NULL;

	if (debug_level)
	{
		int i;
		debug_printf ( "starting server: ");
		for (i = 0; argv[i]; i++)
			fprintf ( stderr, "%s ", argv[i]);
		fprintf ( stderr, "\n" );
	}

	rsh_pid = start_piped ( argv, &to_fd, &from_fd, client_connection_exit_handler );

	send_fd = to_fd;
	recv_fd = from_fd;
	add_read_fd ( recv_fd, connection_read_handler );

	if ( debug_level )
		debug_printf ( "pipes: to: %d from: %d\n", send_fd, recv_fd );

}
