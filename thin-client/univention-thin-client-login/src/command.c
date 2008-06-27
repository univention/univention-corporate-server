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
#include <wait.h>
#include <string.h>
#include <ctype.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <pwd.h>

#include "command.h"
#include "debug.h"
#include "process.h"
#include "protocol.h"
#include "security.h"

#include <univention/config.h>

extern long GLOBAL_TIMEOUT;
char * cleanup_script = NULL;


int alive_handler ( char ** argv ) {

  return 0;
}

int ok_handler ( char ** argv ) {

  fatal_error ( "MUST NOT HAPPEN: Got ok as a command\n" );
  return 0;
}

int setenv_handler ( char ** argv ) {

  if ( !argv || !argv[0] || !argv[0][0] || !argv[1] || ! argv[1][0] )
    fatal_error ( "setenv called with to few arguments\n" );

  if ( setenv ( argv[0], argv[1], 1 ) < 0 )
    fatal_error ( "setenv failed!" );

  return 0;
}

int unsetenv_handler ( char ** argv ) {

  if ( !argv || !argv[0] || !argv[0][0] )
    fatal_error ( "unsetenv called with to few arguments\n" );

  if ( unsetenv ( argv[0] ) < 0 )
    fatal_error ( "unsetenv failed!" );

  return 0;
}

int timeout_handler ( char ** argv ) {
  int res;

  if ( !argv || !argv[0] || !argv[0][0] )
    fatal_error ( "timeout called with to few arguments\n" );

  if (!strcmp(argv[0],"baseconfig")) {
    res=univention_config_get_long(argv[1]);
	if (res > 0 ) {
    	GLOBAL_TIMEOUT=res;
	} else {
		/* set to default value */
		GLOBAL_TIMEOUT=20;
	}
  } else {
    GLOBAL_TIMEOUT=atol(argv[0]);
  }

  return 0;
}

int run_handler ( char ** argv ) {

  if ( !argv || !argv[0] || !argv[0][0] )
    fatal_error ( "run called without arguments\n" );

  return run_process ( argv );
}

int start_handler ( char ** argv ) {
  if ( !argv || !argv[0] || !argv[0][0] )
    fatal_error ( "start called without arguments\n" );

  start_process ( argv, NULL );

  return 0;
}

int exit_handler ( char ** argv ) {
  exit (0);
}

int error_handler ( char ** argv ) {
  exit (1);
}

void call_cleanup_script ( void ) {
  char * argv[2];

  if ( cleanup_script == NULL ) return;
  argv[0] = cleanup_script;
  argv[1] = NULL;

  run_process ( argv );

  cleanup_script = NULL; /* prevent cleanup script from being run twice */

  return;
}

int cleanup_handler ( char ** argv ) {
  if ( !argv || !argv[0] || !argv[0][0] )
    fatal_error ( "cleanup called without arguments\n" );

  if ( cleanup_script != NULL ) free ( cleanup_script );
  cleanup_script = strdup ( argv[0] );
  // atexit ( call_cleanup_script );

  return 0;
}

int create_file ( char * file, int newfd ) {
  int fd;

  fd = open ( file, O_WRONLY | O_CREAT | O_TRUNC, S_IRUSR | S_IWUSR );
  if ( fd < 0 )
    fatal_perror ( "can't open file : %s", file );

  if ( dup2 ( fd, newfd ) < 0 )
    fatal_perror ( "dup2 failed" );

  close ( fd );
  return 0;
}

int stdout_handler ( char ** argv ) {

  if ( !argv || !argv[0] || !argv[0][0] )
    fatal_error ( "stdout called without arguments\n" );
  return create_file ( argv[0], STDOUT_FILENO );
}

int stderr_handler ( char ** argv ) {

  if ( !argv || !argv[0] || !argv[0][0] )
    fatal_error ( "stderr called without arguments\n" );
  return create_file ( argv[0], STDERR_FILENO );
}

int exit_on_last = 0;

int exit_on_last_handler ( char ** argv ) {
  exit_on_last = 1;
  return 0;
}

int mount_handler ( char ** argv ) {

  struct passwd* pwd = getpwuid ( getuid() );
  char *args[5];
  char *p;

  if ( !argv || !argv[0] || !argv[0][0] || !argv[1] || !argv[1][0] )
    fatal_error ( "mount called with too few arguments\n" );

  if ( pwd == NULL )
    fatal_perror ( "could not determine username\n" );

  if ( strcmp(argv[0], "start") != 0 && strcmp(argv[0], "stop") != 0 )
    fatal_perror ( "invalid mount action" );

  /* check for bad hostname */
  for ( p = argv[1]; *p != '\0'; ++p ) {
    if ( !isalnum ( *p ) )
      fatal_perror ( "hostname seems to be invalid\n" );
  }

  args[0] = "/usr/sbin/import-devices.sh";
  args[1] = argv[0];
  args[2] = pwd->pw_name;
  args[3] = argv[1];
  args[4] = NULL;

  become_root();
  start_process ( args, NULL );
  unbecome_root();

  return 0;
}

