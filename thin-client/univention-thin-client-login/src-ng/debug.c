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

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <stdarg.h>
#include <signal.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/select.h>
#include <unistd.h>
#include <wait.h>

#include "debug.h"

extern char * prog_name;

/* die on a fatal error */
void fatal_error( const char *err, ... )
{
  va_list args;

  va_start( args, err );
  fprintf( stderr, "%s: ", prog_name );
  vfprintf( stderr, err, args );
  va_end( args );
  exit(1);
}

void fatal_perror( const char *err, ... )
{
  va_list args;

  va_start( args, err );
  fprintf( stderr, "%s: ", prog_name );
  vfprintf( stderr, err, args );
  perror( " " );
  va_end( args );
  exit(1);
}

void debug_perror( const char *err, ... )
{
  va_list args;

  va_start( args, err );
  fprintf( stderr, "%s: ", prog_name );
  vfprintf( stderr, err, args );
  perror( " " );
  va_end( args );
}

void debug_printf( const char *err, ... )
{
  va_list args;

  va_start( args, err );
  fprintf( stderr, "%s: ", prog_name );
  vfprintf( stderr, err, args );
  va_end( args );
}
