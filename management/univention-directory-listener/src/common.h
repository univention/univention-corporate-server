/*
 * Univention Directory Listener
 *  header information common.h
 *
 * Copyright 2004-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
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
