/*
 * Univention Directory Listener
 *  header information for select_server.c
 *
 * SPDX-FileCopyrightText: 2004-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _SELECT_SERVER_H_
#define _SELECT_SERVER_H_

#include <univention/ldap.h>

struct server_list {
	char *server_name;
};

void select_server(univention_ldap_parameters_t *lp);

#endif
