/*
 * Univention Client Login
 *	this file is part of the Univention thin client tools
 *
 * Copyright 2001-2010 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
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

extern char * script_name;

int to_script_pipe = -1;
int from_script_pipe = -1;
int script_pid = -1;


int script_read_handler ( int fd )
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
    debug_printf ( "script_read_handler\n" );

  len = read_from_pipe ( from_script_pipe, 0, buffer, MAX_CMD_LEN );
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

void script_kill ( void )
{
  int pid = script_pid;
  kill_process ( pid );
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

  to_script_pipe = to_fd;
  from_script_pipe = from_fd;
  atexit ( script_kill );

  add_read_fd ( from_script_pipe, script_read_handler );

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
