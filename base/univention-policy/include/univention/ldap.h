/*
 * Univention Policy
 *  C source of the univnetion policy libary
 *
 * Copyright (C) 2003, 2004, 2005, 2006 Univention GmbH
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
