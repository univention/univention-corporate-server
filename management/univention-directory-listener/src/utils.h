#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <assert.h>
#include <ldap.h>
#define U_CHARSET_IS_UTF8 1
#include <unicode/uchar.h>
#include <unicode/ucasemap.h>
#include <unicode/ustring.h>


static inline bool BERSTREQ(const struct berval *ber, const char *str, size_t len) {
	return ber->bv_len == len && memcmp(ber->bv_val, str, len) == 0;
}


static inline int BER2STR(const struct berval *ber, char **strp) {
	*strp = malloc(ber->bv_len + 1);
	if (!*strp)
		return -1;
	memcpy(*strp, ber->bv_val, ber->bv_len);
	(*strp)[ber->bv_len] = '\0';
	return ber->bv_len;
}


static inline char *lower_utf8(const char *str, UCaseMap *caseMap) {
	size_t size = strlen(str);
	char *buf = NULL;
	for (;;) {
		buf = realloc(buf, size);
		assert(buf);
		UErrorCode status = U_ZERO_ERROR;
		size = ucasemap_utf8ToLower(caseMap, buf, size, str, -1, &status);
		switch (status) {
			default:
				strncpy(buf, str, size);
			case U_ZERO_ERROR:
				return buf;
			case U_STRING_NOT_TERMINATED_WARNING:
				size += 1;
			case U_BUFFER_OVERFLOW_ERROR:
				continue;
		}
	}
}


static inline bool same_dn(const char *left, const char *right) {
	/* BUG: A DN is a sequence of RDNs. An RDN is a sequence of Attribute-value
	   pairs. Each attribute has its own schema definition with its own
	   governing rules. Some attributes are case-sensitive, some are not. As
	   such, a complete DN may have components that are case-sensitive as well
	   as case-insensitive. */

	UErrorCode status = U_ZERO_ERROR;
	UCaseMap *caseMap = ucasemap_open(NULL, U_FOLD_CASE_DEFAULT, &status);
	assert(U_SUCCESS(status));

	char *lbuf = lower_utf8(left, caseMap);
	char *rbuf = lower_utf8(right, caseMap);
	int result = strcmp(lbuf, rbuf);

	free(lbuf);
	free(rbuf);
	ucasemap_close(caseMap);

	return 0 == result;
}
