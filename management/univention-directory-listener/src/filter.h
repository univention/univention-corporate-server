/*
 * Univention Directory Listener
 *  header information for filter.c
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _FILTER_H_
#define _FILTER_H_

#include "cache.h"
#include "handlers.h"

int cache_entry_ldap_filter_match(struct filter **filter, const char *dn, CacheEntry *entry);

#endif /* _FILTER_H_ */
