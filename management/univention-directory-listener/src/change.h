/*
 * Univention Directory Listener
 *  header information for change.c
 *
 * SPDX-FileCopyrightText: 2004-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _CHANGE_H_
#define _CHANGE_H_

#include <ldap.h>
#include <univention/ldap.h>

#include "cache_entry.h"

int change_new_modules(univention_ldap_parameters_t *lp);
int change_update_schema(univention_ldap_parameters_t *lp);
int change_update_entry(univention_ldap_parameters_t *lp, NotifierID id, LDAPMessage *ldap_entry, char command);
extern int change_update_dn(struct transaction *);
extern void change_free_transaction_op(struct transaction_op *);

#endif /* _CHANGE_H_ */
