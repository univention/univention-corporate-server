/*
 * Univention Directory Listener
 *  header information for cache.c
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

#ifndef _CACHE_H_
#define _CACHE_H_

#include <lmdb.h>

#include "network.h"
#include "cache_entry.h"

extern int INIT_ONLY;
extern char *cache_dir;
extern char *ldap_dir;

extern int cache_lock(void);
extern int cache_init(char *cache_mdb_dir, int mdb_flags);
extern void cache_sync(void);
extern int cache_get_master_entry(CacheMasterEntry *master_entry);
extern int cache_update_master_entry(CacheMasterEntry *master_entry);
extern int cache_update_entry(NotifierID id, char *dn, CacheEntry *entry);
extern int cache_update_entry_lower(NotifierID id, char *dn, CacheEntry *entry);
extern int cache_delete_entry(NotifierID id, char *dn);
extern int cache_delete_entry_lower_upper(NotifierID id, char *dn);
extern int cache_update_or_deleteifunused_entry(NotifierID id, char *dn, CacheEntry *entry, MDB_cursor **cur);
extern int cache_get_entry(char *dn, CacheEntry *entry);
extern int cache_get_entry_lower_upper(char *dn, CacheEntry *entry);
extern int cache_first_entry(MDB_cursor **cur, MDB_cursor **cur_dn, char **dn, CacheEntry *entry);
extern int cache_next_entry(MDB_cursor **cur, MDB_cursor **cur_dn, char **dn, CacheEntry *entry);
extern int cache_free_cursor(MDB_cursor *cur, MDB_cursor *cur_dn);
extern void cache_close(void);

extern int cache_set_int(char *key, const NotifierID value);
extern int cache_get_int(char *key, NotifierID *value, const long def);

extern int cache_get_schema_id(NotifierID *value, const long def);
extern int cache_set_schema_id(const NotifierID value);

#endif /* _CACHE_H_ */
