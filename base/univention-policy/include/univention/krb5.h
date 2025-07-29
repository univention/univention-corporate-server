/*
 * Univention Policy
 *  C source of the univention policy library
 *
 * SPDX-FileCopyrightText: 2003-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef __UNIVENTION_KRB5_H__
#define __UNIVENTION_KRB5_H__

#include <krb5.h>

typedef struct univention_krb5_parameters_s {
	char *username;
	char *realm;
	char *password;

	krb5_context context;
	krb5_ccache ccache;
	krb5_principal principal;
	krb5_creds creds;
} univention_krb5_parameters_t;

univention_krb5_parameters_t* univention_krb5_new(void);
int univention_krb5_init(univention_krb5_parameters_t *kp);

#endif
