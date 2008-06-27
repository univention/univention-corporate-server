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

#include <signal.h>
#include <unistd.h>
#include <stdlib.h>

#include "debug.h"
#include "pipe.h"
#include "protocol.h"
#include "alive.h"
#include "command.h"
#include "select_loop.h"

int client_send_keep_alive ( int id )
{
  if ( debug_level )
    debug_printf ( "sending keep-alive\n" );
  send_command_by_name ( "alive", NULL );
  return 0;
}

void client_keep_alive_init ( void )
{
  add_timer ( 15000000, client_send_keep_alive );
}

int client_alive = 0;

int server_alive_handler ( char ** argv )
{
  client_alive = 1;
  return 0;
}

int server_check_client ( int id )
{
  if ( client_alive == 0 )
    fatal_error ( "client seems to be dead, aborting\n" );
  client_alive = 0;
  return 0;
}

void server_keep_alive_init ( void )
{
  COMMANDS[0].handler = server_alive_handler;
  add_timer ( 30000000, server_check_client );
}
