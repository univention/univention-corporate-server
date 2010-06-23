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

#include <sys/types.h>
#include <unistd.h>

#include "debug.h"


int setresuid(uid_t ruid, uid_t euid, uid_t suid);
int setresgid(gid_t rgid, gid_t egid, gid_t sgid);


uid_t ruid;
gid_t rgid;


void init_security ( void )
{
  ruid = getuid();
  rgid = getgid();

  if (ruid == 0) {
    if ( setresgid ( rgid, rgid, 0 ) != 0 )
      fatal_perror ( "can't initialize group id" );
    if ( setresuid ( ruid, ruid, 0 ) != 0 )
      fatal_perror ( "can't initialize user id" );

    if ( debug_level )
      debug_printf ( "setting effective uid to %d and effective gid to %d\n",
		     geteuid(), getegid() );
  }
  return;
}


void become_root ( void ) {

  if ( setresgid ( 0, 0, 0 ) != 0 ) fatal_perror ( "can't set gid" );
  if ( setresuid ( 0, 0, 0 ) != 0 ) fatal_perror ( "can't set uid" );

  if ( debug_level )
    debug_printf ( "setting effective uid to %d and effective gid to %d\n",
		   geteuid(), getegid() );
  return;
}


void unbecome_root ( void ) {

  if ( setresgid ( rgid, rgid, 0 ) != 0 ) fatal_perror ( "can't set group id\n" );
  if ( setresuid ( ruid, ruid, 0 ) != 0 ) fatal_perror ( "can't set user id\n" );

  if ( debug_level )
    debug_printf ( "setting effective uid to %d and effective gid to %d\n",
		   geteuid(), getegid() );
  return;

}
