/*
 * Univention Directory Listener
 *  header information for base64.c
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _BASE64_H_
#define _BASE64_H_

#define BASE64_ENCODE_LEN(n)      (((n)+2)/3 * 4)
#define BASE64_DECODE_LEN(n)      (((n)+3)/4 * 3)

#include <sys/types.h>

int	base64_encode	(u_char const	*src,
			 size_t		 srclength,
			 char		*target,
			 size_t		 targsize);
int	base64_decode	(char const	*src,
			 u_char		*target,
			 size_t		 targsize);

#endif /* _BASE64_H_ */
