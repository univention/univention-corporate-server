/*
 * Univention Directory Listener
 *  notifier.c
 *
 * Copyright 2004-2014 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */

/*
 * The name notifier might be misleading. The main function
 * "notifier_listener" uses the listener network API (network.c)
 * to receive updates from a notifier and calls the "change"
 * functions.
 */

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>

#include <univention/debug.h>
#include <univention/ldap.h>
#ifdef WITH_KRB5
#include <univention/krb5.h>
#endif

#include "notifier.h"
#include "common.h"
#include "handlers.h"
#include "cache.h"
#include "change.h"
#include "network.h"
#include "transfile.h"
#include "select_server.h"

#define DELAY_LDAP_CLOSE		15   /* 15 seconds */
#define DELAY_ALIVE			5*60 /* 5 minutes */
#define TIMEOUT_NOTIFIER_RECONNECT	5*60 /* 5 minutes */


static int connect_to_ldap(univention_ldap_parameters_t *lp,
		                univention_krb5_parameters_t *kp)
{
	/* XXX: Fix when using krb5 */
	while (univention_ldap_open(lp) != LDAP_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "can not connect to ldap server (%s)", lp->host);

		if (suspend_connect()) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN,
				"can not connect to any ldap server, retrying in 30 seconds");
			sleep(30);
		}

		select_server(lp);
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "chosen server: %s:%d", lp->host, lp->port);
	}

	return LDAP_SUCCESS;
}

/* listen for ldap updates */
int notifier_listen(univention_ldap_parameters_t *lp,
		univention_krb5_parameters_t *kp,
		int write_transaction_file,
		univention_ldap_parameters_t *lp_local)
{
	NotifierID	id;

#ifndef WITH_DB42
	/* we should only get here, if the cache has previously been
	   initialized; thus, *some* ID should've been stored in the
	   cache */
	cache_get_int("notifier_id", &id, -1);
	if ((long)id == -1) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to get last transaction ID from cache; possibly, it hasn't been initialized yet");
		return 1;
	}
#endif

	for (;;) {
		NotifierEntry	entry;
		int		msgid;
		time_t		timeout = DELAY_LDAP_CLOSE;
		int		rv;

		if ((msgid = notifier_get_dn(NULL, id+1)) < 1)
			break;

		/* wait for data; on timeouts, do maintenance stuff
		   such as closing the LDAP connection or running postrun
		   handlers */
		while (notifier_get_msg(NULL, msgid) == NULL) {
			/* timeout */
			if ((rv = notifier_wait(NULL, timeout)) == 0) {
				if (timeout == DELAY_ALIVE) {
					if (notifier_alive_s(NULL) == 1) {
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to get alive answer");
						return 1;
					}
					notifier_resend_get_dn(NULL, msgid, id+1);
				} else {
					if (lp->ld != NULL) {
						ldap_unbind_ext(lp->ld, NULL, NULL);
						lp->ld = NULL;
					}
					if (lp_local->ld != NULL) {
						ldap_unbind_ext(lp_local->ld, NULL, NULL);
						lp_local->ld = NULL;
					}
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "running postrun handlers");
					handlers_postrun_all();
					timeout = DELAY_ALIVE;
				}
				continue;
			} else if (rv > 0 && notifier_recv_result(NULL, NOTIFIER_TIMEOUT) == 0) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to recv result");
				return 1;
			} else if (rv < 0) {
				return 1;
			}
		}

		if (notifier_get_dn_result(NULL, msgid, &entry) != 0) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to get dn result");
			return 1;
		}
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "notifier returned = id: %ld\tdn: %s\tcmd: %c", entry.id, entry.dn, entry.command);

		if (entry.id != id+1) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "notifier returned transaction id %ld (%ld expected)", entry.id, id+1);
			notifier_entry_free(&entry);
			return 1;
		}

		/* ensure that LDAP connection is open */
		if (lp->ld == NULL) {
			if ((rv = connect_to_ldap(lp, kp)) != 0) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to connect to LDAP");
				notifier_entry_free(&entry);
				return rv;
			}
		}

		/* Try to do the change. If the LDAP server is down, try
		   to reconnect */
		while ((rv = change_update_dn(lp, entry.id, entry.dn, entry.command, lp_local)) != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "change_update_dn: %s", ldap_err2string(rv));
			if (rv == LDAP_SERVER_DOWN) {
				int rv2;
				if ((rv2 = connect_to_ldap(lp, kp)) != 0) {
					notifier_entry_free(&entry);
					return rv2;
				}
			} else {
				notifier_entry_free(&entry);
				return rv;
			}
		}

		/* rv had better be LDAP_SUCCESS if we get here */
		assert(rv == LDAP_SUCCESS);

		if (write_transaction_file && notifier_write_transaction_file(entry) != 0) {
			notifier_entry_free(&entry);
			break;
		}

		id = entry.id;
#ifndef WITH_DB42
		cache_set_int("notifier_id", id);
#endif
		notifier_entry_free(&entry);
	}

	return 0;
}
