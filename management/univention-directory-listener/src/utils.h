#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <ldap.h>
#include <univention/config.h>


#define FREE(ptr)           \
	do {                \
		free(ptr);  \
		ptr = NULL; \
	} while (0)


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

static inline int ldap_timeout_scans() {
	const int DEFAULT_TIMEOUT = 2 * 60 * 60;
	int timeout = univention_config_get_int("listener/timeout/scans");
	return timeout < 0 ? DEFAULT_TIMEOUT : timeout;
}

extern int ldap_retries;
extern int get_ldap_retries();
#define LDAP_RETRY(lp, cmd)                                                                       \
	({                                                                                        \
		int _rv, _retry = 0;                                                              \
		if (ldap_retries < 0)                                                             \
			ldap_retries = get_ldap_retries();                                        \
		do {                                                                              \
			_rv = (cmd);                                                              \
			if (_rv != LDAP_SERVER_DOWN)                                              \
				break;                                                            \
			while (_retry < ldap_retries && univention_ldap_open(lp) != LDAP_SUCCESS) \
				sleep(1 << (_retry++ % 6));                                       \
		} while (_retry < ldap_retries);                                                  \
		_rv;                                                                              \
	})

extern char *lower_utf8(const char *str);
extern bool same_dn(const char *left, const char *right);
