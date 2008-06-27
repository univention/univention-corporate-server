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

#include <stdio.h>
#include <assert.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

#include "channels.h"
#include "protocol.h"
#include "debug.h"
#include "select_loop.h"
#include "command.h"

// Store a mapping between a channel ID and an associated filedescriptor
struct channel {
	struct channel* next;
	int fd;
	int id;
};

struct channel* first_channel=NULL;

// Handler function which reads from the channel and sends
// data to the remote host
int channel_read_handler(int fd)
{
  struct message received;
  size_t len;
  int id;

  memset ( &received , 0, sizeof(struct message));
  protocol_recv_message (&received);

  id=channel_id_by_fd(fd);

  if (id < 0)
    fatal_error("unknown channel for file descriptor %d\n", fd);

  //  if (command_write(id, buffer, len) < 0)
  //    fatal_error("couldn't write to channel %d\n", id);

  return 0;
}

// Add a channel to the list of multiplexed channels
int channel_add(int fd, int id)
{
	struct channel* tmp;

	if ((tmp=malloc(sizeof(struct channel))) == NULL)
		fatal_perror("malloc failed");

	/* allocate new id, if not passed */
	if (id < 0) {
		struct channel* cur;
		int largest_id=-1;
		for (cur=first_channel; cur != NULL; cur=cur->next)
			if (cur->id > largest_id)
				largest_id=cur->id;
		id=largest_id+1;
	}

	tmp->fd=fd;
	tmp->next=first_channel;
 	first_channel=tmp;

	add_read_fd(fd, channel_read_handler);

	return id;
}

// Remove a channel from the list of multiplexed channels
void channel_remove(int id)
{
	struct channel *cur, *prev=NULL;

	for (cur=first_channel; cur != NULL; cur=cur->next) {
		if (cur->id == id)
			break;
		prev=cur;
	}

	/* cur points to channel that is to be removed if found, otherwise to NULL */
	if (cur == NULL)
		return;

	if (cur == first_channel) {
		first_channel=cur->next;
		free(cur);
	} else {
		assert(prev != NULL); /* otherwise cur == firstchannel */
		prev->next=cur->next;
		free(cur);
	}
}


// Returns the associated channel ID to a given filedescriptor
int channel_id_by_fd(int fd)
{
	struct channel* cur;

	for (cur=first_channel; cur != NULL; cur=cur->next) {
		if (cur->fd == fd)
			return cur->id;
	}
	return -1;
}

// Return the associated filedescriptor to a given channel ID
int channel_fd_by_id(int id)
{
	struct channel* cur;

	for (cur=first_channel; cur != NULL; cur=cur->next) {
		if (cur->id == id)
			return cur->fd;
	}
	return -1;
}
