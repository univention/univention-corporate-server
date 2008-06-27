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

  if ( setresgid ( rgid, rgid, 0 ) != 0 )
    fatal_perror ( "can't initialize group id" );
  if ( setresuid ( ruid, ruid, 0 ) != 0 )
    fatal_perror ( "can't initialize user id" );

  if ( debug_level )
    debug_printf ( "setting effective uid to %d and effective gid to %d\n",
		   geteuid(), getegid() );

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
