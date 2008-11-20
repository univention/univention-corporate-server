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
#include <wait.h>
#include <pthread.h>

#include "process.h"
#include "debug.h"
#include "signals.h"
#include "security.h"

extern int should_exit;

static pthread_mutex_t mut_process = PTHREAD_MUTEX_INITIALIZER;
// int initialized = 0;
int has_finished = 0;

void kill_process ( int pid ) {
  int status;
  struct timeval to_start, to;
  int i;
  int ret;

  to_start.tv_sec = 0;
  to_start.tv_usec = 1000;


  /* nothing to do */
  if ( pid < 1 ) return;

  if ( kill ( pid, 0 ) == 0 )
    {
      if ( debug_level )
	debug_printf ( "killing process %d\n", pid );

      become_root();
      kill ( pid, SIGTERM );
      unbecome_root();

      for ( i=0; i<20; i++ ) {
	if ( waitpid ( pid, &status, WNOHANG ) == pid ) goto success;
	if ( kill ( pid, 0 ) != 0 ) goto success;
	to = to_start;
	while ( 1 ) {
	  ret = select ( 1, NULL, NULL, NULL, &to );
	  if ( ret == -1 && errno == EINTR ) continue;
	  break;
	}
      }

      if ( debug_level )
	debug_printf ( "still not dead, trying harder\n" );

      become_root();
      kill ( pid, SIGKILL );
      unbecome_root();

      for ( i=0; i<20; i++ ) {
	if ( waitpid ( pid, &status, WNOHANG ) == pid ) goto success;
	if ( kill ( pid, 0 ) != 0 ) goto success;
	to = to_start;
	while ( 1 ) {
	  ret = select ( 1, NULL, NULL, NULL, &to );
	  if ( ret == -1 && errno == EINTR ) continue;
	  break;
	}
      }
    }

  debug_printf ( "we failed to kill process %d\n", pid );
  return;

 success:
  remove_process ( pid );
  return;

}

extern int exit_on_last;
child_process * first_child = NULL;
int nprocess=0;

void kill_childs ( void )
{
  child_process * tmp = first_child;

  __block_signals();
  while ( tmp != NULL ) {
    kill_process ( tmp->pid );
    tmp = tmp->next;
  }
  __unblock_signals();

  return;
}

void insert_process ( child_process * child )
{
  child_process * tmp = first_child;
  child_process * tmp2 = NULL;
  nprocess++;

  while ( tmp != NULL ) {
    tmp2 = tmp;
    tmp = tmp->next;
  }
  if ( tmp2 == NULL )
    first_child = child;
  else
    tmp2->next = child;

  if ( debug_level )
    debug_printf ( "number of childs now: %d\n", nprocess );

}

/* FIXME: should close any pipes associated with the process */

int remove_process ( int pid )
{
  child_process * tmp = first_child;
  child_process * tmp2 = NULL;
  exit_hdlr handler = NULL;

  nprocess--;
  if ( debug_level ) {
    debug_printf ( "number of childs now: %d\n", nprocess );
  }

  while ( tmp != NULL ) {
    if ( tmp->pid == pid ) {
      handler = tmp->exit_handler;
      if ( tmp == first_child ) {
        first_child = first_child->next;
      } else {
        tmp2->next = tmp->next;
      }
      free ( tmp );
      goto success;
    }
    tmp2 = tmp;
    tmp = tmp->next;
  }

  /*
  while ( tmp != NULL ) {
    if ( tmp->pid == pid ) {
      handler = tmp->exit_handler;
      if ( tmp2 == NULL ) {
	if ( first_child->next )
	  first_child = first_child->next;
	else
	  first_child = NULL;
	free ( tmp );
	goto success;
      }
      tmp2->next = tmp->next;
      free ( tmp );
      goto success;
    }
    tmp2 = tmp;
    tmp = tmp->next;
  }
  */
  return -1;

 success:
  if (handler != NULL)
    handler();
  if ( ( nprocess == 0  ) && ( exit_on_last == 1 )) {
    if ( debug_level ) {
      debug_printf ( "no more childs, exiting\n" );
    }
    should_exit = 0;
  }
  return 0;
}

