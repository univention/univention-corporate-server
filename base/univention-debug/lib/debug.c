/*
 * Univention Debug
 *  debug.c
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

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

#define _DEBUG_ARRAY_
#include <univention/debug.h>

#define UV_DEBUG_DEFAULT        UV_DEBUG_WARN

int  *univention_debug_level;
char *univention_debug_filename = NULL;
FILE *univention_debug_file = NULL;
char univention_debug_flush;
char univention_debug_function;

static char debug_init = 0;

const char *univention_debug_id_text[]={
	"MAIN       ",
	"LDAP       ",
	"USERS      ",
	"NETWORK    ",
	"SSL        ",
	"SLAPD      ",
	"SEARCH     ",
	"TRANSFILE  ",
	"LISTENER   ",
	"POLICY     ",
	"ADMIN      ",
	"CONFIG     ",
	"LICENSE    ",
	"KERBEROS   "
};

const char *univention_debug_level_text[]={
	"( ERROR   ) : ",
	"( WARN    ) : ",
	"( PROCESS ) : ",
	"( INFO    ) : ",
	"( ALL     ) : "
};

void univention_debug_init( char *logfile, char flush, char function )
{
	int i;
	time_t t;
	struct tm *tm;

	if ( debug_init == 1 ) {
		return;
	}

	debug_init = 1;
	
	univention_debug_level = malloc (DEBUG_MODUL_COUNT * sizeof(int));
	for( i=0; i<DEBUG_MODUL_COUNT; i++)
	{
		univention_debug_level[i] = UV_DEBUG_DEFAULT;
	}

    if ( !strcmp(logfile,"stderr" ) )  univention_debug_file = stderr;
    else if ( !strcmp(logfile,"stdout" ) )  univention_debug_file = stdout;
	else if ( logfile != NULL ) {
		if( (univention_debug_file = fopen(logfile, "a+"))  == NULL ) {
			fprintf(stderr,"Could not open logfile \"%s\"\n", univention_debug_filename);
			return 1;
		}
	}

	if ( flush == UV_DEBUG_FLUSH) univention_debug_flush = UV_DEBUG_FLUSH;
	else univention_debug_flush = UV_DEBUG_NO_FLUSH;

	if ( function == UV_DEBUG_FUNCTION) univention_debug_function = UV_DEBUG_FUNCTION;
	else univention_debug_function = UV_DEBUG_NO_FUNCTION;

	t=time(NULL);
	tm=localtime(&t);

	fprintf(univention_debug_file,"%02d.%02d.%02d %02d:%02d:%02d  DEBUG_INIT\n",tm->tm_mday, tm->tm_mon+1, tm->tm_year-100, tm->tm_hour,tm->tm_min, tm->tm_sec );
	fflush(univention_debug_file);
}

void univention_debug_reopen( void )
{
	if ( univention_debug_file == stderr || univention_debug_file == stdout)
		return;
	if ( univention_debug_file != NULL )
		fclose(univention_debug_file);
	
	if ( strcmp(univention_debug_filename, "stderr" ) == 0 )
		univention_debug_file = stderr;
	else if ( strcmp(univention_debug_filename ,"stdout" ) == 0 )
		univention_debug_file = stdout;
	else if ( univention_debug_filename != NULL ) {
		if( (univention_debug_file = fopen(univention_debug_filename, "a+"))  == NULL ) {
			fprintf(stderr,"Could not open logfile \"%s\"\n", univention_debug_filename);
			return 1;
		}
	}
}

void univention_debug_exit ( void )
{
	time_t t;
	struct tm *tm;

	if ( debug_init == 0 ) {
		return;
	}
	debug_init = 0;
	
	t=time(NULL);
	tm=localtime(&t);

	fprintf(univention_debug_file,"%02d.%02d.%02d %02d:%02d:%02d  DEBUG_EXIT\n",tm->tm_mday, tm->tm_mon+1, tm->tm_year-100, tm->tm_hour,tm->tm_min, tm->tm_sec );
	fflush(univention_debug_file);
	fclose(univention_debug_file);
	univention_debug_file = NULL;
}

void univention_debug_set_level ( int id, int level )
{
	univention_debug_level[id] = level;
}

void univention_debug_set_function ( char function )
{
	univention_debug_function = function;
}

