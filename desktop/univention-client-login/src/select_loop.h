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

#ifndef _SELECT_LOOP_H_
#define _SELECT_LOOP_H_

typedef int (*timeout_handler)(int id);
typedef int (*filedes_handler)(int fd);

struct timer {
  struct timer* next;
  int id;
  long usec;
  long remaining; /* current remaining time to wait */
  timeout_handler handler;
};

struct filedes {
  struct filedes* next;
  int fd;
  filedes_handler handler;
  int to_remove;
};

int add_timer ( long usec, timeout_handler handler  );
int remove_timer ( int id );
int add_read_fd ( int fd, filedes_handler handler );
int remove_read_fd ( int fd );
void select_loop ( void );

#endif /* _SELECT_LOOP_H_ */
