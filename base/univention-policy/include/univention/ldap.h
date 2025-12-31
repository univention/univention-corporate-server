/*
 * Univention Policy
 *  C source of the univention policy library
 *
 * SPDX-FileCopyrightText: 2003-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef __UNIVENTION_LDAP_H__
#define __UNIVENTION_LDAP_H__

#include <ldap.h>

typedef struct univention_ldap_parameters_s {
	LDAP *ld;
	int version;
	char *host;
	int port;
	char *uri;
	int start_tls;
	char *binddn;
	char *bindpw;
	char *base;
	int authmethod;
	char *sasl_mech;
	char *sasl_realm;
	char *sasl_authcid;
	char *sasl_authzid;
} univention_ldap_parameters_t;

univention_ldap_parameters_t* univention_ldap_new(void);
int univention_ldap_open(univention_ldap_parameters_t *lp);
void univention_ldap_close(univention_ldap_parameters_t *lp);
int univention_ldap_set_admin_connection( univention_ldap_parameters_t *lp );

#endif
