/*
 * Univention Policy
 *  C source of the univention policy library
 *
 * Copyright 2003-2019 Univention GmbH
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

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>
#include <pwd.h>
#include <krb5.h>

#include <univention/config.h>
#include <univention/krb5.h>
#include <univention/debug.h>

univention_krb5_parameters_t* univention_krb5_new(void)
{
	univention_krb5_parameters_t* kp;
	if ((kp = calloc(1, sizeof(univention_krb5_parameters_t))) == NULL)
		return NULL;
	return kp;
}

static krb5_error_code kerb_prompter(krb5_context ctx, void *data,
	       const char *name, const char *banner, int num_prompts,
	       krb5_prompt prompts[])
{
	if (num_prompts == 0)
		return 0;

	memset(prompts[0].reply->data, 0, prompts[0].reply->length);
	if (prompts[0].reply->length > 0) {
		if (data) {
			strncpy(prompts[0].reply->data, data, prompts[0].reply->length-1);
			prompts[0].reply->length = strlen(prompts[0].reply->data);
		} else {
			prompts[0].reply->length = 0;
		}
	}
	return 0;
}

int univention_krb5_init(univention_krb5_parameters_t *kp)
{
	krb5_error_code rv = -1;
	char *principal_name;

	if (kp->username == NULL) {
		struct passwd pwd, *result;
		char *buf;
		size_t bufsize;
		int s;

		bufsize = sysconf(_SC_GETPW_R_SIZE_MAX);
		if (bufsize == -1)
			bufsize = 16384;
		buf = malloc(bufsize);
		if (buf == NULL)
			goto err;
		s = getpwuid_r(getuid(), &pwd, buf, bufsize, &result);
		if (result != NULL)
			kp->username = strdup(pwd.pw_name);
		free(buf);
	}

	if (kp->realm == NULL)
		kp->realm = univention_config_get_string("kerberos/realm");

	if (kp->username == NULL || kp->realm == NULL)
		goto err;
	asprintf(&principal_name, "%s@%s", kp->username, kp->realm);
	if (principal_name == NULL)
		goto err;

	univention_debug(UV_DEBUG_KERBEROS, UV_DEBUG_INFO, "receiving Kerberos ticket for %s", principal_name);

	if ((rv = krb5_init_context(&kp->context)))
		goto err1;
	if ((rv = krb5_cc_default(kp->context, &kp->ccache)))
		goto err2;
	if ((rv = krb5_parse_name(kp->context, principal_name, &kp->principal)))
		goto err2;
	if ((rv = krb5_get_init_creds_password(kp->context, &kp->creds, kp->principal,
					NULL, kerb_prompter, kp->password, 0, NULL, NULL)))
		goto err3;
	if ((rv = krb5_cc_initialize(kp->context, kp->ccache, kp->principal)))
		goto err4;
	if ((rv = krb5_cc_store_cred(kp->context, kp->ccache, &kp->creds)))
		goto err5;

	rv = 0;

err5:
	krb5_cc_close(kp->context, kp->ccache);
	kp->ccache = NULL;
err4:
	krb5_free_cred_contents(kp->context, &kp->creds);
	kp->creds = NULL;
err3:
	krb5_free_principal(kp->context, kp->principal);
	kp->principal = NULL;
err2:
	krb5_free_context(kp->context);
	kp->context = NULL;
err1:
	free(principal_name);
err:
	return rv;
}
