/*
 * Univention Directory Notifier
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef __NOTIFY_H__
# define __NOTIFY_H__

#include <signal.h>
#include <stdio.h>

/* incoming transaction file, from slapo-translog or UDL running on Backup Directory Node with option "-o" */
#define FILE_NAME_LISTENER "/var/lib/univention-ldap/listener/listener"
/* private work queue transaction file */
#define FILE_NAME_NOTIFIER_PRIV "/var/lib/univention-ldap/listener/listener.priv"
/* transaction file, for notifier action */
#define FILE_NAME_TF "/var/lib/univention-ldap/notify/transaction"
#define FILE_NAME_TF_IDX "/var/lib/univention-ldap/notify/transaction.index"

typedef struct {
	unsigned long id;
} NotifyId_t;

typedef struct notify_entry {
	NotifyId_t notify_id;			/* cookie for this entry */
	char *dn;						/* the dn */
	char command;					/* (m)odify, (d)elete, (a)dd */
} NotifyEntry_t;

typedef struct {
	FILE *tf;						/* transaction file, for notifier action */
	FILE *l_tf;
} Notify_t;

void notify_init ( Notify_t *notify );
int  notify_transaction_get_last_notify_id ( Notify_t *notify, NotifyId_t *notify_id );
char* notify_transcation_get_one_dn ( unsigned long last_known_id );

void notify_schema_change_callback(int sig, siginfo_t *si, void *data);
void notify_listener_change_callback(int sig, siginfo_t *si, void *data);

#endif
