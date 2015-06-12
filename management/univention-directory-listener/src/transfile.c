/*
 * Univention Directory Listener
 *  transfile.c
 *
 * Copyright 2004-2015 Univention GmbH
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
#include <unistd.h>
#include <limits.h>
#include <sys/types.h>
#include <sys/stat.h>

#include <univention/debug.h>

#include "common.h"
#include "transfile.h"

char *transaction_file = "/var/lib/univention-ldap/listener/listener";
static const char *failed_ldif_file = "/var/lib/univention-directory-replication/failed.ldif";
extern long long listener_lock_count;


/* Open file exclusively. */
static FILE* fopen_lock(const char *name, const char *type, FILE **l_file)
{
	char buf[PATH_MAX];
	FILE *file;
	int count = 0;
	int l_fd;

	snprintf( buf, sizeof(buf), "%s.lock", name );

	if ((*l_file = fopen(buf, "a")) == NULL) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "Could not open lock file [%s]\n", buf);
		return NULL;
	}

	l_fd = fileno(*l_file);
	for (;;) {
		int rc = lockf(l_fd, F_TLOCK, 0);
		if (!rc)
			break;
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "Could not get lock for file [%s]; count=%d\n", buf, count);
		count++;
		if (count > listener_lock_count) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Could not get lock for file [%s]; exit\n", buf);
			exit(0);
		}
		usleep(1000);
	}

	if ((file = fopen(name, type)) == NULL) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "Could not open file [%s]\n", name);

		lockf(l_fd, F_ULOCK, 0);
		fclose(*l_file);
		*l_file = NULL;
	}

	return file;
}


/* Close file and lock file. */
static int fclose_lock(FILE **file, FILE **l_file)
{
	if (*file != NULL) {
		fclose(*file);
		*file = NULL;
	}

	if (*l_file != NULL) {
		int l_fd = fileno(*l_file);
		int rc = lockf(l_fd, F_ULOCK, 0);
		if (rc)
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ALL, "unlockf(): %d", rc);
		fclose(*l_file);
		*l_file = NULL;
	}

	return 0;
}


/* Write entry to transaction file. */
int notifier_write_transaction_file(NotifierEntry entry)
{
	FILE *file, *l_file;
	int res = -1;

	struct stat stat_buf;

	/* Check for failed ldif, if exists don't write the transaction file,
	 * otherwise the notifier notifiies the other listeners and nothing changed
	 * in our local LDAP.
	 */
	if (stat(failed_ldif_file, &stat_buf) != 0) {
		if ((file = fopen_lock(transaction_file, "a+", &l_file)) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Could not open %s\n", transaction_file);
			return res;
		}

		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "write to transaction file dn=[%s], command=[%c]", entry.dn, entry.command);
		fprintf(file, "%ld %s %c\n", entry.id, entry.dn, entry.command);
		res = fclose_lock(&file, &l_file);
		if (res != 0)
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to write to transaction file %s: %d", transaction_file, res);
	} else {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Could not write to transaction file %s. Check for %s\n", transaction_file, failed_ldif_file);
	}

	return res;
}
