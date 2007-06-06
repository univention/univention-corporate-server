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
#include <errno.h>
#include <stdarg.h>
#include <signal.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/select.h>
#include <unistd.h>
#include <fcntl.h>
#include <wait.h>

#include "debug.h"

int write_to_pipe ( int to_fd, int timeout, char * buffer )
{
  int ret, len;
  fd_set write_fds;
  struct timeval to;

  len = strlen ( buffer );

  to.tv_sec = timeout;
  to.tv_usec = 0;

  FD_ZERO(&write_fds);
  FD_SET(to_fd, &write_fds);

  if ( debug_level )
    debug_printf ( "writing to pipe (fd=%d): %s", to_fd, buffer );

  /* select non blocking io */
  if ( fcntl ( to_fd, F_SETFL, O_NONBLOCK ) != 0 )
    fatal_perror ( "can't select non-blocking io for fd %d", to_fd );

  while ( 1 ) {

    ret = write ( to_fd, buffer, len );

    if ( ret == -1 && ( errno == EAGAIN || errno == EINTR )) {
      /* wait until timeout or we can write */
      if ( timeout == 0 )
	ret = select ( to_fd+1, NULL, &write_fds, NULL, NULL );
      else
	ret = select ( to_fd+1, NULL, &write_fds, NULL, &to );

      if ( ret == -1 && errno == EINTR ) continue;
      if ( ret == -1 ) fatal_perror ( "select before write failed (fd=%d)", to_fd );
      if ( ret == 0 ) {
	if (debug_level )
	  debug_printf ( "select timed out (fd=%d)\n", to_fd );
	return 0;
      }
      continue;
    }

    if ( ret != len ) fatal_error ( "could not write %d bytes to fd %d\n", len, to_fd );
    return ret;
  }

  return 0;
}

int read_from_pipe ( int from_fd, int timeout, char * buffer, int buflen )
{
  fd_set read_fds;
  struct timeval to;
  char * p;
  int ret;
  int retval = 0;

  to.tv_sec = timeout;
  to.tv_usec = 0;

  FD_ZERO(&read_fds);
  FD_SET(from_fd, &read_fds);

  buffer[0]='\0';
  p = buffer;

  if ( debug_level )
    debug_printf ( "read pipe: %d\n", from_fd );

  while (1) {

    if ( timeout == 0 )
      ret = select ( from_fd+1, &read_fds, NULL, NULL, NULL );
    else
      ret = select ( from_fd+1, &read_fds, NULL, NULL, &to );

    if ( ret == -1 && errno == EINTR ) continue;
    if ( ret == -1 ) fatal_perror ( "select before read failed (fd=%d)", from_fd );
    if ( ret == 0 ) {
      if (debug_level )
	debug_printf ( "select timed out (fd=%d)\n", from_fd );
      return 0;
    }
    ret = read ( from_fd, p, 1 );
    if ( debug_level > 1 )
      debug_printf ( "read returned with %d\n", ret );

    /* happens, when the child dies during select */
    if ( ret == 0 ) return 0;

    if ( ret == -1 ) fatal_perror ( "read failed" );

    if ( ret > 1 ) fatal_error ( "got more than one char from read\n" );

    /* terminate the read result */
    p[1]='\0';

    if ( buffer[retval] == '\n' ) {
      buffer[retval]='\0';
      break;
    }

    retval++;
    p++;

    if ( retval == buflen ) {
      fatal_error ( "string from pipe to long: %s\n", buffer );
    }
  }

  if ( debug_level )
    debug_printf ( "string from pipe: %s\n", buffer );

  return retval;
}
