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
#include <stdbool.h>

/**
 * Retrieve value of config registry entry associated with key.
 * @return an allocated buffer containing the value or NULL on errors if not found.
 */
char *univention_config_get_string(const char *key);
/**
 * Retrieve integer value of config registry entry associated with key.
 * @return an integer value of -1 on errors if not found.
 */
int univention_config_get_int(const char *key);
/**
 * Retrieve integer value of config registry entry associated with key.
 * @return an integer value of -1 on errors if not found.
 */
long univention_config_get_long(const char *key);
/**
 * Set config registry entry associated with key to new value.
 * @return 0 on success, -1 on internal errors.
 */
int univention_config_set_string(const char *key, const char *value);
/**
 * Return whether the strings value of key is considered as true
 * @return true or false if value is set otherwise default_value
 */
bool univention_config_is_true(const char *key, bool default_value);

#endif
