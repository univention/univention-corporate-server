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

#include <signal.h>
#include <unistd.h>
#include <stdlib.h>

#include "debug.h"
#include "pipe.h"
#include "protocol.h"
#include "alive.h"
#include "command.h"
#include "select_loop.h"

/* client */

int client_alive_send(int id)
{
  struct message msg;

  if (debug_level)
    debug_printf("sending keep-alive\n");

  msg.command=COMMAND_ALIVE;
  msg.args_length=0;
  msg.data_length=0;

  protocol_send_message(&msg);
  return 0;
}

void client_keep_alive_init(void)
{
  add_timer(500000, client_alive_send);
}


/* server */
int client_alive = 0;

int command_handler_alive(int args_length, void* args, int data_length, void* data)
{
  client_alive = 1;
  return 0;
}

int server_alive_check(int id)
{
  if (client_alive == 0)
    fatal_error("client seems to be dead, aborting\n");
  client_alive = 0;
  return 0;
}

void server_keep_alive_init(void)
{
  add_timer(30000000, server_alive_check);
}
