/*
 * Univention Policy
 *  C source of the univention policy library
 *
 * SPDX-FileCopyrightText: 2003-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef __UNIVENTION_POLICY_H__
#define __UNIVENTION_POLICY_H__

#include <ldap.h>

typedef struct univention_policy_result_s {
	char* policy_dn;
	int count;
	char** values;
} univention_policy_result_t;

typedef struct univention_policy_handle_s univention_policy_handle_t;

univention_policy_handle_t* univention_policy_open(LDAP *ld, const char *base, const char *dn);
univention_policy_result_t* univention_policy_get(univention_policy_handle_t *handle, const char *policy_name, const char *attribute_name);
void univention_policy_close(univention_policy_handle_t* handle);

#endif
