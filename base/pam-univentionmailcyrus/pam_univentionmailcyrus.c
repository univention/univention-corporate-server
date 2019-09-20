/*
 * PAM Univention Mail Cyrus
 *  PAM Module to change username from email@address.com to username
 *
 * Copyright 2005-2019 Univention GmbH
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
#include <stdio.h>
#include <string.h>
#include <dirent.h>
#include <signal.h>
#include <wait.h>
#include <security/pam_appl.h>
#include <univention/ldap.h>

#define PAM_SM_AUTH

#include <security/pam_modules.h>
#include <security/_pam_macros.h>
#include <ldap.h>

static char ldap_host[BUFSIZ] = "localhost";
static char ldap_base[BUFSIZ];
static unsigned int ldap_port = 389;
static char fromattr[BUFSIZ];
static char toattr[BUFSIZ];
static char binddn[BUFSIZ];
static char pwfile[BUFSIZ] = "/etc/machine.secret";
static char bindpw[BUFSIZ];

#define UNIVENTIONMAILCYRUS_QUIET 020

/* some syslogging */
static void _log_err(int err, const char *format, ...)
    __attribute__ ((format (printf, 2, 3)));
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
   FILE *fp;
   int len;

   /* does the application require quiet? */
   if ((flags & PAM_SILENT) == PAM_SILENT)
      ctrl |= UNIVENTIONMAILCYRUS_QUIET;

   /* reset global variables to their default values */
   /* step through arguments */
   for (; argc-- > 0; ++argv)
   {
      if (!strcmp(*argv, "silent"))
          ctrl |= UNIVENTIONMAILCYRUS_QUIET;
      else if (!strncmp(*argv, "ldap_host=", 10))
          strncpy(ldap_host, *argv + 10, BUFSIZ);
      else if (!strncmp(*argv, "ldap_port=", 10))
          ldap_port=atoi(*argv + 10);
      else if (!strncmp(*argv, "ldap_base=", 10))
          strncpy(ldap_base, *argv + 10, BUFSIZ);
      else if (!strncmp(*argv, "from_attr=", 10))
          strncpy(fromattr, *argv + 10, BUFSIZ);
      else if (!strncmp(*argv, "to_attr=", 8))
          strncpy(toattr, *argv + 8, BUFSIZ);
      else if (!strncmp(*argv, "binddn=", 7))
          strncpy(binddn, *argv + 7, BUFSIZ);
      else if (!strncmp(*argv, "pwfile=", 7))
          strncpy(pwfile, *argv + 7, BUFSIZ);
      else
          _log_err(LOG_ERR, "unknown option: %s", *argv);
   }

   /* read password from file */
   if ((fp = fopen(pwfile, "r")) != NULL) {
     if (fgets(bindpw, BUFSIZ, fp) == NULL) {
       len = strlen(bindpw);
       if (bindpw[len-1] == '\n')
         bindpw[len-1] = '\0';
     }
     fclose(fp);
   }

   return ctrl;
}

static int mapuser(const char *fromuser, char *touser)
{
   int msgid;
   int scope = LDAP_SCOPE_SUBTREE;
   char filter[BUFSIZ];
   char *attrs[] = {toattr, NULL};
   int attrsonly = 0;
   LDAPControl **serverctrls = NULL;
   LDAPControl **clientctrls = NULL;
   struct timeval timeout = {.tv_sec=10, .tv_usec=0};
   int sizelimit = 0;
   LDAPMessage *res = NULL, *entry;
   struct berval **values = NULL;
   int ret = PAM_USER_UNKNOWN;
   univention_ldap_parameters_t *lp;
   char *host;
   char *saved;

   lp = univention_ldap_new();
   lp->port = ldap_port;
   lp->base = strdup(ldap_base);
   lp->binddn = strdup(binddn);
   lp->bindpw = strdup(bindpw);
   lp->start_tls++;

   snprintf(filter, BUFSIZ, "(&(%s=%s)(%s=*))", fromattr, fromuser, toattr);

   for(host=strtok_r(ldap_host, ",", &saved); host != NULL; host=strtok_r(NULL, ",", &saved)) {
      lp->host = strdup(host);
      if (univention_ldap_open(lp) != 0) {
         _log_err(LOG_NOTICE, "Failed to connect to LDAP server %s:%d", host, ldap_port);
         free(lp->host);
         continue;
      }
      break;
   }
   if(host == NULL) {
      _log_err(LOG_NOTICE, "Failed to connect to the configured LDAP servers");
      goto cleanup;
   }
   if ((msgid = ldap_search_ext_s(lp->ld, ldap_base, scope, filter, attrs,
                   attrsonly, serverctrls, clientctrls, &timeout, sizelimit, &res)) != LDAP_SUCCESS) {
       _log_err(LOG_NOTICE, "Failed to query LDAP server: %s", filter);
       goto cleanup;
   }
   if (ldap_count_entries(lp->ld, res) != 1) {
       _log_err(LOG_NOTICE, "No or ambiguous result, found %d entries.", ldap_count_entries(lp->ld, res));
       goto cleanup_msg;
   }
   if ((entry = ldap_first_entry(lp->ld, res)) == NULL) {
       _log_err(LOG_NOTICE, "LDAP search returned no entries.");
       goto cleanup_msg;
   }
   if ((values = ldap_get_values_len(lp->ld, entry, toattr)) == NULL) {
       _log_err(LOG_NOTICE, "LDAP search returned no values: %s", filter);
       goto cleanup_msg;
   }
   if (ldap_count_values_len(values) != 1) {
       _log_err(LOG_NOTICE, "No or ambiguous result, found %d values.", ldap_count_values_len(values));
       goto cleanup_values;
   }
   strncpy(touser, values[0]->bv_val, BUFSIZ);
   ret = PAM_SUCCESS;

cleanup_values:
   ldap_value_free_len(values);
cleanup_msg:
   ldap_msgfree(res);
cleanup:
   univention_ldap_close(lp);
   return ret;
}

PAM_EXTERN
int pam_sm_authenticate(pam_handle_t *pamh, int flags,
                        int argc, const char **argv)
{
   int retval;
   const char* auth_user;
   char user[BUFSIZ];

   /* Parse the flag values */
   _pam_parse(flags, argc, argv);

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
