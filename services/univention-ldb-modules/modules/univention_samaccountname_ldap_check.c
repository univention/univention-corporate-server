/* 
 * Samba LDB module univention_samaccountname_ldap_check
 *	LDB Module for checking samaccountname adds against external LDAP
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

/* univention_samaccountname_ldap_check was derived from the tests/sample_module

   Unix SMB/CIFS implementation.
   Samba utility functions
   Copyright (C) Jelmer Vernooij <jelmer@samba.org> 2007

     ** NOTE! The following LGPL license applies to the ldb
     ** library. This does NOT imply that all of Samba is released
     ** under the LGPL
   
   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public
   License as published by the Free Software Foundation; either
   version 3 of the License, or (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public
   License along with this library; if not, see <https://www.gnu.org/licenses/>.
*/

#include "ldb_module.h"
#include <univention/config.h>
#include <stdbool.h>
#include "base64.h"
#include <unistd.h>
#include <errno.h>
#include <string.h>
#include <sys/wait.h>
#include <util/data_blob.h>
#include <core/werror.h>

#include <util/time.h>
#include <samba/session.h>
#include <ctype.h>

// From dom_sid.h in S4
#define DOM_SID_STR_BUFLEN (15*11+25)
// From openldap/servers/slapd/slap.h
#define SLAP_LDAPDN_MAXLEN 8192

char *sid_to_string(const struct dom_sid *sid)
{
	char buf[DOM_SID_STR_BUFLEN];
	int ofs, i, buflen;
	uint32_t ia;

	ia = (sid->id_auth[5]) +
		(sid->id_auth[4] << 8 ) +
		(sid->id_auth[3] << 16) +
		(sid->id_auth[2] << 24);

	buflen = sizeof(buf);
	ofs = snprintf(buf, buflen, "S-%u-%lu",
			   (unsigned int)sid->sid_rev_num, (unsigned long)ia);

	for (i = 0; i < sid->num_auths; i++) {
		int s = buflen - ofs;
		if (s<0)
			s=0;
		ofs += snprintf(buf + ofs, s, "-%lu",
				(unsigned long)sid->sub_auths[i]);
	}

   return strdup(buf);
}

static char* read_pwd_from_file(char *filename)
{
	FILE *fp;
	char line[1024];
	int len;

	if ((fp = fopen(filename, "r")) == NULL)
		return NULL;
	if (fgets(line, 1024, fp) == NULL)
		return NULL;

	len = strlen(line);
	if (line[len-1] == '\n')
		line[len-1] = '\0';

	return strdup(line);
}

static int univention_samaccountname_ldap_check_add_callback(struct ldb_request *down_req,
			       struct ldb_reply *ares)
{
	struct ldb_request *req =
		talloc_get_type_abort(down_req->context,
		struct ldb_request);

	return ldb_module_done(req, ares->controls,
			       ares->response, ares->error);
}

