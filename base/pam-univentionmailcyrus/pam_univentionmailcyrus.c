/*
 * PAM Univention Mail Cyrus
 *  PAM Module to change username from email@address.com to username
 *
 * Copyright (C) 2005, 2006 Univention GmbH
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

#include <syslog.h>
#include <stdarg.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <pwd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <dirent.h>
#include <signal.h>
#include <wait.h>
#include <security/pam_appl.h>

#define PAM_SM_AUTH

#include <security/pam_modules.h>
#include <security/_pam_macros.h>
#include <ldap.h>

static char ldap_host[BUFSIZ] = "localhost";
static char ldap_base[BUFSIZ];
static unsigned int ldap_port = 389;
static char fromattr[BUFSIZ];
static char toattr[BUFSIZ];

#define UNIVENTIONMAILCYRUS_QUIET 020

/* some syslogging */
static void _log_err(int err, const char *format, ...)
{
   va_list args;

   va_start(args, format);
   openlog("PAM-univentionmailcyrus", LOG_CONS|LOG_PID, LOG_AUTH);
   vsyslog(err, format, args);
   va_end(args);
   closelog();
}

static int _pam_parse(int flags, int argc, const char **argv)
{
   int ctrl = 0;

   /* does the appliction require quiet? */
   if ((flags & PAM_SILENT) == PAM_SILENT)
      ctrl |= UNIVENTIONMAILCYRUS_QUIET;

   /* reset global variables to their default values */
   /* step through arguments */
   for (; argc-- > 0; ++argv)
   {
      if (!strcmp(*argv, "silent")) {
	 ctrl |= UNIVENTIONMAILCYRUS_QUIET;
      } else if (!strncmp(*argv,"ldap_host=",10))
	strncpy(ldap_host,*argv+10,BUFSIZ);
      else if (!strncmp(*argv,"ldap_port=",10))
	ldap_port=atoi(*argv+10);
      else if (!strncmp(*argv,"ldap_base=",10))
	strncpy(ldap_base,*argv+10,BUFSIZ);
      else if (!strncmp(*argv,"from_attr=",10))
	strncpy(fromattr,*argv+10,BUFSIZ);
      else if (!strncmp(*argv,"to_attr=",8))
	strncpy(toattr,*argv+8,BUFSIZ);
      else {
	 _log_err(LOG_ERR, "unknown option; %s", *argv);
      }
   }

   return ctrl;
}

int mapuser(const char *fromuser, char *touser)
{
   LDAP *ld;
   int msgid;
   char filter[BUFSIZ];
   char *attrs[] = {toattr, NULL};
   LDAPMessage *res = NULL, *entry;
   char **values = NULL;
   int ret = PAM_SUCCESS;

   snprintf(filter, BUFSIZ, "(&(%s=%s)(%s=*))", fromattr, fromuser, toattr);

   if ((ld = ldap_init(ldap_host, ldap_port)) == NULL) {
       _log_err(LOG_NOTICE, "Failed to connect to LDAP server %s:%d", ldap_host, ldap_port);
       ret = PAM_USER_UNKNOWN;
	   goto cleanup;
   }
   if ((msgid = ldap_search_s(ld, ldap_base, LDAP_SCOPE_SUBTREE, filter, attrs, 0, &res)) != LDAP_SUCCESS) {
       _log_err(LOG_NOTICE, "Failed to query LDAP server: ", filter);
       ret = PAM_USER_UNKNOWN;
	   goto cleanup;
   }
   if (ldap_count_entries(ld, res) != 1) {
       _log_err(LOG_NOTICE, "No or ambigous result, found %d entries.", ldap_count_entries(ld, res));
       ret = PAM_USER_UNKNOWN;
	   goto cleanup;
   }
   if ((entry = ldap_first_entry(ld, res)) == NULL) {
       _log_err(LOG_NOTICE, "LDAP search returned no entries.");
       ret = PAM_USER_UNKNOWN;
	   goto cleanup;
   }
   if ((values = ldap_get_values(ld, entry, toattr)) == NULL) {
       _log_err(LOG_NOTICE, "LDAP search returned no values: %s", filter);
       ret = PAM_USER_UNKNOWN;
	   goto cleanup;
   }
   if (ldap_count_values(values) != 1) {
       _log_err(LOG_NOTICE, "No or ambigous result, found %d values.", ldap_count_values(values));
       ret = PAM_USER_UNKNOWN;
	   goto cleanup;
   }
   strncpy(touser, values[0], BUFSIZ);

cleanup:
   if ( values ) ldap_value_free(values);
   if ( res ) ldap_msgfree(res);
   ldap_unbind(ld);
   return ret;
}

PAM_EXTERN
int pam_sm_authenticate(pam_handle_t *pamh, int flags,
			int argc, const char **argv)
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
   if (mapuser(auth_user, user) != PAM_SUCCESS) {
       _log_err(LOG_NOTICE, "failed to map username");
       return PAM_USER_UNKNOWN;
   }

   retval = pam_set_item(pamh, PAM_USER, user);
   if (retval != PAM_SUCCESS) {
      _log_err(LOG_NOTICE, "could not set new username");
      return PAM_USER_UNKNOWN;
   }
   _log_err(LOG_NOTICE, "continuing as user %s", user);

   return PAM_SUCCESS;
}

/* Ignore */
int pam_sm_setcred(pam_handle_t *pamh, int flags, int
		     argc, const char **argv)
{
   return PAM_IGNORE;
}

#ifdef PAM_STATIC

/* static module data */
struct pam_module _pam_univentionmail_modstruct =
{
   "pam_univentionmail",
   pam_sm_authenticate,
   pam_sm_setcred,
   NULL,
   NULL,
   NULL,
   NULL,
   NULL,
};

#endif
