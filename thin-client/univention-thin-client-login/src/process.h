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

#ifndef _PROTOCOL_H_
#define _PROTOCOL_H_

typedef void (*exit_hdlr)(void);

struct Child_Process {
  int pid;
  int to_fd;
  int from_fd;
  exit_hdlr exit_handler;
  struct Child_Process * next;
};
typedef struct Child_Process child_process;

int start_piped ( char ** argv, int * to_fd, int * from_fd, void (* exit_handler)(void) );
int start_process ( char ** argv, void (* exit_handler)(void) );
int run_process ( char ** argv );
void kill_process ( int pid );
void kill_childs ( void );
int remove_process ( int pid );

#endif /* _PROTOCOL_H_ */
