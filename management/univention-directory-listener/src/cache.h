/*
 * Univention Directory Listener
 *  header information for cache.c
 *
 * Copyright (C) 2004-2009 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Binary versions of this file provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

#ifndef _CACHE_H_
#define _CACHE_H_

#include <db.h>

#include "network.h"
#include "cache_entry.h"

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
int	cache_delete_entry			(NotifierID		  id,
						 char			 *dn);
int	cache_update_or_deleteifunused_entry	(NotifierID		  id,
						 char			 *dn,
						 CacheEntry		 *entry);
int	cache_get_entry				(NotifierID		  id,
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
int	cache_set_int				(const char		 *key,
						 const long		  value);
int	cache_get_int				(const char		 *key,
						 long			 *value,
						 const long		  def);

int cache_get_schema_id(const char *key, long *value, const long def);
int cache_set_schema_id(const char *key, const long value);

#endif /* _CACHE_H_ */