static int univention_samaccountname_ldap_check_add(struct ldb_module *module, struct ldb_request *req)
{
	struct ldb_context *ldb;
	struct ldb_message *msg;
	struct ldb_message_element *attribute;
	struct ldb_request *down_req = NULL;
	bool is_computer = false;
	bool is_group = false;
	bool is_user = false;
	char *usersid;
	int i, fd[2], nbytes, ret;
	char target_dn_str[SLAP_LDAPDN_MAXLEN+1] = "";	// initialize with NULs

	/* check if there's a bypass_samaccountname_ldap_check control */
	struct ldb_control *control;
	control = ldb_request_get_control(req, LDB_CONTROL_BYPASS_SAMACCOUNTNAME_LDAP_CHECK_OID);
	if (control != NULL) {
		// ldb = ldb_module_get_ctx(module);
		// ldb_debug(ldb, LDB_DEBUG_TRACE, ("%s: plain ldb_add\n"), ldb_module_get_name(module));
		return ldb_next_request(module, req);
	}

	ldb = ldb_module_get_ctx(module);
	ldb_debug(ldb, LDB_DEBUG_TRACE, ("%s: ldb_add\n"), ldb_module_get_name(module));

	struct auth_session_info *session_info = (struct auth_session_info *)ldb_get_opaque(ldb, "sessionInfo");
	struct security_token *sec_token = (struct security_token *)session_info->security_token;
	struct dom_sid *d_sid = (struct dom_sid *)sec_token->sids;
	usersid = sid_to_string(d_sid);
	ldb_debug(ldb, LDB_DEBUG_TRACE, ("%s: sid: %s\n"), ldb_module_get_name(module), usersid);

	
	attribute = ldb_msg_find_element(req->op.add.message, "objectClass");
	for (i=0; i<attribute->num_values; i++) {
		if ( !(strcasecmp((const char *)attribute->values[i].data, "computer")) ) {
			is_computer = true;
		}
		if ( !(strcasecmp((const char *)attribute->values[i].data, "group")) ) {
			is_group = true;
		}
		if ( !(strcasecmp((const char *)attribute->values[i].data, "user")) ) {
			is_user = true;
		}
	}
			
	if ( is_computer ) {
		attribute = ldb_msg_find_element(req->op.add.message, "sAMAccountName");
		if( attribute == NULL ) {
			// we can't handle this
			return ldb_next_request(module, req);
		}
			
		char *opt_name = malloc(5 + attribute->values[0].length + 1);
		if (opt_name == NULL) {
			return ldb_module_oom(module);
		}
		sprintf(opt_name, "name=%s", attribute->values[0].data);
		opt_name[5 + attribute->values[0].length] = 0;

		char *opt_unicodePwd = NULL;
		attribute = ldb_msg_find_element(req->op.add.message, "unicodePwd");
		if( attribute != NULL ) {
			char *unicodePwd_base64;
			size_t unicodePwd_base64_strlen = BASE64_ENCODE_LEN(attribute->values[0].length);
			unicodePwd_base64 = malloc(unicodePwd_base64_strlen + 1);
			if (unicodePwd_base64 == NULL) {
				return ldb_module_oom(module);
			}
			base64_encode(attribute->values[0].data, attribute->values[0].length, unicodePwd_base64, unicodePwd_base64_strlen + 1);
			opt_unicodePwd = malloc(9 + unicodePwd_base64_strlen + 1);
			if (opt_unicodePwd == NULL) {
				return ldb_module_oom(module);
			}
			sprintf(opt_unicodePwd, "password=%s", unicodePwd_base64);
			opt_unicodePwd[9 + unicodePwd_base64_strlen] = 0;
			free(unicodePwd_base64);
		} else {
			ldb_debug(ldb, LDB_DEBUG_WARNING, ("%s: new computer object without initial unicodePwd\n"), ldb_module_get_name(module));
		}

		char *ldap_master = univention_config_get_string("ldap/master");
		char *machine_pass = read_pwd_from_file("/etc/machine.secret");
		if (machine_pass == NULL) {
			ldb_debug(ldb, LDB_DEBUG_ERROR, ("%s: Error reading /etc/machine.secret\n"), ldb_module_get_name(module));
			return LDB_ERR_OPERATIONS_ERROR;
		}

		char *my_hostname = univention_config_get_string("hostname");
		char *opt_my_samaccoutname = malloc(strlen(my_hostname) + 2);
		if (opt_my_samaccoutname == NULL) {
			return ldb_module_oom(module);
		}
		sprintf(opt_my_samaccoutname, "%s$", my_hostname);
		opt_my_samaccoutname[strlen(my_hostname)+1] = 0;
		char *opt_usersid = malloc(strlen(usersid) + strlen("usersid=") + 1);
		if (opt_usersid == NULL) {
			return ldb_module_oom(module);
		}
		sprintf(opt_usersid, "usersid=%s", usersid);
		free(my_hostname);

		int errno_wait = 0;
		sighandler_t sh;
		sh = signal(SIGCHLD, SIG_DFL);

		pipe(fd);

		int status;
		int pid=fork();
		if ( pid < 0 ) {

			ldb_debug(ldb, LDB_DEBUG_ERROR, ("%s: fork failed\n"), ldb_module_get_name(module));
			return LDB_ERR_UNWILLING_TO_PERFORM;

		} else if ( pid == 0 ) {
			close(fd[0]);   // close reading end
			dup2(fd[1], STDOUT_FILENO);

			ldb_debug(ldb, LDB_DEBUG_ERROR, ("%s: calling ucs-school-create_windows_computer\n"), ldb_module_get_name(module));
			if (opt_unicodePwd != NULL) {
				status = execl("/usr/sbin/ucs-school-create_windows_computer", "/usr/sbin/ucs-school-create_windows_computer", "-s", ldap_master, "-P", machine_pass, "-U", opt_my_samaccoutname, "selectiveudm/create_windows_computer", "-o", opt_name, "-o", opt_unicodePwd, "-o", "decode_password=yes", "-o", opt_usersid, NULL);
			} else {
				status = execl("/usr/sbin/ucs-school-create_windows_computer", "/usr/sbin/ucs-school-create_windows_computer", "-s", ldap_master, "-P", machine_pass, "-U", opt_my_samaccoutname, "selectiveudm/create_windows_computer", "-o", opt_name, "-o", opt_usersid, NULL);
			}
 
			if (status == -1) {     // otherwise es wouldn't be here
				ldb_debug(ldb, LDB_DEBUG_ERROR, ("%s: exec of /usr/sbin/ucs-school-create_windows_computer failed: %s\n"), ldb_module_get_name(module), strerror(errno));
			}

			_exit(status);
		} else {
			close(fd[1]);   // close writing end

			if ( waitpid(pid, &status, 0) == -1 ) {
				errno_wait = errno;
			}

			signal(SIGCHLD, sh);
		}

		free(ldap_master);
		free(machine_pass);
		free(opt_my_samaccoutname);
		free(opt_name);
		free(usersid);
		free(opt_usersid);
		if (opt_unicodePwd != NULL) {
			free(opt_unicodePwd);
		}

		if( ! WIFEXITED(status) ) {
			ldb_debug(ldb, LDB_DEBUG_ERROR, "%s: Cannot determine return status of ucs-school-create_windows_computer: %s (%d)\n", ldb_module_get_name(module), strerror(errno_wait), errno_wait);
			return LDB_ERR_UNWILLING_TO_PERFORM;
		} else if( WEXITSTATUS(status) == 2 ) {
			ldb_debug(ldb, LDB_DEBUG_ERROR, ("%s: ldb_add of machine object is disabled\n"), ldb_module_get_name(module));
			return LDB_ERR_UNWILLING_TO_PERFORM;
		} else if( WEXITSTATUS(status) == 3 ) {
			ldb_debug(ldb, LDB_DEBUG_TRACE, ("%s: ldb_add of machine object ignored in dummy mode\n"), ldb_module_get_name(module));
			return LDB_SUCCESS;
		} else if( WEXITSTATUS(status) == 4 ) {
			ldb_debug(ldb, LDB_DEBUG_ERROR, "%s: LDB_ERR_ENTRY_ALREADY_EXISTS\n", ldb_module_get_name(module));
			return LDB_ERR_ENTRY_ALREADY_EXISTS;
		} else if( WEXITSTATUS(status) ) {
			ldb_debug(ldb, LDB_DEBUG_ERROR, ("%s: unknown error code from ucs-school-create_windows_computer: %d\n"), ldb_module_get_name(module), WEXITSTATUS(status));
			return LDB_ERR_UNWILLING_TO_PERFORM;
		}

		nbytes = read(fd[0], target_dn_str, sizeof(target_dn_str)-1);
		close(fd[0]);   // close reading end

		ldb_debug(ldb, LDB_DEBUG_TRACE, ("%s: ucs-school-create_windows_computer returned: '%s' (%d bytes)\n"), ldb_module_get_name(module), target_dn_str, nbytes);

		if (nbytes == 0) {
			// The call succeeded but we didn't obtain a recommended location,
			// in this case we must continue without rewriting the DN.
			return ldb_next_request(module, req);
		}

		// Trim trailing space
  		char *end_ptr = target_dn_str + nbytes - 1;
  		while(end_ptr > target_dn_str && isspace((unsigned char)*end_ptr)) end_ptr--;
  		// Write new null terminator
  		*(end_ptr+1) = 0;

		// Now modify request DN
		msg = ldb_msg_copy_shallow(req, req->op.add.message);
		if (msg == NULL) {
			return ldb_module_oom(module);
		}

		msg->dn = ldb_dn_new(msg, ldb, target_dn_str);
		if (msg->dn == NULL) {
			return ldb_module_oom(module);
		}

		if (!ldb_dn_validate(msg->dn)) {
			return LDB_ERR_OPERATIONS_ERROR;
		}

		ret = ldb_build_add_req(&down_req, ldb, req,
				msg,
				req->controls,
				req, univention_samaccountname_ldap_check_add_callback,
				req);
		if (ret != LDB_SUCCESS) {
			return ret;
		}
	 
		return ldb_next_request(module, down_req);

	} else if ( is_user || is_group ) {
		ldb_debug(ldb, LDB_DEBUG_ERROR, ("%s: ldb_add of user and group object is disabled\n"), ldb_module_get_name(module));
		return LDB_ERR_UNWILLING_TO_PERFORM;
	}

	return ldb_next_request(module, req);
}

