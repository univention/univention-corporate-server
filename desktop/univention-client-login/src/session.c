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

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <limits.h>
#include <pwd.h>
#include <sys/types.h>
#include <sys/stat.h>

#include "debug.h"

char* session_directory = NULL;

void setup_session_directory( void )
{
  struct passwd* pwd;

  if ( (session_directory = malloc(PATH_MAX*sizeof(char))) == NULL )
    fatal_perror ( "malloc failed\n" );

  pwd = getpwuid( getuid() );
  if ( pwd == NULL )
    fatal_perror ( "Could not determine UID.\n" );

  snprintf ( session_directory, PATH_MAX, "%s/.univention-session",
	     pwd->pw_dir );
  mkdir ( session_directory, S_IRWXU );
}
