/*
 * Univention Client Login
 *  this file is part of the Univention thin client tools
 *
 * Copyright 2004-2010 Univention GmbH
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
