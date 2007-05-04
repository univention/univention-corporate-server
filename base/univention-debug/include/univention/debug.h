/*
 * Univention Debug
 *  debug.h
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
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

#ifndef __DEBUG_H__
#define __DEBUG_H__
#include <stdio.h>
#include <time.h>
#include <syslog.h>


#define UV_DEBUG_ERROR     0
#define UV_DEBUG_WARN      1
#define UV_DEBUG_PROCESS   2
#define UV_DEBUG_INFO      3
#define UV_DEBUG_ALL       4


#define UV_DEBUG_MAIN           0x00
#define UV_DEBUG_LDAP           0x01
#define UV_DEBUG_USERS          0x02
#define UV_DEBUG_NETWORK        0x03
#define UV_DEBUG_SSL            0x04
#define UV_DEBUG_SLAPD          0x05
#define UV_DEBUG_SEARCH         0x06
#define UV_DEBUG_TRANSFILE      0x07
#define UV_DEBUG_LISTENER       0x08
#define UV_DEBUG_POLICY         0x09
#define UV_DEBUG_ADMIN          0x0A
#define UV_DEBUG_CONFIG         0x0B
#define UV_DEBUG_LICENSE		0x0C
#define UV_DEBUG_KERBEROS		0x0D
#define UV_DEBUG_DHCP			0x0E

#define DEBUG_MODUL_COUNT       0x0F

#define UV_DEBUG_NO_FLUSH       0x00
#define UV_DEBUG_FLUSH          0x01

#define UV_DEBUG_NO_FUNCTION       0x00
#define UV_DEBUG_FUNCTION          0x01


#ifndef _DEBUG_ARRAY_

extern int        *univention_debug_level;
extern FILE       *univention_debug_file;
extern char       univention_debug_function;
extern const char *univention_debug_id_text[];
extern const char *univention_debug_level_text[];

extern char univention_debug_flush;

#endif

#define univention_debug(id, level, args...)				\
  if( univention_debug_file && level <= univention_debug_level[id] )	\
  {									\
    time_t    t   = time(NULL);						\
    struct tm *tm = localtime(&t);					\
    fprintf( univention_debug_file,					\
             "%02d.%02d.%02d %02d:%02d:%02d  %s %s",			\
             tm->tm_mday, tm->tm_mon+1, tm->tm_year-100,		\
             tm->tm_hour,tm->tm_min, tm->tm_sec,			\
             univention_debug_id_text[id],				\
             univention_debug_level_text[level]);			\
    fprintf( univention_debug_file,  ##args);				\
    fprintf( univention_debug_file, "\n");				\
    if( level == UV_DEBUG_ERROR )					\
    {									\
      syslog( LOG_ERR, ##args);						\
    }									\
    if( univention_debug_flush == UV_DEBUG_FLUSH )			\
    {									\
      fflush( univention_debug_file );					\
    }									\
  }

#define univention_debug_begin(s)					\
  if( univention_debug_file && univention_debug_function == UV_DEBUG_FUNCTION )\
  {									\
    fprintf( univention_debug_file, "UNIVENTION_DEBUG_BEGIN  : %s\n",s);\
    if( univention_debug_flush == UV_DEBUG_FLUSH )			\
      fflush(univention_debug_file);					\
  }

#define univention_debug_end(s)						\
  if( univention_debug_file && univention_debug_function == UV_DEBUG_FUNCTION )\
  {									\
    fprintf( univention_debug_file, "UNIVENTION_DEBUG_END    : %s\n",s);\
    if( univention_debug_flush == UV_DEBUG_FLUSH )			\
      fflush(univention_debug_file);					\
  }

void univention_debug_set_level ( int id, int level );
void univention_debug_set_function ( char function );
void univention_debug_init      ( char *logfile, char flush , char function);
void univention_debug_reopen	( void );
void univention_debug_exit	( void );


#endif
