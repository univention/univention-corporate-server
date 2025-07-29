/*
 * Univention Directory Listener
 *  header information for notifier.c
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _NOTIFIER_H_
#define _NOTIFIER_H_

#include <stdbool.h>
#include <univention/ldap.h>

int notifier_listen(univention_ldap_parameters_t *lp, bool write_transaction_file, univention_ldap_parameters_t *lp_local);

#endif /* _NOTIFIER_H_ */
