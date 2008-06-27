/*
 * Univention Client Login
 *  this file is part of the Univention thin client tools
 *
 * Copyright (C) 2004, 2005, 2006 Univention GmbH
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
#include "pipe.h"
#include "process.h"
#include "select_loop.h"
#include "cmd_handler.h"

extern char * script_name;

int to_script_pipe = -1;
int from_script_pipe = -1;
int script_pid = -1;

// Read from the script handle and generate a command packet that is sent on the wire
// Returns the size of the read command in bytes.
int script_read_handler ( int fd )
{
  int len;
  char *argv[MAX_CMD_ARGS];
  char **p=argv;

  char * buffer = malloc ( MAX_CMD_LEN * sizeof ( char ) );
  char *b = buffer;
  char *complete = malloc (MAX_CMD_LEN * sizeof (char ));
  if ( buffer == NULL )
    fatal_error ( "malloc_failed\n" );

  //  complete = buffer;

  len = read_from_script_pipe ( from_script_pipe, 0, buffer, MAX_CMD_LEN );

  if ( len == 0 ) {
    free ( b );
    return ( -1 );
  }

  if ( debug_level )
    debug_printf ( "command from script: %s (%d bytes long)\n", buffer, strlen(buffer) );

  int argcount = get_command_args ( buffer, p, MAX_CMD_ARGS );
  int argslength = 0;

  if ( argv )
    {
      int i;
      debug_printf ( "args: ");
      if (argcount > 0)
	{
	  for (i = 1; argv[i]; i++)
	    {
	      strcat(complete, argv[i]);
	      strcat(complete, " ");
	    }
	}
    }

  if ( debug_level )
    debug_printf ( "command from script short: %s (%d args) \n", argv[0], argcount );

  argslength=strlen(complete);

  struct message sendpacket;
  sendpacket.args = complete;
  sendpacket.args_length = argslength;
  sendpacket.data = NULL;
  sendpacket.data_length = 0;

  if (strcmp(argv[0],"alive") == 0)
    sendpacket.command = COMMAND_ALIVE;
  else if (strcmp(argv[0],"setenv") == 0)
    sendpacket.command = COMMAND_SETTING_SETENV;
  else if (strcmp(argv[0],"run") == 0)
    sendpacket.command = COMMAND_EXEC;
  else if (strcmp(argv[0],"start") == 0)
    sendpacket.command = COMMAND_START;
  else if (strcmp(argv[0],"exit") == 0)
    sendpacket.command = COMMAND_END_EXIT;
  else if (strcmp(argv[0],"error") == 0)
    sendpacket.command = COMMAND_ERROR;
  else if (strcmp(argv[0],"cleanup") == 0)
    sendpacket.command = COMMAND_END_CLEANUP;
  else if (strcmp(argv[0],"stdout") == 0)
    sendpacket.command = COMMAND_RED_STDOUT;
  else if (strcmp(argv[0],"stderr") == 0)
    sendpacket.command = COMMAND_RED_STDERR;
  else if (strcmp(argv[0],"exit_on_last_child") == 0)
    sendpacket.command = COMMAND_END_WAITCHILD;
  else if (strcmp(argv[0],"mount") == 0)
    sendpacket.command = COMMAND_MOUNT;
  else if (strcmp(argv[0],"unsetenv") == 0)
    sendpacket.command = COMMAND_SETTING_UNSETENV;

  //  debug_printf("command type %d\n", sendpacket.command);

  // FIXME, 1 byte offset of str??
  //  sendpacket.args_length = strlen(buffer);

  protocol_send_message(&sendpacket);

  free ( b );
  return len;
}

void script_kill ( void )
{
  //  int pid = script_pid;
  void kill_process ( int pid );
  script_pid = -1;
  remove_read_fd ( from_script_pipe );
}

void script_exit_handler ( void )
{
  script_pid = -1;
  debug_printf ( "session setup script finished\n" );
  remove_read_fd ( from_script_pipe );
  return;
}

void start_script ( char * arg )
{
  char *argv[3];
  char **p = argv;
  char * my_script;
  int to_fd, from_fd;

  my_script = script_name;
  if ( !my_script ) my_script = getenv ( "SESSION_SCRIPT" );
  if ( !my_script ) my_script = "uv-default-session-script";

  *p++ = my_script;
  *p++ = arg;
  *p++ = NULL;

  if (debug_level)
    {
      int i;
      debug_printf ( "starting script: ");
      for (i = 0; argv[i]; i++)
	fprintf ( stderr, "%s ", argv[i]);
      fprintf ( stderr, "\n" );
    }

  script_pid = start_piped ( argv, &to_fd, &from_fd, script_exit_handler );
  //  script_pid = start_piped ( argv, &send_fd, &recv_fd, script_exit_handler );

  //  if (debug_level)
  //    debug_printf("start_piped : %i %i\n", send_fd, recv_fd);

  to_script_pipe = to_fd;
  from_script_pipe = from_fd;
  atexit ( script_kill );

  if (debug_level)
    debug_printf("Reading from script pipe fd %d\n", from_script_pipe);

  add_read_fd ( from_script_pipe, script_read_handler );

  //  if (debug_level)
  //      debug_printf ( "established script pipe on fd%d\n ", from_script_pipe);

}

void run_stop_script ( void )
{
  char *argv[3];
  char **p = argv;
  char * my_script;

  my_script = script_name;
  if ( !my_script ) my_script = getenv ( "SESSION_SCRIPT" );
  if ( !my_script ) my_script = "uv-default-session-script";

  *p++ = my_script;
  *p++ = "stop";
  *p++ = NULL;

  if (debug_level)
    {
      int i;
      debug_printf ( "starting stop script: ");
      for (i = 0; argv[i]; i++)
	fprintf ( stderr, "%s ", argv[i]);
      fprintf ( stderr, "\n" );
    }

  script_pid = run_process ( argv );

}
