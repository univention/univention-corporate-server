#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <ldap.h>


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
	return 0 == strcasecmp(left, right);
}
