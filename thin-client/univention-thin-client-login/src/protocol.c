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
#include <string.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/select.h>
#include <signal.h>
#include <unistd.h>
#include <wait.h>
#include <errno.h>

extern int errno;

#include "debug.h"
#include "connection.h"
#include "protocol.h"
#include "command.h"
#include "pipe.h"
#include "signals.h"
#include "select_loop.h"

long GLOBAL_TIMEOUT=20;


void send_command_fd ( char * buffer, int recv_fd, int send_fd )
{
  int len;
  char tmpbuf[256];

  /* __block_signals(); */

  if ( debug_level )
    debug_printf ( "sending command: %s", buffer );

  if ( send_fd == -1 ) fatal_error ( "pipe not open\n" );

  len = write_to_pipe ( send_fd, GLOBAL_TIMEOUT, buffer );

  if ( len != strlen ( buffer ) )
       fatal_error ( "failed to send command: %s\n", buffer );

  /* now wait for ok from the other side */

  if ( read_from_pipe ( recv_fd, GLOBAL_TIMEOUT, tmpbuf, 255 ) == 0 )
    fatal_error ( "failed to get ok\n" );

  if ( strcmp ( tmpbuf, "ok" ) != 0 )
    fatal_error ( "failed to get ok, got %s\n", tmpbuf );

  /* __unblock_signals(); */

  return;

}

void send_command ( char * buffer )
{
  send_command_fd ( buffer, recv_fd, send_fd );
}

void recv_command_fd ( char * buffer, int buflen, int recv_fd, int send_fd )
{

  /* __block_signals(); */

  if ( debug_level )
    debug_printf ( "receiving command\n" );

  if ( recv_fd == -1 ) fatal_error ( "pipe not open\n" );

  if ( read_from_pipe ( recv_fd, GLOBAL_TIMEOUT, buffer, buflen ) == 0 )
    fatal_error ( "failed to read command\n" );

  if ( strcmp ( buffer, "ok" ) == 0 )
    fatal_error ( "got ok as command\n" );

  if ( write_to_pipe ( send_fd, GLOBAL_TIMEOUT, "ok\n" ) < 2 )
    fatal_error ( "can't answer ok\n" );

  /* __unblock_signals(); */

  return;
}

void recv_command ( char * buffer, int buflen )
{
  recv_command_fd ( buffer, buflen, recv_fd, send_fd );
}

void init_server ( void )
{
  init_server_pipes();
  /* add_read_fd ( recv_fd, handler ); */
}
