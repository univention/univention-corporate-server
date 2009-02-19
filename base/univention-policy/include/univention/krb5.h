/*
 * Univention Policy
 *  C source of the univnetion policy libary
 *
 * Copyright (C) 2003-2009 Univention GmbH
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

#ifndef __UNIVENTION_KRB5_H__
#define __UNIVENTION_KRB5_H__

#include <krb5.h>

typedef struct univention_krb5_parameters_s {
	char *username;
	char *realm;
	char *password;

	krb5_context context;
	krb5_ccache ccache;
	krb5_principal principal;
	krb5_creds creds;
} univention_krb5_parameters_t;

univention_krb5_parameters_t* univention_krb5_new(void);
int univention_krb5_init(univention_krb5_parameters_t *kp);

#endif
