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

#include "command.h"
#include "channels.h"
#include "protocol.h"
#include "alive.h"
#include "bits/types.h"
#include "process.h"
#include "debug.h"

int exit_on_last = 0;

//int exit_on_last_handler(char **argv)
//{
//	exit_on_last = 1;
//	return 0;
//}

// Send arbitrary data to the communication endpoint
size_t command_write(int id, const void *buf, size_t count)
{
  struct message msg;

  msg.command=COMMAND_FD_DATA;
  msg.args=&id;
  msg.args_length=sizeof(id);
  msg.data=(void*)buf;
  msg.data_length=count;

  if (protocol_send_message(&msg) == 0)
    return count;
  else
    return -1;
}

// FIXME, eventueller Rueckgabewert
// Send the command, which executes a program on the comm endpoint
void command_exec(char** argv, char** envp)
{
  struct message msg;

  msg.command=COMMAND_EXEC;
  msg.args=argv;
  msg.args_length=sizeof(argv);
  msg.data=envp;
  msg.data_length=sizeof(envp);

  protocol_send_message(&msg);
}

void command_handler_ack(int args_length, void* args, int data_length, void* data)
{
	fatal_error("ack command outside of request received.");
}

// FIXME, define return-semantics
int command_handler_exec(int args_length, void* args, int data_length, void* data)
{
  //  	char* filename;
	char** argv;
	char** envp;

	int stdin_fd, stdout_fd, stderr_fd;
	int stdin_id, stdout_id, stderr_id;

	process_exec(argv, envp, &stdin_fd, &stdout_fd, &stderr_fd, 0);

	stdin_id=channel_add(stdin_fd, -1);
	stdout_id=channel_add(stdout_fd, -1);
	stderr_id=channel_add(stderr_fd, -1);
	return 0;
}

int command_handler_fd_data(int args_length, void* args, int data_length, void* data)
{
	int id;
	int fd;
	int len=0;

	if ((fd=channel_fd_by_id(id)) < 0) {
	  //		if (debug_level)
	  debug_printf("There is no file descriptor for channel %d!\n", id);
		return -1;
	}

	while (len < data_length) {
		int written;
		written=write(fd, (char*)data+len, data_length-len);
		if (written < 1)
			return -1;
		len+=written;
	}

	return 0;
}

/*
commands[]={
	{COMMAND_ACK,		command_handler_ack	},
	//	{COMMAND_ALIVE, 	command_handler_alive	},
	{COMMAND_EXEC,		command_handler_exec	},
	{COMMAND_FD_DATA,	command_handler_fd_data },
};
*/
