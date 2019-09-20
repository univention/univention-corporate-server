/*
 * Univention Directory Notifier
 *
 * Copyright 2004-2019 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */

#ifndef __NOTIFY_H__
# define __NOTIFY_H__

#include <signal.h>
#include <stdio.h>

/* incoming transaction file, from lsitener */
#define FILE_NAME_LISTENER "/var/lib/univention-ldap/listener/listener"
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
	struct notify_entry *next;		/* next entry */

} NotifyEntry_t;

typedef struct {
	FILE *tf;						/* transaction file, for notifier action */
	FILE *l_tf;
} Notify_t;


void notify_init ( Notify_t *notify );
int  notify_transaction_get_last_notify_id ( Notify_t *notify, NotifyId_t *notify_id );
char* notify_transcation_get_one_dn ( unsigned long last_known_id );

void notify_entry_init ( NotifyEntry_t *entry );
void notify_entry_free(NotifyEntry_t *entry );

char* notify_entry_to_string(NotifyEntry_t entry ) ;

void notify_schema_change_callback(int sig, siginfo_t *si, void *data);
void notify_listener_change_callback(int sig, siginfo_t *si, void *data);

#endif
