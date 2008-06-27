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

#include "protocol.h"
#include "connection.h"
#include "unistd.h"
#include "stdlib.h"
#include "debug.h"
#include "pipe.h"
#include <string.h>


// send a protocol data unit over the current connection and wait for an
// ACK packet
int protocol_send_message_fd(int recv_fd, int send_fd, struct message* msg)
{
  struct raw_message_t raw_message;
  memset ( &raw_message, 0, sizeof(struct raw_message_t));

  raw_message.command=msg->command;
  raw_message.args_length=msg->args_length;
  raw_message.data_length=msg->data_length;

  if (debug_level)
    debug_printf("Msg-Length send_msg CAD %d  %d  %d\n", msg->command, msg->args_length, msg->data_length);

  write_to_pipe(send_fd, 0, &raw_message, sizeof(raw_message));

  if (msg->args_length > 0)
    write_buf_to_pipe(send_fd, 0, msg->args, msg->args_length);
  if (msg->data_length > 0)
    write_buf_to_pipe(send_fd, 0, msg->data, msg->data_length);

  int ack_received = protocol_recv_ack_fd(recv_fd, send_fd);

  if (ack_received == 0)
    debug_printf("Received ACK: yes\n");
  else
    debug_printf("Received ACK: no\n");

  if (ack_received != 0)
    return -1;

  return msg->command;
}

// read a protocol data unit from the current connection and send an ACK packet
// to the generous spender
int protocol_recv_message_fd(int recv_fd, int send_fd, struct message* message)
{
  struct raw_message_t raw_message;
  memset ( &raw_message, 0, sizeof(struct raw_message_t));

  read_cmd_from_pipe(recv_fd, 0, &raw_message, sizeof(struct raw_message_t));
  message->command     = raw_message.command;
  message->args_length = raw_message.args_length;
  message->data_length = raw_message.data_length;

  sleep(3);

  if (debug_level)
    debug_printf("Msg-Length recv_msg C %d A %d D %d FD %d\n", raw_message.command, raw_message.args_length, raw_message.data_length, recv_fd);

  if (raw_message.args_length > 0)
    {
      message->args = malloc(raw_message.args_length);
      //      memset ( message->args, 0, raw_message.args_length);

      read_data_from_pipe(recv_fd, 0, message->args, raw_message.args_length);
      debug_printf("ARGS %s \n", message->args);
    }
  else
    {
      message->args=NULL;
    }
  if (raw_message.data_length > 0)
    {
      message->data=malloc(raw_message.data_length);
      //      memset ( message->data, 0, raw_message.data_length);

      read_data_from_pipe(recv_fd, 0, message->data, raw_message.data_length);
    }
  else
    {
      message->data=NULL;
    }

  int ack_sent = protocol_send_ack_fd(recv_fd, send_fd);

  if (ack_sent == 0)
    debug_printf("ACK sent: yes\n");
  else
    debug_printf("ACK sent: no\n");

  if (ack_sent != 0)
    return -1;

  return message->command;
}

// send an ACK packet on the connection
// Returns 0 if everything was OK, otherwise -1
int protocol_send_ack_fd(int sendack_fd, int send_fd)
{
  struct raw_message_t message;
  memset ( &message, 0, sizeof(struct raw_message_t));

  message.command=COMMAND_ACK;
  message.args_length=0;
  message.data_length=0;

  //  FIXME, Retransmits einrichten
  if (write_to_pipe(sendack_fd, 0, &message, sizeof(message)) == -1)
    ; //   write_buf_to_pipe(send_fd, 0, message.data, message.data_length);

  //  if (protocol_recv_ack_fd(recv_fd, send_fd) != 0)
  //    return -1;

  return message.command;
}

// return whether an ACK packet has been sent on the connection
int protocol_recv_ack_fd(int recv_fd, int send_fd)
{
  struct raw_message_t msg;
  memset ( &msg, 0, sizeof(struct raw_message_t));

  read_cmd_from_pipe(recv_fd, 5, &msg, sizeof(msg));

  if (msg.command == COMMAND_ACK)
    return 0;
  else
    return -1;
}

// wrapper function to send a protocol data unit on the wire
int protocol_send_message(struct message* msg)
{
  debug_printf("command type %d\n", msg->command);
  return protocol_send_message_fd(recv_fd, send_fd, msg);
}

// wrapper function to read a protocol data unit from the wire
int protocol_recv_message(struct message* msg)
{
  return protocol_recv_message_fd(recv_fd, send_fd, msg);
}
