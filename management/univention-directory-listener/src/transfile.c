/*
 * Univention Directory Listener
 *  transfile.c
 *
 * Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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
#include <unistd.h>
#include <sys/types.h>
#include <sys/stat.h>

#include <univention/debug.h>

#include "common.h"
#include "transfile.h"

#define TRANSACTION_FILE "/var/lib/univention-ldap/listener/listener"
#define MAX_PATH_LEN 4096

static FILE* fopen_lock ( const char *name, const char *type, FILE **l_file )
{
	char buf[MAX_PATH_LEN];
	FILE *file;
	int count=0;
	int rc;

	snprintf( buf, sizeof(buf), "%s.lock", name );

	if ( (*l_file = fopen ( buf, type )) == NULL ) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "Could not open lock file [%s]\n", buf);
		return NULL;
	}

	while ( (rc=lockf( fileno(*l_file), F_TEST, 0 ) ) != 0 ) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "Could not get lock for file [%s]; count = %d\n", buf,count);
		count++;
		usleep(1000);
	}

	lockf( fileno(*l_file), F_LOCK, 0 );

	if ( (file = fopen( name, type ) ) == NULL ) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "Could not open file [%s]\n", name);

		lockf( fileno(*l_file), F_ULOCK, 0 );
		fclose(*l_file);
		l_file  = NULL;
	}

	return file;
}

static int fclose_lock ( FILE *file, FILE *l_file )
{
	int rc;
	if ( file != NULL ) {
		if ( file->_fileno != -1 ) {
			fclose ( file );
		}
	}
	file  = NULL;


	rc=lockf( fileno(l_file), F_ULOCK, 0 );
	if ( rc == 0 ) {
		if ( l_file != NULL ) {
			if ( l_file->_fileno != -1 ) {
				fclose(l_file);
			}
		}
	}
	l_file  = NULL;

	return 0;
}


int notifier_write_transaction_file(NotifierEntry entry)
{
	FILE *file, *l_file;
	int res;

	struct stat stat_buf;

	/* Check for failed ldif, if exists don't write the transaction file,
	 * otherwise the notifier notifiies the other listeners and nothing changed
	 * in our local LDAP.
	 */
	if( (stat("/var/lib/univention-ldap-replication/failed.ldif", &stat_buf)) != 0 ) {

		if ((file = fopen_lock(TRANSACTION_FILE, "a+", &l_file)) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Could not open %s\n",TRANSACTION_FILE);
		}

		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "write to transaction file dn=[%s], command=[%c]", entry.dn, entry.command);
		fprintf(file, "%ld %s %c\n", entry.id, entry.dn, entry.command);
		res = fclose_lock ( file, l_file );
	} else {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Could not write to transaction file %s. Check for /var/lib/univention-ldap-replication/failed.ldif\n",TRANSACTION_FILE);
		res = -1;
	}

	return res;
}

