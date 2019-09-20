 /*
 * Univention Configuration registry
 *  header file for univention config registry lib
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

#ifndef __UNIVENTION_CONFIG_H__
#define __UNIVENTION_CONFIG_H__

#include <stdio.h>

/**
 * Retrieve value of config registry entry associated with key.
 * @return an allocated buffer containingt the value or NULL on errors or if not found.
 */
char *univention_config_get_string(const char *key);
/**
 * Retrieve integer value of config registry entry associated with key.
 * @return an integer value of -1 on errors of if not found.
 */
int univention_config_get_int(const char *key);
/**
 * Retrieve integer value of config registry entry associated with key.
 * @return an integer value of -1 on errors of if not found.
 */
long univention_config_get_long(const char *key);
/**
 * Set config registry entry associated with key to new value.
 * @return 0 on success, -1 on internal errors.
 */
int univention_config_set_string(const char *key, const char *value);

#endif
