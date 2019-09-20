/*
 * Univention Debug
 *  debug.h
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

#ifndef __DEBUG_H__
#define __DEBUG_H__

#include <stdio.h>

enum uv_debug_level {
	UV_DEBUG_ERROR = 0,
	UV_DEBUG_WARN = 1,
	UV_DEBUG_PROCESS = 2,
	UV_DEBUG_INFO = 3,
	UV_DEBUG_ALL = 4
};

enum uv_debug_category {
	UV_DEBUG_MAIN		= 0x00,
	UV_DEBUG_LDAP		= 0x01,
	UV_DEBUG_USERS		= 0x02,
	UV_DEBUG_NETWORK	= 0x03,
	UV_DEBUG_SSL		= 0x04,
	UV_DEBUG_SLAPD		= 0x05,
	UV_DEBUG_SEARCH		= 0x06,
	UV_DEBUG_TRANSFILE	= 0x07,
	UV_DEBUG_LISTENER	= 0x08,
	UV_DEBUG_POLICY		= 0x09,
	UV_DEBUG_ADMIN		= 0x0A,
	UV_DEBUG_CONFIG		= 0x0B,
	UV_DEBUG_LICENSE	= 0x0C,
	UV_DEBUG_KERBEROS	= 0x0D,
	UV_DEBUG_DHCP		= 0x0E,
	UV_DEBUG_PROTOCOL	= 0x0F,
	UV_DEBUG_MODULE		= 0x10,
	UV_DEBUG_ACL		= 0x11,
	UV_DEBUG_RESOURCES	= 0x12,
	UV_DEBUG_PARSER		= 0x13,
	UV_DEBUG_LOCALE		= 0x14,
	UV_DEBUG_AUTH		= 0x15,

	DEBUG_MODUL_COUNT 	= 0x16
};

enum uv_debug_flag_flush {
	UV_DEBUG_NO_FLUSH = 0x00,
	UV_DEBUG_FLUSH = 0x01
};

enum uv_debug_flag_function {
	UV_DEBUG_NO_FUNCTION = 0x00,
	UV_DEBUG_FUNCTION = 0x01
};

/**
 * Log message of level and category id.
 */
void univention_debug(enum uv_debug_category id, enum uv_debug_level level, const char *fmt, ...)
	__attribute__ ((format (printf, 3, 4)));
/**
 * Log begin of function s.
 */
void univention_debug_begin(const char *s);
/**
 * Log end of function s.
 */
void univention_debug_end(const char *s);
/**
 * Set debug level of category id to specified level.
 */
void univention_debug_set_level(enum uv_debug_category id, enum uv_debug_level level);
/**
 * Get debug level of category id
 */
enum uv_debug_level univention_debug_get_level(enum uv_debug_category id);
/**
 * Enable or disable logging of function begin and end.
 */
void univention_debug_set_function(enum uv_debug_flag_function function);
/**
 * Initialize debugging library.
 */
FILE * univention_debug_init(const char *logfile, enum uv_debug_flag_flush flush, enum uv_debug_flag_function function);
/**
 * Close old logfile and re-open it.
 */
void univention_debug_reopen(void);
/**
 * De-initialize debugging library to flush and close logfile.
 */
void univention_debug_exit(void);

#endif
