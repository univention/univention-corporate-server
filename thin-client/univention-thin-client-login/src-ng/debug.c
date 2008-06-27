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
