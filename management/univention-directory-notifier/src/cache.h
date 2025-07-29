/*
 * Univention Directory Notifier
 *  cache.h
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef __CACHE_H__
#define __CACHE_H__


typedef struct {
	unsigned long id;
	char *dn;
	char command;
} notify_cache_t;

int	notifier_cache_init ( unsigned long max_id);
void notifier_cache_free();
int notifier_cache_add(unsigned long id, char *dn, char cmd);

char* notifier_cache_get(unsigned long id);

#endif
