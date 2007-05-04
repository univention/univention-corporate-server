/*
 * Univention Baseconfig
 *  C library for univention baseconfig
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

#include <univention/config.h>
#include <univention/debug.h>

#include <errno.h>

#define BASECONFIG_FILE     "/etc/univention/base.conf"
#define BASECONFIG_MAX_LINE 256


char* univention_config_get_string ( char *value )
{
	FILE *file;
	char line[BASECONFIG_MAX_LINE];

	if( (file=fopen(BASECONFIG_FILE,"r")) == NULL )
	{
		univention_debug(UV_DEBUG_CONFIG,UV_DEBUG_ERROR,"Error on opening \"%s\n",BASECONFIG_FILE);
		return NULL;
	}

	while( fgets(line, BASECONFIG_MAX_LINE, file) != NULL )
	{
		if( !strncmp(line, value, strlen(value) ) )
		{
			fclose (file);
			return (char*)strndup(&(line[strlen(value)+2]), strlen(line) - (strlen(value)+2) - 1 );
																								/* no newline */
		}
	}

	fclose (file);

    univention_debug(UV_DEBUG_USERS, UV_DEBUG_INFO,"Did not find \"%s\"\n",value);

	return NULL;
}

int univention_config_get_int(char *value)
{
	FILE *file;
	char line[BASECONFIG_MAX_LINE];
	char *s_var;
	int var;

	if( (file=fopen(BASECONFIG_FILE,"r")) == NULL )
	{
		univention_debug(UV_DEBUG_USERS,UV_DEBUG_ERROR,"Error on opening \"%s\n",BASECONFIG_FILE);
		return -1;
	}

	while( fgets(line, BASECONFIG_MAX_LINE, file) != NULL )
	{
		if( !strncmp(line, value, strlen(value) ) )
		{
			fclose (file);
			s_var=(char*)strndup(&(line[strlen(value)+2]), strlen(line) - (strlen(value)+2) - 1 );
			return atoi(s_var);
		}
	}

	fclose (file);

    univention_debug(UV_DEBUG_USERS, UV_DEBUG_INFO,"Did not find \"%s\"\n",value);

	return -1;
}

long univention_config_get_long(char *value)
{
	FILE *file;
	char line[BASECONFIG_MAX_LINE];
	char *s_var;
	long var;

	if( (file=fopen(BASECONFIG_FILE,"r")) == NULL )
	{
		univention_debug(UV_DEBUG_USERS,UV_DEBUG_ERROR,"Error on opening \"%s\n",BASECONFIG_FILE);
		return -1;
	}

	while( fgets(line, BASECONFIG_MAX_LINE, file) != NULL )
	{
		if( !strncmp(line, value, strlen(value) ) )
		{
			fclose (file);
			s_var=(char*)strndup(&(line[strlen(value)+2]), strlen(line) - (strlen(value)+2) - 1 );
			return atol(s_var);
		}
	}

	fclose (file);

    univention_debug(UV_DEBUG_USERS, UV_DEBUG_INFO,"Did not find \"%s\"\n",value);

	return -1;
}

int univention_config_set_string(char *key, char *value)
{
	char *str;
	int pid, status;

	
	str=malloc((strlen(key)+strlen(value)+2) * sizeof(char));
	strcpy(str, key);
	strcat(str, "=");
	strcat(str,value);

	pid = fork();
	if (pid == -1)
		return -1;
	if (pid == 0) {
		char *argv[5];
		argv[0] = "sh";
		argv[1] = "-c";
		argv[2] = "univention-baseconfig";
		argv[2] = "set";
		argv[3] = str;
		argv[4] = 0;
		execve("/bin/sh", argv, NULL);
		exit(127);
	}
	do {
		if (waitpid(pid, &status, 0) == -1) {
			if (errno != EINTR)
				return -1;
		} else
			return status;
	} while(1);

	return 0;
}

