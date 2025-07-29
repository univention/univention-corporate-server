/*
 * Univention Directory Listener
 *  header information for cache.c
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _CACHE_H_
#define _CACHE_H_

#include <lmdb.h>

#include "network.h"
#include "cache_entry.h"

extern int INIT_ONLY;
extern char *cache_dir;
extern char *ldap_dir;

int cache_lock(void);
int cache_init(char *cache_mdb_dir, int mdb_flags);
void cache_sync(void);
int cache_get_master_entry(CacheMasterEntry *master_entry);
int cache_update_master_entry(CacheMasterEntry *master_entry);
int cache_update_entry(NotifierID id, char *dn, CacheEntry *entry);
int cache_update_entry_lower(NotifierID id, char *dn, CacheEntry *entry);
int cache_delete_entry(NotifierID id, char *dn);
int cache_delete_entry_lower_upper(NotifierID id, char *dn);
int cache_update_or_deleteifunused_entry(NotifierID id, char *dn, CacheEntry *entry, MDB_cursor **cur);
int cache_get_entry(char *dn, CacheEntry *entry);
int cache_get_entry_lower_upper(char *dn, CacheEntry *entry);
int cache_first_entry(MDB_cursor **cur, MDB_cursor **cur_dn, char **dn, CacheEntry *entry);
int cache_next_entry(MDB_cursor **cur, MDB_cursor **cur_dn, char **dn, CacheEntry *entry);
int cache_free_cursor(MDB_cursor *cur, MDB_cursor *cur_dn);
void cache_close(void);

int cache_set_int(char *key, const NotifierID value);
int cache_get_int(char *key, NotifierID *value, const long def);

int cache_get_schema_id(NotifierID *value, const long def);
int cache_set_schema_id(const NotifierID value);

#endif /* _CACHE_H_ */
