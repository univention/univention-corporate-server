/*
 * Univention Policy
 *  C source of the univnetion policy libary
 *
 * Copyright (C) 2003-2009 Univention GmbH
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
	if ((kp=malloc(sizeof(univention_krb5_parameters_t))) == NULL)
		return NULL;
	kp->username=NULL;
	kp->realm=NULL;
	kp->password=NULL;
	return kp;
}

static krb5_error_code kerb_prompter(krb5_context ctx, void *data,
	       const char *name, const char *banner, int num_prompts,
	       krb5_prompt prompts[])
{
	if (num_prompts == 0) return 0;

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
	krb5_error_code rv;
	char *principal_name;

	if (kp->username == NULL) {
		struct passwd *pwd;
		pwd = getpwuid(getuid());
		if (pwd == NULL) {
			return 1;
		}
		kp->username=strdup(pwd->pw_name);
	}
	if (kp->realm == NULL) {
		kp->realm=univention_config_get_string("kerberos/realm");
		if (kp->realm == NULL) {
			return 1;
		}
	}
	asprintf(&principal_name, "%s@%s", kp->username, kp->realm);

	univention_debug(UV_DEBUG_KERBEROS, UV_DEBUG_INFO, "receiving Kerberos ticket for %s", principal_name);

	if ((rv = krb5_init_context(&kp->context))) {
		free(principal_name);
		return rv;
	}
	if ((rv = krb5_cc_default(kp->context, &kp->ccache))) {
		free(principal_name);
		krb5_free_context(kp->context);
		return rv;
	}
	if ((rv = krb5_parse_name(kp->context, principal_name, &kp->principal))) {
		free(principal_name);
		krb5_free_context(kp->context);
		return rv;
	}
	if ((rv = krb5_get_init_creds_password(kp->context, &kp->creds, kp->principal,
					NULL, kerb_prompter, kp->password, 0, NULL, NULL))) {
		free(principal_name);
		krb5_free_principal(kp->context, kp->principal);
		krb5_free_context(kp->context);
		return rv;
	}
	if ((rv = krb5_cc_initialize(kp->context, kp->ccache, kp->principal))) {
		free(principal_name);
		krb5_free_cred_contents(kp->context, &kp->creds);
		krb5_free_principal(kp->context, kp->principal);
		krb5_free_context(kp->context);
		return rv;
	}
	if ((rv = krb5_cc_store_cred(kp->context, kp->ccache, &kp->creds))) {
		free(principal_name);
		krb5_cc_close(kp->context, kp->ccache);
		krb5_free_cred_contents(kp->context, &kp->creds);
		krb5_free_principal(kp->context, kp->principal);
		krb5_free_context(kp->context);
		return rv;
	}

	free(principal_name);
	krb5_cc_close(kp->context, kp->ccache);
	krb5_free_cred_contents(kp->context, &kp->creds);
	krb5_free_principal(kp->context, kp->principal);
	krb5_free_context(kp->context);
	return 0;
}
