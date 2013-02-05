/*
 * Univention Directory Listener
 *  cache entry header information
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

#ifndef _CACHE_ENTRY_H_
#define _CACHE_ENTRY_H_

#include <stdio.h>
#include <stdbool.h>
#include <ldap.h>
#include <univention/ldap.h>

#include "network.h"

typedef struct _CacheMasterEntry {
	NotifierID id;
	NotifierID schema_id;
} CacheMasterEntry;
extern CacheMasterEntry cache_master_entry;

struct _CacheEntryAttribute {
	char *name;
	char **values;
	int *length;
	int value_count;
} typedef CacheEntryAttribute;

struct _CacheEntry {
	CacheEntryAttribute **attributes;
	int attribute_count;
	char **modules;
	int module_count;
} typedef CacheEntry;

struct transaction_op {
	NotifierEntry notify;
	CacheEntry cache;
	char *ldap_dn;
	char *uuid;
};
struct transaction {
	univention_ldap_parameters_t *lp;
	univention_ldap_parameters_t *lp_local;
	LDAPMessage *ldap;
	struct transaction_op cur, prev;
};

/* Initialize interal setting once. */
extern void cache_entry_init(void);

extern int cache_free_entry(char **dn, CacheEntry *entry);
extern void cache_dump_entry(char *dn, CacheEntry *entry, FILE *fp);
extern int cache_new_entry_from_ldap(char **dn, CacheEntry *cache_entry, LDAP *ld, LDAPMessage *ldap_entry);
extern int cache_entry_module_add(CacheEntry *entry, char *module);
extern int cache_entry_module_remove(CacheEntry *entry, char *module);
extern int cache_entry_module_present(CacheEntry *entry, char *module);
extern char **cache_entry_changed_attributes(CacheEntry *new, CacheEntry *old);

extern int copy_cache_entry(CacheEntry *cache_entry, CacheEntry *backup_cache_entry);

extern const char *cache_entry_get1(CacheEntry *entry, const char *key);
extern void cache_entry_set1(CacheEntry *entry, const char *key, const char *value);
extern CacheEntryAttribute *cache_entry_add1(CacheEntry *entry, const char *key, const char *value);

extern CacheEntryAttribute *cache_entry_update_rdn1(CacheEntry *entry, LDAPAVA *ava);
extern void cache_entry_update_rdn(struct transaction *trans, LDAPRDN new_dn);

static inline bool cache_entry_valid(CacheEntry *entry) {
	return entry->attribute_count > 0;
}

#endif /* _CACHE_ENTRY_H_ */
