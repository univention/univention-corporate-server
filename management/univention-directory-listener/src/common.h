/*
 * Univention Directory Listener
 *  header information common.h
 *
 * SPDX-FileCopyrightText: 2004-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _COMMON_H_
#define _COMMON_H_

#include <univention/debug.h>

extern void drop_privileges(void);

#ifdef DMALLOC
#include <dmalloc.h>
#endif /* DMALLOC */

#define STREQ(a, b) (strcmp(a, b) == 0)
#define STRNEQ(a, b) (strcmp(a, b) != 0)

#ifndef LOG_CATEGORY
#define LOG_CATEGORY UV_DEBUG_LISTENER
#endif
#define LOG(level, fmt, ...) \
	do { \
		univention_debug( \
			LOG_CATEGORY, UV_DEBUG_##level, \
			"%s:%d:%s " fmt, \
			__FILE__, __LINE__, __func__, ##__VA_ARGS__); \
	} while (0)

#endif /* _COMMON_H_ */
