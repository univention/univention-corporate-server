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
#include <sys/types.h>
#include <wait.h>
#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>

#include "debug.h"
#include "process.h"

int sig_block_count = 0;
sigset_t block_mask;

void __block_signals ( void )
{
  static int init_done = 0;

  if ( (sig_block_count++) != 1 ) return;

  if ( init_done == 0 ) {
    sigemptyset ( &block_mask );
    sigaddset ( &block_mask, SIGPIPE );
    sigaddset ( &block_mask, SIGHUP );
    sigaddset ( &block_mask, SIGINT );
    sigaddset ( &block_mask, SIGQUIT );
    sigaddset ( &block_mask, SIGTERM );
    sigaddset ( &block_mask, SIGABRT );
    sigaddset ( &block_mask, SIGCHLD );
    init_done = 1;
  }

  sigprocmask ( SIG_BLOCK, &block_mask, NULL );
  return;
}

void __unblock_signals ( void )
{
  sigset_t sigset;

  if ( (sig_block_count--) != 0 ) return;
  sigprocmask ( SIG_UNBLOCK, &block_mask, NULL );

  /*

  if ( sigpending ( &sigset ) == 0 ) {
    if ( sigismember ( &sigset, SIGCHLD ) ) {
      raise ( SIGCHLD );
    }

  */
}


static void sigterm_handler( int sig )
{
  if ( debug_level )
    debug_printf ( "got signal %d\n", sig );
  exit(1);  /* make sure atexit functions get called */
}

static void sigchld_handler( int sig )
{
  int status;
  pid_t pid;

  pid = wait ( &status );

  if ( pid == -1 ) {
    if ( debug_level ) debug_printf ( "wait failed\n" );
    return;
  }
  if ( debug_level )
    debug_printf ( "sigchld_handler called for process %d\n", pid );

  if ( remove_process ( pid ) < 0 )
    debug_printf ( "got SIGCHLD from unknown process %d\n", pid );

  return;

}

void install_handler ( int sig, void (*handler)(int sig) )
{
    struct sigaction setup_action;
    sigset_t block_mask;

    sigemptyset ( &block_mask );
    sigaddset ( &block_mask, SIGPIPE );
    sigaddset ( &block_mask, SIGHUP );
    sigaddset ( &block_mask, SIGINT );
    sigaddset ( &block_mask, SIGQUIT );
    sigaddset ( &block_mask, SIGTERM );
    sigaddset ( &block_mask, SIGABRT );
    sigaddset ( &block_mask, SIGCHLD );

    setup_action.sa_handler = handler;
    setup_action.sa_mask = block_mask;
    setup_action.sa_flags = 0;
    sigaction ( sig, &setup_action, NULL );
}

/* initialize signal handling */
void signal_init(void)
{
#if 0
    signal( SIGPIPE, sigterm_handler );
    signal( SIGHUP, sigterm_handler );
    signal( SIGINT, sigterm_handler );
    signal( SIGQUIT, sigterm_handler );
    signal( SIGTERM, sigterm_handler );
    signal( SIGABRT, sigterm_handler );
    signal ( SIGCHLD, sigchld_handler );
#endif
    install_handler ( SIGPIPE, &sigterm_handler );
    install_handler ( SIGHUP, &sigterm_handler );
    install_handler ( SIGINT, &sigterm_handler );
    install_handler ( SIGQUIT, &sigterm_handler );
    install_handler ( SIGTERM, &sigterm_handler );
    install_handler ( SIGABRT, &sigterm_handler );
    install_handler ( SIGCHLD, &sigchld_handler );
}