struct command COMMANDS[] = {
  { 1, "alive", alive_handler },
  { 2, "ok", ok_handler },
  { 3, "setenv", setenv_handler },
  { 4, "run", run_handler },
  { 5, "start", start_handler },
  { 6, "exit", exit_handler },
  { 7, "error", error_handler },
  { 8, "cleanup", cleanup_handler },
  { 9, "stdout", stdout_handler },
  { 10, "stderr", stderr_handler },
  { 11, "exit_on_last_child", exit_on_last_handler },
  { 12, "mount", mount_handler },
  { 13, "unsetenv", unsetenv_handler },
  { 14, "timeout", timeout_handler },
  { 0, NULL, NULL }
};


int call_handler ( int cmdid, char ** argv ) {
  int i=0;

  while ( COMMANDS[i].id != 0 ) {
    if ( COMMANDS[i].id == cmdid ) {
      return COMMANDS[i].handler ( argv );
    }
    i++;
  }
  fatal_error ( "handler called with unknown command: %d\n", cmdid );
  return 1;
}

int execute_command ( char * buffer ) {

  char * argv[MAX_CMD_ARGS];
  char ** p = argv;
  int cmdid = get_command_id_by_id ( &buffer );

  get_command_args ( buffer, p, MAX_CMD_ARGS );

  return call_handler ( cmdid, argv );
}

int get_command_id_by_id ( char ** buffer ) {

  char *p;
  int i=0;
  int cmd = strtol ( *buffer, &p, 10 );

  while ( COMMANDS[i].id != 0 ) {
    if ( COMMANDS[i].id == cmd ) {
      while ( *p == ' ' ) p++;
      *buffer=p;
      return cmd;
    }
    i++;
  }
  fatal_error ( "got unknown command: %d (from: %s)\n", cmd, *buffer );
  return cmd;
}

int get_command_id_by_name ( char ** buffer ) {

  char *p;
  char *buf = *buffer;
  int i=0;
  int cmd = 0;

  while ( buf[i] != '\0' ) {
    if  ( (buf[i] == ' ') || (buf[i] == '\n')  ) {
      buf[i] = '\0';
      i++;
      break;
    }
    i++;
  }
  if ( debug_level ) debug_printf ( "got command %s (i=%d)\n", buf, i );

  p=&buf[i];

  i=0;
  while ( COMMANDS[i].id != 0 ) {
    if ( strcmp ( COMMANDS[i].string, *buffer ) == 0 ) {
      cmd = COMMANDS[i].id;
      *buffer=p;
      return cmd;
    }
    i++;
  }
  fatal_error ( "got unknown command: %s\n", *buffer );
  return cmd;
}

int get_command_args ( char * buffer, char ** argv, int max ) {
  int i=0;
  int arg=0;

  if ( debug_level )
    debug_printf ( "parsing: %s\n", buffer );

  if ( !buffer || !buffer[0] ) {
    if ( max > 0 ) argv[0] = NULL;
    return 0;
  }

  argv[arg] = &buffer[i];

  while ( ( buffer[i] != '\0' ) && ( buffer[i] != '\n' ) ) {
    if  ( buffer[i] == ' ' ) {
      buffer[i] = '\0';
      i++;
      while ( buffer[i] == ' ' ) i++;
      if ( ( buffer[i] == '\0' ) || ( buffer[i] == '\n' ) ) break;
      arg++;
      if ( arg > max ) fatal_error ( "too many arguments\n" );
      argv[arg]=&buffer[i];
    }
    i++;
  }
  argv[arg+1] = NULL;
  return arg;
}

void send_command_by_name ( char * cmd, char ** argv )
{
  int cmdid=0;
  int i=0;

  while ( COMMANDS[i].id != 0 ) {
    if ( strcmp ( cmd, COMMANDS[i].string ) == 0 )
      cmdid = COMMANDS[i].id;
    i++;
  }
  if ( cmdid == 0 )
    fatal_error ( "got unknown command: %s\n", cmd );

  send_command_by_id ( cmdid, argv );
}

void send_command_by_id ( int cmdid, char ** argv )
{
  char buffer[MAX_CMD_LEN];
  char *p = buffer;
  int i=0;

  sprintf ( p, "%d", cmdid );
  p = p + strlen ( buffer );

  i=0;
  if ( argv != NULL ) {
    while ( argv[i] != NULL )
      {
	if ( ( strlen ( buffer ) + strlen ( argv[i] ) ) > MAX_CMD_LEN-3 )
	  fatal_error ( "command length to long\n" );
	*p++=' ';
	sprintf ( p, "%s", argv[i] );
	p = p + strlen ( argv[i] );
	i++;
      }
  }
  *p++ = '\n';
  *p++ = '\0';

  if ( debug_level )
    debug_printf ( "sending command: %s", buffer );

  send_command ( buffer );
}
