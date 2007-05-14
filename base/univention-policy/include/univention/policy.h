/*
 * Univention Policy
 *  C source of the univnetion policy libary
 *
 * Copyright (C) 2003, 2004, 2005, 2006 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Binary versions of this file provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */

#ifndef __UNIVENTION_POLICY_H__
#define __UNIVENTION_POLICY_H__

#include <ldap.h>

typedef struct univention_policy_result_s {
	char* policy_dn;
	int count;
	char** values;
} univention_policy_result_t;

struct univention_policy_attribute_list_s;
struct univention_policy_attribute_list_s {
	struct univention_policy_attribute_list_s* next;
	char* name;
	univention_policy_result_t* values;
};

struct univention_policy_list_s;
struct univention_policy_list_s {
	struct univention_policy_list_s* next;
	char* name;
	struct univention_policy_attribute_list_s* attributes;
};

typedef struct univention_policy_handle_s {
	struct univention_policy_list_s* policies;
} univention_policy_handle_t;


univention_policy_handle_t* univention_policy_open(LDAP* ld, char* base, char* dn);
univention_policy_result_t* univention_policy_get(univention_policy_handle_t* handle, char* policy_name, char* attribute_name);
void univention_policy_close(univention_policy_handle_t* handle);

#endif
