/*
 * Univention Directory Listener
 *  utility functions
 *
 * SPDX-FileCopyrightText: 2014-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifdef DEBUG
#include <stdio.h>
#endif
#include <stdio.h>
#include <assert.h>
#include "utils.h"
#define U_CHARSET_IS_UTF8 1
#include <unicode/uchar.h>
#include <unicode/ucnv.h>


#define BUFSIZE(len) (((len)+1) * sizeof(*out))

static inline UChar *_from_utf8(const char *in, size_t len) {
	static UConverter *conv;
	if (!conv) {
		UErrorCode status = U_ZERO_ERROR;
		conv = ucnv_open("UTF-8", &status);
		assert(U_SUCCESS(status));
	}

	UChar *out = NULL;
	for (;;) {
		size_t size = BUFSIZE(len);
		out = realloc(out, size);
		assert(out);
		UErrorCode status = U_ZERO_ERROR;
		len = ucnv_toUChars(conv, out, size, in, -1, &status);
		switch (status) {
		default:
			assert(status);
		case U_ZERO_ERROR:
			return out;
		case U_STRING_NOT_TERMINATED_WARNING:
			len++;
		case U_BUFFER_OVERFLOW_ERROR:
			assert(BUFSIZE(len) > size);
		}
	}
}


static inline char *_to_utf8(const UChar *in, size_t len) {
	static UConverter *conv;
	if (!conv) {
		UErrorCode status = U_ZERO_ERROR;
		conv = ucnv_open("UTF-8", &status);
		assert(U_SUCCESS(status));
	}

	char *out = NULL;
	for (;;) {
		size_t size = BUFSIZE(len);
		out = realloc(out, size);
		assert(out);
		UErrorCode status = U_ZERO_ERROR;
		len = ucnv_fromUChars(conv, out, size, in, -1, &status);
		switch (status) {
		default:
			assert(status);
		case U_ZERO_ERROR:
			return out;
		case U_STRING_NOT_TERMINATED_WARNING:
			len++;
		case U_BUFFER_OVERFLOW_ERROR:
#ifdef DEBUG
			printf("%zd\n", len);
#endif
			assert(BUFSIZE(len) > size);
		}
	}
}


char *lower_utf8(const char *str) {
	size_t len = strlen(str);
	/* convert from UTF-8 to internal UChar */
	UChar *tmp = _from_utf8(str, len);
	/* convert to lower case */
	UChar *c;
	for (c = tmp; *c; c++)
		*c = u_tolower(*c);
	/* convert internal UChar to UTF-8 */
	char *out = _to_utf8(tmp, len);
	free(tmp);
	return out;
}


bool same_dn(const char *left, const char *right) {
	/* BUG: A DN is a sequence of RDNs. An RDN is a sequence of Attribute-value
	   pairs. Each attribute has its own schema definition with its own
	   governing rules. Some attributes are case-sensitive, some are not. As
	   such, a complete DN may have components that are case-sensitive as well
	   as case-insensitive. */
	char *lbuf = lower_utf8(left);
	char *rbuf = lower_utf8(right);
	int result = strcmp(lbuf, rbuf);

	free(lbuf);
	free(rbuf);

	return 0 == result;
}


int ldap_retries = -1;

int get_ldap_retries() {
	const int DEFAULT_RETRIES = 5;
	int retries = univention_config_get_int("listener/ldap/retries");
	return retries < 0 ? DEFAULT_RETRIES : retries;
}

int notifier_retries = -1;

int get_notifier_retries() {
	const int DEFAULT_RETRIES = 10;
	int retries = univention_config_get_int("listener/notifier/retries");
	return retries < 0 ? DEFAULT_RETRIES : retries;
}
