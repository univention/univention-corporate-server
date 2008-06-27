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

#ifndef _COMMAND_H_
#define _COMMAND_H_

#define MAX_CMD_LEN 2048
#define MAX_CMDID_LEN 16
#define MAX_CMD_ARGS 32

typedef int (*cmd_handler)(char ** argv );

struct command {
  int id;
  char * string;
  cmd_handler handler;
};

extern struct command COMMANDS[];

int get_command_id_by_id ( char ** buffer );
int get_command_id_by_name ( char ** buffer );
int get_command_args ( char * buffer, char ** argv, int max );
void send_command_by_name ( char * cmd, char ** argv );
void send_command_by_id ( int cmdid, char ** argv );
int execute_command ( char * buffer );
void call_cleanup_script ( void );

#endif /* _COMMAND_H_ */
