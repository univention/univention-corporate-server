/*
 * Univention Directory Listener
 *  header information for cache_lowlevel.c
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _CACHE_LOWLEVEL_
#define _CACHE_LOWLEVEL_

#include "cache.h"

int unparse_entry(void **data, u_int32_t *size, CacheEntry *entry);
int parse_entry(void *data, u_int32_t size, CacheEntry *entry);
void hex_dump(int level, void *data, u_int32_t start, u_int32_t size);
void abort_io(const char *func, const char *filename) __attribute__((noreturn));

#endif /* _CACHE_LOWLEVEL_ */
