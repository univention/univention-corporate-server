/*
 * Univention Directory Listener
 *  header information for cache.c
 *
 * Copyright 2004-2015 Univention GmbH
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

#include <db.h>

#include "network.h"
#include "cache_entry.h"

extern char *cache_dir;
extern char *ldap_dir;

#ifdef WITH_DB42
struct _CacheMasterEntry {
	NotifierID id;
	NotifierID schema_id;
} CacheMasterEntry;
#endif

int	cache_init				(void);
#ifdef WITH_DB42
int	cache_get_master_entry			(CacheMasterEntry	 *master_entry);
int	cache_update_master_entry		(CacheMasterEntry	 *master_entry,
						 DB_TXN			 *dptxnp);
#endif
int	cache_update_entry			(NotifierID		  id,
						 char			 *dn,
						 CacheEntry		 *entry);
inline int	cache_update_entry_lower			(NotifierID		  id,
						 char			 *dn,
						 CacheEntry		 *entry);
int	cache_delete_entry			(NotifierID		  id,
						 char			 *dn);
int	cache_delete_entry_lower_upper			(NotifierID		  id,
						 char			 *dn);
int	cache_update_or_deleteifunused_entry	(NotifierID		  id,
						 char			 *dn,
						 CacheEntry		 *entry);
int	cache_get_entry(
						 char			 *dn,
						 CacheEntry		 *entry);
int	cache_get_entry_lower_upper(
						 char			 *dn,
						 CacheEntry		 *entry);
int	cache_first_entry			(DBC			**cur,
						 char			**dn,
						 CacheEntry		 *entry);
int	cache_next_entry			(DBC			**cur,
						 char			**dn,
						 CacheEntry		 *entry);
int	cache_free_cursor			(DBC			 *cur);
int	cache_close				(void);

/* deprecated with DB42*/
int	cache_set_int				(char		 *key,
						 const NotifierID		  value);
int	cache_get_int				(char		 *key,
						 NotifierID			 *value,
						 const long		  def);

int cache_get_schema_id(char *key, NotifierID *value, const long def);
int cache_set_schema_id(char *key, const NotifierID value);

#endif /* _CACHE_H_ */
