/*
 * Univention Directory Listener
 *  cache entry header information
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

#ifndef _CACHE_ENTRY_H_
#define _CACHE_ENTRY_H_

#include <stdio.h>
#include <ldap.h>

struct _CacheEntryAttribute {
	char			 *name;
	char			**values;
	int			*length;
	int			  value_count;
} typedef CacheEntryAttribute;

struct _CacheEntry {
	CacheEntryAttribute	**attributes;
	int			  attribute_count;
	char			**modules;
	int			  module_count;
} typedef CacheEntry;

int	cache_free_entry		(char		**dn,
					 CacheEntry	 *entry);
int	cache_dump_entry		(char		 *dn,
					 CacheEntry	 *entry,
					 FILE		 *fp);
int	cache_new_entry_from_ldap	(char		**dn,
					 CacheEntry	 *cache_entry,
					 LDAP		 *ld,
					 LDAPMessage	 *ldap_entry);
int	cache_entry_module_add		(CacheEntry	 *entry,
					 char		 *module);
int	cache_entry_module_remove	(CacheEntry	 *entry,
					 char		 *module);
int	cache_entry_module_present	(CacheEntry	 *entry,
					 char		 *module);
char**	cache_entry_changed_attributes	(CacheEntry	 *new,
					 CacheEntry	 *old);

int	copy_cache_entry		(CacheEntry *cache_entry,
					 CacheEntry *backup_cache_entry);

void	compare_cache_entries		(CacheEntry *lentry,
					 CacheEntry *rentry);

#endif /* _CACHE_ENTRY_H_ */
