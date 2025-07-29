/*
 * Univention Directory Listener
 *  cache entry header information
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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

int cache_free_entry(char **dn, CacheEntry *entry);
void cache_dump_entry(char *dn, CacheEntry *entry, FILE *fp);
int cache_new_entry_from_ldap(char **dn, CacheEntry *cache_entry, LDAP *ld, LDAPMessage *ldap_entry);
int cache_entry_module_add(CacheEntry *entry, char *module);
int cache_entry_module_remove(CacheEntry *entry, char *module);
int cache_entry_module_present(CacheEntry *entry, char *module);
char **cache_entry_changed_attributes(CacheEntry *new, CacheEntry *old);

int copy_cache_entry(CacheEntry *cache_entry, CacheEntry *backup_cache_entry);

extern const char *cache_entry_get1(CacheEntry *entry, const char *key);
extern void cache_entry_set1(CacheEntry *entry, const char *key, const char *value);
extern CacheEntryAttribute *cache_entry_add1(CacheEntry *entry, const char *key, const char *value);

extern CacheEntryAttribute *cache_entry_update_rdn1(CacheEntry *entry, LDAPAVA *ava);
extern void cache_entry_update_rdn(struct transaction *trans, LDAPRDN new_dn);

static inline bool cache_entry_valid(CacheEntry *entry) {
	return entry->attribute_count > 0;
}

#endif /* _CACHE_ENTRY_H_ */
