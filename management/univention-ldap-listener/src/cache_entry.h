/*
 * Univention LDAP Listener
 *  cache entry header information
 *
 * Copyright (C) 2004, 2005, 2006 Univention GmbH
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

#endif /* _CACHE_ENTRY_H_ */
