 /*
 * Univention Configuration registry
 *  header file for univention config registry lib
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
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
