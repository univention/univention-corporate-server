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


static inline bool same_dn(const char *left, const char *right) {
	/* BUG: A DN is a sequence of RDNs. An RDN is a sequence of Attribute-value
	   pairs. Each attribute has its own schema definition with its own
	   governing rules. Some attributes are case-sensitive, some are not. As
	   such, a complete DN may have components that are case-sensitive as well
	   as case-insensitive. */

	UErrorCode status = U_ZERO_ERROR;
	UCaseMap *caseMap = ucasemap_open(NULL, U_FOLD_CASE_DEFAULT, &status);
	assert(U_SUCCESS(status));

	size_t lsize = strlen(left) + 1;
	char *lbuf = malloc(lsize * sizeof(char));
	assert(lbuf);
	do {
		status = U_ZERO_ERROR;
		lsize = ucasemap_utf8ToLower(caseMap, lbuf, lsize, left, -1, &status);
		if (status == U_BUFFER_OVERFLOW_ERROR) {
			lbuf = realloc(lbuf, lsize);
			assert(lbuf);
			continue;
		}
		assert(U_SUCCESS(status));
	} while(false);

	size_t rsize = strlen(right) + 1;
	char *rbuf = malloc(rsize * sizeof(char));
	assert(rbuf);
	do {
		UErrorCode status = U_ZERO_ERROR;
		rsize = ucasemap_utf8ToLower(caseMap, rbuf, rsize, right, -1, &status);
		if (status == U_BUFFER_OVERFLOW_ERROR) {
			rbuf = realloc(rbuf, rsize);
			assert(rbuf);
			continue;
		}
		assert(U_SUCCESS(status));
	} while(false);

	int result = strcmp(lbuf, rbuf);

	free(lbuf);
	free(rbuf);
	ucasemap_close(caseMap);

	return 0 == result;
}