static int univention_samaccountname_ldap_check_init_context(struct ldb_module *module)
{
	struct ldb_context *ldb;

	int ret;
	ret = ldb_mod_register_control(module, LDB_CONTROL_BYPASS_SAMACCOUNTNAME_LDAP_CHECK_OID);
	if (ret != LDB_SUCCESS) {
		ldb = ldb_module_get_ctx(module);
		ldb_debug(ldb, LDB_DEBUG_TRACE,
			"%s: "
			"Unable to register %s control with rootdse.\n"
			"Errormessage: %s\n"
			"This seems to be ok, continuing..",
			LDB_CONTROL_BYPASS_SAMACCOUNTNAME_LDAP_CHECK_NAME,
			ldb_module_get_name(module),
			ldb_errstring(ldb));
	}

	return ldb_next_init(module);
}

static struct ldb_module_ops ldb_univention_samaccountname_ldap_check_module_ops = {
	.name	= "univention_samaccountname_ldap_check",
	.add	= univention_samaccountname_ldap_check_add,
	// .init_context	= univention_samaccountname_ldap_check_init_context,
};

int ldb_univention_samaccountname_ldap_check_init(const char *version)
{
	if (strcmp(version, LDB_VERSION) != 0) {
		fprintf(stderr, "ldb: WARNING: module version mismatch in %s : ldb_version=%s module_version=%s\n", __FILE__, version, LDB_VERSION);
	}
	return ldb_register_module(&ldb_univention_samaccountname_ldap_check_module_ops);
}