int start_piped ( char ** argv, int * to_fd, int * from_fd, void (* exit_handler)(void) )
{
  int pid;

  /* pipes for stdout and stdin */
  int to_pipe[2];
  int from_pipe[2];
  int ready_pipe[2];

  /* structure to store the properties of the process */
  child_process * child = malloc ( sizeof ( child_process ));

  if ( debug_level ) {
    int i;
    debug_printf ( "start_piped: " );
    for ( i = 0; argv[i] != NULL; ++i )
      fprintf ( stderr, "%s ", argv[i] );
    fprintf ( stderr, "\n" );
  }

  /* create the pipes */
  if ( to_fd != NULL ) {
    if (pipe (to_pipe) < 0)
      fatal_perror ( "can't create pipe" );
  }
  if ( from_fd != NULL ) {
    if (pipe (from_pipe) < 0)
      fatal_perror ( "can't create pipe" );
  }
  if (pipe (ready_pipe) < 0)
    fatal_perror ( "can't create pipe" );

  /* we must not receive SIGCHLD for this process until it is in
     our process list */
  __block_signals();

  /* fork */
  pid = fork();

  if ( pid < 0 )
    fatal_perror ( "can't fork" );

  /* child */
  if ( pid == 0 ) {
    char tmp;

    if ( to_fd != NULL ) {
      if (dup2 (to_pipe[0], STDIN_FILENO) < 0)
	fatal_perror ( "child: dup2 failed" );
      if (close (to_pipe[1]) < 0)
	fatal_perror ( "child: close failed" );
    }

    if ( to_fd != NULL ) {
      if (dup2 (from_pipe[1], STDOUT_FILENO) < 0)
	fatal_perror ( "child: dup2 failed" );
      if (close (from_pipe[0]) < 0)
	fatal_perror ( "child: close failed" );
    }

    if (close (ready_pipe[1]) < 0)
      fatal_perror ( "child: close failed" );
    /* block until ready */
    read ( ready_pipe[0], &tmp, 1 );
    if (close (ready_pipe[0]) < 0)
      fatal_perror ( "child: close failed" );

    /* sleep (1); */

    /* do we need to manually reset the signals? execve(2) says no */
    execvp ( argv[0], argv );
    debug_printf ( "child: exec_failed\n" );
    _exit ( 1 );
  }

  child->pid = pid;

  if ( to_fd != NULL ) {
    if (close (to_pipe[0]) < 0)
      fatal_perror ( "close failed" );
    *to_fd = to_pipe[1];
    child->to_fd = to_pipe[1];
  }
  else {
    child->to_fd = -1;
  }
  if ( from_fd != NULL ) {
    if (close (from_pipe[1]) < 0)
      fatal_perror ( "close failed" );
    *from_fd = from_pipe[0];
    child->from_fd = from_pipe[1];
  }
  else {
    child->from_fd = -1;
  }

  child->exit_handler = exit_handler;
  child->next = NULL;

  insert_process( child );

  if (close (ready_pipe[0]) < 0)
    fatal_perror ( "child: close failed" );
  write ( ready_pipe[1], "", 1 ); /* process insert, child may continue */
  if (close (ready_pipe[1]) < 0)
    fatal_perror ( "child: close failed" );
  __unblock_signals();

  if ( debug_level )
    debug_printf ( "started pocess with pid %d\n", pid );

  return pid;

}

/* asynchron */
int start_process ( char ** argv, void (* exit_handler)(void) )
{
  int rc = 0;
  /*if ( ! initialized ) {
    pthread_mutex_unlock(&mut_process);
    initialized=1;
    }*/

  // start_process may only be called by one process at a time
  pthread_mutex_lock(&mut_process);
  rc = start_piped ( argv, NULL, NULL, exit_handler );
  pthread_mutex_unlock(&mut_process);

  return rc;
}


void call_when_finished ( void ) {
  has_finished = 1;
  return;
}

/* synchron */
int run_process ( char ** argv )
{
  int pid;
  struct timeval tv;

  /*if ( ! initialized ) {
    pthread_mutex_unlock(&mut_process);
    initialized=1;
    }*/

  // start_process may only be called by one process at a time
  pthread_mutex_lock(&mut_process);

  has_finished = 0;

  pid = start_piped ( argv, NULL, NULL, call_when_finished );

  tv.tv_sec = 0;
  tv.tv_usec = 100000;

  while(1){
    // wait for a signal (SIGCHLD)
    select (0, NULL, NULL, NULL, &tv );
    if (has_finished==1){
      pthread_mutex_unlock(&mut_process);
      return 0;
    }
  }

  // never reached
  return -1;
}
