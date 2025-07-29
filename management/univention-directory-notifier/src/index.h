/*
 * Univention Directory Notifier
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#ifndef __NOTIFIER_INDEX_H__
#define __NOTIFIER_INDEX_H__

#include <stdio.h>

static const unsigned long MAGIC = 0x3395e0d4;

struct index_header {
	unsigned long magic;
} __attribute__((__packed__));
struct index_entry {
	char valid;
	size_t offset;  // BUG: should have been off_t as size_t is 32 bit even with _FILE_OFFSET_BITS=64 on i386
} __attribute__((__packed__));

FILE* index_open(const char *filename);
size_t index_get(FILE *fp, unsigned long id);
void index_set(FILE *fp, unsigned long id, size_t offset);

#endif /* __NOTIFIER_INDEX_H__ */
