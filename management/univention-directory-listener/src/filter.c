/*
 * Univention Directory Listener
 *  filter.c
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

/*
 * Functions to match LDAP filters to cache entries. Currently, we don't
 * use any schema information. However, to do this properly, we'd need to.
 */

#define _GNU_SOURCE /* for strndup */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "common.h"
#include "filter.h"


/* Check if entry matches value of attribute.
 * @param attribute Name of attribute.
 * @param value Expected string value. '*' as a wild-card at the front or end is supported.
 * @param entry Cached LDAP entry to match.
 * @return 1 on match, 0 otherwise.
 */
static int cache_entry_match_attribute_value(char *attribute, char *value, CacheEntry *entry) {
	CacheEntryAttribute **a;
	char **v;
	int len;
	int rv = 0;
	char *substr = NULL;
	int begins = 0, ends = 0;

	for (a = entry->attributes; a != NULL && *a != NULL; a++) {
		if (strcmp((*a)->name, attribute) == 0)
			break;
	}
	if (a == NULL || *a == NULL)
		return 0;

	if (strcmp(value, "*") == 0)
		return 1;

	len = strlen(value);
	begins = value[0] == '*';
	ends = value[len - 1] == '*';
	if (begins || ends)
		substr = strndup(value + begins, len - begins - ends);

	for (v = (*a)->values; v != NULL && *v != NULL; v++) {
		char *match;
		if (strcmp(*v, value) == 0) {
			rv = 1;
			break;
		} else if (substr != NULL && (match = strstr(*v, substr)) != NULL) {
			rv = (begins || match == *v) && (ends || strcmp(match, substr) == 0);
			if (rv)
				break;
		}
	}

	free(substr);
	return rv;
}


/* Check if entry matches the LDAP filter.
 * @param filter LDAP search filter supporting. LIMITED.
 * @param first Index into filter to specify start character.
 * @param last Index into filter to specify last character.
 * @param entry Cached LDAP entry to match.
 * @return 1 on match, 0 on no match, -1 on errors.
 */
static int __cache_entry_ldap_filter_match(char *filter, int first, int last, CacheEntry *entry) {
	/* sanity check */
	if (filter[first] != '(' || filter[last] != ')')
		return -1;

	if (filter[first + 1] == '&' || filter[first + 1] == '|' || filter[first + 1] == '!') {
		int i;
		int begin = -1;
		int depth = 0;

		/* sanity check */
		if (filter[first + 2] != '(' || filter[last - 1] != ')')
			return -1;

		for (i = first + 2; i <= last - 1; i++) {
			if (filter[i] == '(') {
				if (begin == -1)
					begin = i;
				++depth;
			} else if (filter[i] == ')' && begin != -1) {
				int cond_is_true;

				--depth;
				if (depth != 0)
					continue;

				cond_is_true = __cache_entry_ldap_filter_match(filter, begin, i, entry);
				if (!cond_is_true && filter[first + 1] == '&')
					return 0;
				else if (cond_is_true && filter[first + 1] == '|')
					return 1;
				else if (filter[first + 1] == '!')
					return !cond_is_true;

				begin = -1;
			}
		}

		if (filter[first + 1] == '&')
			return 1;
		else if (filter[first + 1] == '|')
			return 0;
		else /* '!', we shouldn't get here */
			return -1;
	} else {
		int type = -1; /* 0: =; 1: ~=; 2: >=; 3: <= */
		char *attr, *val;
		int i;
		int rv;

		for (i = first + 1; i <= last - 1; i++) {
			if (filter[i] == '=' && i > first + 1) {
				if (filter[i - 1] == '~')
					type = 1;
				else if (filter[i - 1] == '>')
					type = 2;
				else if (filter[i - 1] == '<')
					type = 3;
				else
					type = 0;
				break;
			}
		}
		if (type != 0) /* (type == -1) */
			return -1;

		attr = strndup(filter + first + 1, i - first - 1);
		val = strndup(filter + i + 1, last - i - 1);

		rv = cache_entry_match_attribute_value(attr, val, entry);

		free(attr);
		free(val);

		return rv;
	}

	return -1;
}


/* Check if entry matches LDAP dn.
 * @param filter An array of LDAP filters, scopes and bases.
 * @param dn The distinguished name of the cached LDAP entry.
 * @param entry Cached LDAP entry to match.
 * @return 1 on match, 0 otherwise.
 */
int cache_entry_ldap_filter_match(struct filter **filter, const char *dn, CacheEntry *entry) {
	struct filter **f;
	size_t dn_len = strlen(dn);

	for (f = filter; f != NULL && *f != NULL; f++) {
		/* check if base and scope match */
		if ((*f)->base != NULL && (*f)->base[0] != '\0') {
			size_t b_len = strlen((*f)->base);
			/* No match if required base is longer then tested dn */
			if (b_len > dn_len)
				continue;
			/* No match if testes dn does not end on required base */
			if (strcmp(dn + dn_len - b_len, (*f)->base))
				continue;

			switch ((*f)->scope) {
			case LDAP_SCOPE_BASE:
				/* skip if more levels exists. */
				if (strchr(dn, ',') <= dn + dn_len - b_len)
					continue;
				break;
			case LDAP_SCOPE_ONELEVEL:
				/* skip if more then one level */
				if (strchr(dn, ',') + 1 != dn + dn_len - b_len)
					continue;
				break;
			}
		}

		int len = strlen((*f)->filter);
		if (__cache_entry_ldap_filter_match((*f)->filter, 0, len - 1, entry))
			return 1;
	}
	return 0;
}
