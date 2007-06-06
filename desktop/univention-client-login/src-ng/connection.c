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
#include <sys/types.h>
#include <sys/time.h>
#include <sys/select.h>
#include <signal.h>
#include <unistd.h>
#include <wait.h>
#include <errno.h>

#include "debug.h"
#include "process.h"
#include "protocol.h"
#include "command.h"
#include "select_loop.h"
#include "cmd_handler.h"

extern int should_exit;

int send_fd = -1;
int recv_fd = -1;
int rsh_pid = -1;

int connection_read_handler(int fd)
{
  struct message received;
  memset ( &received , 0, sizeof(struct message));

  //  if (debug_level)
  //    debug_printf("read: begun %d %d\n", recv_fd, send_fd);

  protocol_recv_message (&received);

  if (debug_level && received.args_length > 0)
    debug_printf("received command: %s (%d)\n", received.args, received.command);

  char** argstart;

  get_command_args(received.args, argstart, MAX_CMD_ARGS);

  if      (received.command == COMMAND_SETTING_SETENV)
    setenv_handler(argstart);

  else if (received.command == COMMAND_SETTING_UNSETENV)
    unsetenv_handler(argstart);

  else if (received.command == COMMAND_EXEC)
    run_handler(argstart);

  else if (received.command == COMMAND_START)
    start_handler(argstart);

  else if (received.command == COMMAND_RED_STDOUT)
    stdout_handler(argstart);

  else if (received.command == COMMAND_RED_STDERR)
    stderr_handler(argstart);

  else if (received.command == COMMAND_END_WAITCHILD)
    exit_on_last_handler(argstart);

  else if (received.command == COMMAND_END_CLEANUP)
    cleanup_handler(argstart);

  else if (received.command == COMMAND_END_EXIT)
    exit_handler(argstart);

  else if (received.command == COMMAND_MOUNT)
    mount_handler(argstart);

  // This doesn't make overwhelmingly much sense, but it may be useful for
  // debugging purposes
  else if (received.command == COMMAND_ERROR)
    error_handler(argstart);

  else if (received.command == COMMAND_ALIVE)
    alive_handler(argstart);

  return 0;
}

// Duplicates the fds for stdin and stdout, maps them onto globally accesible
// fds and installs a connection_read_handler for them

void init_server_pipes(void)
{
  send_fd = dup(STDOUT_FILENO);
  if (send_fd < 0)
    fatal_perror("dup failed");
  //  close(STDOUT_FILENO);
  if (debug_level)
    debug_printf("to_client fd=%d\n", send_fd);
  recv_fd = dup(STDIN_FILENO);
  if (recv_fd < 0)
    fatal_perror("dup failed");
  //  close(STDIN_FILENO);
  add_read_fd(recv_fd, connection_read_handler);

  if (debug_level)
    debug_printf("Initialized callee connection_read_handler on fd=%d\n", recv_fd);

  if (debug_level)
    debug_printf("Initialized server pipes: %d  %d\n", recv_fd, send_fd);

  return;
}

void client_connection_exit_handler(void)
{
  rsh_pid = -1;
  debug_printf("connection to server died\n");
  should_exit = 0;
  return;
}

void connect_to_server(void)
{
  char *argv[10];
  char **p = argv;
  char *session_rsh, *session_server, *my_server;
  int to_fd, from_fd;
  char *ssh_debug = "-v";
  char *server_debug = "-d";
  char *opposite_host_prefix = "-o";

  extern char *server_host;
  extern char *server_prog;
  //  extern char *opposite_host;

  session_rsh = getenv("SESSION_RSH");
  if (!session_rsh)
    session_rsh = "rsh";

  session_server = server_prog;
  if (!session_server)
    session_server = getenv("SESSION_SERVER");
  if (!session_server)
    session_server = "univention-session";

  my_server = server_host;
  if (!my_server)
    my_server = getenv("SESSION_HOST");
  if (!my_server)
    fatal_error("no server\n");

  char opposite_hostname[128];
  if ( gethostname ( opposite_hostname, 128 ) == -1 )
    fatal_perror ( "could not determine my own host name\n" );

  *p++ = session_rsh;
  if (debug_level > 1)
    *p++ = ssh_debug;
  *p++ = my_server;
  *p++ = session_server;
  if (debug_level)
    *p++ = server_debug;
  *p++ = opposite_host_prefix;
  *p++ = opposite_hostname;
  *p++ = NULL;

  if (debug_level) {
    int i;
    debug_printf("starting connection to server: ");
    for (i = 0; argv[i]; i++)
      fprintf(stderr, "%s ", argv[i]);
    fprintf(stderr, "\n");
  }

  rsh_pid = start_piped(argv, &to_fd, &from_fd, client_connection_exit_handler);

  if (debug_level)
    debug_printf("Connection established to server with pid %i on fds %d/%d\n", rsh_pid, to_fd, from_fd);

  send_fd = to_fd;
  recv_fd = from_fd;
  add_read_fd(recv_fd, connection_read_handler);

  if (debug_level)
    debug_printf("Initialized client connection_read_handler on fd=%d\n", recv_fd);

  if (debug_level)
    debug_printf("pipes: to: %d from: %d\n", send_fd, recv_fd);
}
