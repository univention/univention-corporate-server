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
