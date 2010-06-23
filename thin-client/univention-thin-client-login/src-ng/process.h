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
int process_remove ( int pid );
void process_add ( child_process* child );
void process_killall ( void );
int process_exec(char **argv, char **envp, int *to_fd, int *from_fd, int *err_fd, void (*exit_handler) (void));

#endif /* _PROTOCOL_H_ */
