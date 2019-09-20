/*
 * PAM Univention Samba Domain
 *  PAM Module to change username from Domain+username to username
 *
 * Copyright 2011-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */

#include <syslog.h>
#include <stdarg.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <pwd.h>
#include <stdlib.h>
#include <ctype.h>
#include <stdio.h>
#include <string.h>
#include <dirent.h>
#include <signal.h>
#include <wait.h>
#include <security/pam_appl.h>
#include <univention/config.h>

#define PAM_SM_AUTH

#include <security/pam_modules.h>
#include <security/_pam_macros.h>

static char *windows_domain;

#define UNIVENTIONSAMBADOMAIN_QUIET 020

/* some syslogging */
static void _log_err(int err, const char *format, ...)
{
	va_list args;

	va_start(args, format);
	openlog("PAM-univentionsambadomain", LOG_CONS|LOG_PID, LOG_AUTH);
	vsyslog(err, format, args);
	va_end(args);
	closelog();
}

static int _pam_parse(int flags, int argc, const char **argv)
{
	int ctrl = 0;

	windows_domain = univention_config_get_string("windows/domain");
	/* does the application require quiet? */
	if ((flags & PAM_SILENT) == PAM_SILENT)
		ctrl |= UNIVENTIONSAMBADOMAIN_QUIET;

	/* reset global variables to their default values */
	/* step through arguments */
	for (; argc-- > 0; ++argv)
	{
		if (!strcmp(*argv, "silent")) {
			ctrl |= UNIVENTIONSAMBADOMAIN_QUIET;
		} else if (!strncmp(*argv,"windows_domain=",15))
			strncpy(windows_domain,*argv+15,BUFSIZ);
		else {
			_log_err(LOG_ERR, "unknown option; %s", *argv);
		}
	}

	return ctrl;
}

inline int mapuser(const char *fromuser, char *touser)
{
	int mapped = 0;
	int len_windows_domain = strlen(windows_domain);

	if ( strlen(fromuser) > len_windows_domain ) {

		int i;
		for (i=0; i<len_windows_domain; i++) {
			if ( toupper(windows_domain[i]) != toupper(fromuser[i]) ) {
				break;
			}
		}
		if (i == len_windows_domain && ( fromuser[i] == '+' || fromuser[i] == '\\' ) ) {
			strncpy(touser, fromuser + len_windows_domain + 1, strlen(fromuser) - len_windows_domain );
			mapped = 1;
		}
	}

	return mapped;
}

inline int pam_map_user(pam_handle_t *pamh, int flags, int argc, const char **argv)
{
	int retval, ctrl;
	const char* auth_user;
	char user[BUFSIZ];

	/* Parse the flag values */
	ctrl = _pam_parse(flags, argc, argv);

	retval = pam_get_item(pamh, PAM_USER, (const void **) &auth_user);
	if (retval != PAM_SUCCESS || auth_user == NULL || *auth_user == '\0') {
		_log_err(LOG_NOTICE, "user unknown");
		return PAM_USER_UNKNOWN;
	}

	if (mapuser(auth_user, user)) {
		retval = pam_set_item(pamh, PAM_USER, user);

		if (retval != PAM_SUCCESS) {
			_log_err(LOG_NOTICE, "could not set new username");
			return PAM_USER_UNKNOWN;
		}
		_log_err(LOG_INFO, "continuing as user %s", user);
	}

	return PAM_SUCCESS;
}

PAM_EXTERN
int pam_sm_open_session(pam_handle_t *pamh, int flags, int argc, const char **argv)
{
	return pam_map_user(pamh, flags, argc, argv);
}

/* Ignore */
PAM_EXTERN
int pam_sm_close_session(pam_handle_t *pamh, int flags, int argc, const char **argv)
{
	return PAM_IGNORE;
}

#ifdef PAM_STATIC

/* static module data */
struct pam_module _pam_univentionsambadomain_modstruct =
{
	"pam_univentionsambadomain",
	NULL,
	NULL,
	NULL,
	pam_sm_open_session,
	pam_sm_close_session,
	NULL,
	NULL,
};

#endif
