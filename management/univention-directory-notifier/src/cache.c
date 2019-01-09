/*
 * Univention Directory Notifier
 *  cache.c
 *
 * Copyright 2004-2019 Univention GmbH
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
#define _GNU_SOURCE

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <univention/debug.h>

#include "cache.h"
#include "notify.h"

long long notifier_cache_size = 1000;

static notify_cache_t *cache;

/*
 * Return cache bucket for transaction id.
 * :param id: Tranbsaction ID.
 * :return: Cache entry.
 */
static inline notify_cache_t *lookup(NotifyId id) {
	return cache + id % notifier_cache_size;
}

/*
 * Initialize cache with up to given number of entries.
 * :param max_id: Number of cache entries.
 * :returns: 0 on success, 1 on errors.
 */
int notifier_cache_init(NotifyId max_id) {
	NotifyId id;

	cache = calloc(notifier_cache_size, sizeof(notify_cache_t));

	id = max_id <= notifier_cache_size ? 1 : max_id - notifier_cache_size + 1;
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Loading cache %ld..%ld", id, max_id);
	for (; id <= max_id; id++) {
		notify_cache_t *entry = lookup(id);
		char *buffer = notify_transcation_get_one_dn(id);
		if (buffer == NULL) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "Failed lookup: %ld", id);
			continue;
		}
		if (notifer_cache_parse(buffer, entry))
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Failed parse: %s", buffer);

		free(buffer);
	}

	return 0;
}

/*
 * Add new transaction to cache.
 * :param id: Transaction ID.
 * :param dn: Distinguished name.
 * :param cmd: LDAP command.
 * :returns: 0
 */
int notifier_cache_add(NotifyId id, char *dn, char cmd) {
	if (dn == NULL)
		return 0;

	notify_cache_t *entry = lookup(id);

	free(entry->dn);
	entry->id = id;
	entry->dn = strdup(dn);
	entry->command = cmd;

	return 0;
}

/*
 * Lookup and return transaction.
 * :param id: Transaction id to lookup.
 * :returns: A string with transactions ID, DN and command separated by one blank.
 */
char *notifier_cache_get(NotifyId id) {
	char *str = NULL;
	notify_cache_t *entry = lookup(id);

	if (entry->id == id) {
		if (asprintf(&str, "%ld %s %c", entry->id, entry->dn, entry->command) < 0)
			abort();
	}

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "cache[%ld] = [%s]", id, str ? str : "<NULL>");
	return str;
}

/*
 * Parse line into transaction entry.
 * :param buffer: the string buffer containing a single line.
 * :param entry: Return variable for parsed entry.
 * :returns: 0 on success, 1 on errors.
 */
int notifer_cache_parse(const char *buffer, notify_cache_t *entry) {
	const char *head, *tail;

	if (sscanf(buffer, "%ld", &(entry->id)) != 1)
		return 1;
	head = index(buffer, ' ');
	if (head == NULL)
		return 1;
	tail = rindex(++head, ' ');
	if (tail == NULL)
		return 1;
	entry->dn = strndup(head, tail - head);
	if (entry->dn == NULL)
		return 1;
	entry->command = tail[1];

	return 0;
}
