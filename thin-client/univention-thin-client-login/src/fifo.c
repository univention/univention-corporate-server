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
#include <unistd.h>

#include "debug.h"
#include "protocol.h"
#include "command.h"
#include "process.h"
#include "select_loop.h"
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>


extern char * script_name;

int fifo_fd = -1;


int fifo_read_handler ( int fd )
{
  int len;
  int cmd;
  char *argv[MAX_CMD_ARGS];
  char **p=argv;

  char * buffer = malloc ( MAX_CMD_LEN * sizeof ( char ) );
  char *b = buffer;
  if ( buffer == NULL )
    fatal_error ( "malloc_failed\n" );

  if ( debug_level )
    debug_printf ( "fifo_read_handler\n" );

  len = read_from_pipe ( fifo_fd, 0, buffer, MAX_CMD_LEN );
  if ( len == 0 ) {
    free ( b );
    return ( -1 );
  }

  if ( debug_level )
    debug_printf ( "command from script: %s\n", buffer );

  cmd = get_command_id_by_name ( &buffer );
  if ( debug_level )
    debug_printf ( "received cmd %d\n", cmd );

  get_command_args ( buffer, p, MAX_CMD_ARGS );

  if (debug_level && argv )
    {
      int i;
      debug_printf ( "args: ");
      for (i = 0; argv[i]; i++)
	fprintf ( stderr, "%s ", argv[i]);
      fprintf ( stderr, "\n" );
    }

  send_command_by_id ( cmd, argv );

  free ( b );
  return len;
}

void open_fifo ( char *name )
{
  if (name)
    {
      fifo_fd = open( name, O_NONBLOCK | O_RDONLY );
      if (debug_level)
        debug_printf( "opened %s as fd %d\n", name, fifo_fd );
      if ( fifo_fd != -1 ) 
       add_read_fd( fifo_fd, fifo_read_handler );
    }	
}

