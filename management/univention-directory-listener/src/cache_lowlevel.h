/*
 * Univention Directory Listener
 *  header information for cache_lowlevel.c
 *
 * Copyright (C) 2004, 2005, 2006, 2007 Univention GmbH
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

#ifndef _CACHE_LOWLEVEL_
#define _CACHE_LOWLEVEL_

#include "cache.h"

int	unparse_entry	(void		**data,
			 u_int32_t	 *size,
			 CacheEntry	 *entry);
int	parse_entry	(void		 *data,
			 u_int32_t	  size,
			 CacheEntry	 *entry);
void hex_dump(int level, void *data, u_int32_t start, u_int32_t size);

#endif /* _CACHE_LOWLEVEL_ */
