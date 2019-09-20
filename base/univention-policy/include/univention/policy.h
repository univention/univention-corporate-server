/*
 * Univention Policy
 *  C source of the univention policy library
 *
 * Copyright 2003-2019 Univention GmbH
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

#ifndef __UNIVENTION_POLICY_H__
#define __UNIVENTION_POLICY_H__

#include <ldap.h>

typedef struct univention_policy_result_s {
	char* policy_dn;
	int count;
	char** values;
} univention_policy_result_t;

typedef struct univention_policy_handle_s univention_policy_handle_t;

univention_policy_handle_t* univention_policy_open(LDAP *ld, const char *base, const char *dn);
univention_policy_result_t* univention_policy_get(univention_policy_handle_t *handle, const char *policy_name, const char *attribute_name);
void univention_policy_close(univention_policy_handle_t* handle);

#endif
