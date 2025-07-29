/*
 * Univention Directory Listener
 *  header information for transfile.c
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _TRANSFILE_H_
#define _TRANSFILE_H_

#include <stdbool.h>
#include "network.h"

extern char *transaction_file;
bool notifier_has_failed_ldif(void);
int notifier_write_transaction_file(NotifierEntry entry);

#endif /* _TRANSFILE_H_ */
