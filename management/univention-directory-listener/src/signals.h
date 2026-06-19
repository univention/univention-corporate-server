/*
 * Univention Directory Listener
 *  signal handling
 *
 * SPDX-FileCopyrightText: 2004-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _SIGNALS_H_
#define _SIGNALS_H_

#include <stdbool.h>
#include <univention/ldap.h>

void signals_block(void);
void signals_unblock(void);
void signals_init(void);

extern void exit_handler_cleanup(int sig, univention_ldap_parameters_t *lp, univention_ldap_parameters_t *lp_local) __attribute__((noreturn));
void exit_handler(int sig);
bool check_exit_signal(void);
int get_exit_signal(void);

#endif /* _SIGNALS_H_ */
