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
#include <unistd.h>
#include <sys/time.h>
#include <sys/types.h>
#include <errno.h>

#include "debug.h"
#include "select_loop.h"

struct timer * first_timer = NULL;
struct filedes * first_read_fd = NULL;
struct filedes * first_write_fd = NULL;

int should_exit = -1;


int add_timer ( long usec, timeout_handler handler  )
{
  int id = 1;
  struct timer* tmp;
  struct timer* ti = malloc ( sizeof ( struct timer ) );

  if ( ti == NULL ) {
    return -1;
  }

  if ( first_timer == NULL ) {
    first_timer = ti;
  }
  else {
    for ( tmp = first_timer; ;tmp = tmp->next ) {
      id = ( id > tmp->id ) ? id : tmp->id + 1;
      if ( tmp->next == NULL ) break;
    }
    tmp->next = ti;
  }
  ti->next = NULL;
  ti->id = id;
  ti->usec = usec;
  ti->remaining = usec;
  ti->handler = handler;

  return id;
}


int remove_timer ( int id )
{
  struct timer* tmp;

  for ( tmp = first_timer; tmp != NULL; tmp = tmp->next) {
    if ( tmp == first_timer && tmp->id == id ) {
      first_timer = tmp->next;
      free ( tmp );
      break;
    }
    if ( tmp != NULL && tmp->next->id == id ) {
      struct timer * to_delete = tmp->next;
      tmp->next = tmp->next->next;
      free ( to_delete );
      break;
    }
  }

  return id;
}


int add_write_fd ( int fd, filedes_handler handler )
{

  return 0;
}

int remove_write_fd ( int fd )
{

  return 0;
}

int add_read_fd ( int fd, filedes_handler handler )
{
  struct filedes* ti = malloc ( sizeof ( struct filedes ) );

  if ( ti == NULL ) {
    return -1;
  }

  ti->next = first_read_fd;
  first_read_fd = ti;
  ti->fd = fd;
  ti->handler = handler;
  ti->to_remove = 0;

  return fd;
}

int __remove_read_fd ( int fd )
{
  struct filedes* tmp;

  for ( tmp = first_read_fd; tmp != NULL; tmp = tmp->next) {
    if ( tmp == first_read_fd && tmp->fd == fd ) {
      first_read_fd = tmp->next;
      free ( tmp );
      break;
    }
    if ( tmp != NULL && tmp->next->fd == fd ) {
      struct filedes* to_delete = tmp->next;
      tmp->next = tmp->next->next;
      free ( to_delete );
      break;
    }
  }

  return fd;
}

int remove_read_fd ( int fd )
{
  struct filedes* tmp;

  for ( tmp = first_read_fd; tmp != NULL; tmp = tmp->next) {
    if ( tmp->fd == fd ) {
      tmp->to_remove = 1;
      break;
    }
  }

  return fd;
}

static int __inline__ init_fd_set ( fd_set* fds, struct filedes* first )
{
  struct filedes* tmp;
  int n = 0;

  FD_ZERO ( fds );
  for ( tmp = first; tmp != NULL; tmp = tmp->next) {
    FD_SET ( tmp->fd, fds );
    if ( tmp->fd > n )
      n = tmp->fd;
  }

  return n;
}

static struct timer __inline__ * shortest_timeout ( void ) {
  struct timer * tmp;
  struct timer * shortest = NULL;

  for ( tmp = first_timer; tmp != NULL; tmp = tmp->next) {
    if ( shortest == NULL || tmp->remaining < shortest->remaining ) {
      shortest = tmp;
    }
  }

  return shortest;
}

void select_loop ( void )
{
  fd_set readfds;
  fd_set writefds;

  for ( ; ; ) {

    int n = 0, r = 0;
    long timeout = -1, waited = 0;
    struct timeval to, before_select, after_select;
    struct timer * to_tmp, *stimeout;
    struct filedes * fd_tmp;
    int ready_fds = 0;

    if ( should_exit != -1 ) exit ( should_exit );


    /* find out highest numbered file descriptor for select */
    if ( ( r = init_fd_set ( &readfds, first_read_fd ) ) > n )
      n = r;
    if ( ( r = init_fd_set ( &writefds, first_write_fd ) ) > n )
      n = r;

    /* find out timeout for select */
    stimeout = shortest_timeout();
    if ( stimeout != NULL ) {
      timeout = stimeout->remaining;
      to.tv_sec = timeout / 1000000;
      to.tv_usec = timeout % 1000000;
    }

    if (n == 0 && stimeout == NULL) {
      debug_printf ( "nothing to wait for, exiting...\n" );
      exit(0);
    }

    if ( debug_level )
      debug_printf ( "select ( %d )\n", n );
    gettimeofday ( &before_select, 0 );
    ready_fds = select ( n+1, &readfds, &writefds, NULL,
			 stimeout == NULL ? NULL : &to );
    gettimeofday ( &after_select, 0 );

    if ( ready_fds == -1 && errno == EINTR ) {
      debug_perror ( "select" );
      continue;
    } else if ( ready_fds == -1 ) {
      fatal_perror ( "select" );
    }

    waited = (after_select.tv_sec-before_select.tv_sec)*1000000
      + after_select.tv_usec-before_select.tv_usec;

    /* timeout? */
    for ( to_tmp = first_timer; to_tmp != NULL; to_tmp = to_tmp->next) {
      to_tmp->remaining -= waited;
      if ( debug_level )
	debug_printf ( "timer: %d/%d\n", to_tmp->remaining, to_tmp->usec );
      if ( to_tmp->remaining < 1 ) {
	to_tmp->handler ( to_tmp->id );
	to_tmp->remaining = to_tmp->usec;
      }
    }

    /* file descriptor ready? */
    for ( fd_tmp = first_read_fd; fd_tmp != NULL; fd_tmp = fd_tmp->next) {
      if ( ready_fds > 0 && FD_ISSET ( fd_tmp->fd, &readfds ) ) {

	int r = fd_tmp->handler ( fd_tmp->fd );
	if ( debug_level )
	  debug_printf ( "file descriptor %d is ready\n", fd_tmp->fd );
	if ( fd_tmp->to_remove && r == -1 ) {
	  if ( debug_level )
	    debug_printf ( "removing fd %d from select_loop\n", fd_tmp ->fd );
	  __remove_read_fd ( fd_tmp->fd );
	}
      }
    }
    for ( fd_tmp = first_write_fd; fd_tmp != NULL; fd_tmp = fd_tmp->next) {
      if ( ready_fds > 0 && FD_ISSET ( fd_tmp->fd, &writefds ) ) {
	fd_tmp->handler ( fd_tmp->fd );
      }
    }

  }
}
