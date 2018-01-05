#include "test.c"
#include <ldap.h>

#include "../src/change.c"

static inline bool _test(const char *left, const char *right, bool expected) {
	bool rv;
	LDAPDN a = NULL, b = NULL;
	ldap_str2dn(left, &a, 0);
	ldap_str2dn(right, &b, 0);
	rv = same_rdn(a[0], b[0]);
	ldap_dnfree(a);
	ldap_dnfree(b);
	return rv == expected;
}
#define TEST(n, a, b, e)               \
	static bool test_##n(void) {   \
		return _test(a, b, e); \
	}                              \
	_TEST(n)

TEST(same, "cn=foo,dc=univention,dc=de", "cn=foo,dc=univention,dc=de", true);
TEST(different, "cn=foo,dc=univention,dc=de", "cn=bar,dc=univention,dc=de", false);
TEST(same_rdn, "cn=foo+cn=bar,dc=univention,dc=de", "cn=foo+cn=bar,dc=univention,dc=de", true);
TEST(different_rdn, "cn=foo+cn=baz,dc=univention,dc=de", "cn=bar+cn=baz,dc=univention,dc=de", false);
TEST(subset_rdn, "cn=foo,dc=univention,dc=de", "cn=foo+cn=bar,dc=univention,dc=de", false);
TEST(swapped_rdn, "cn=foo+cn=bar,dc=univention,dc=de", "cn=bar+cn=foo,dc=univention,dc=de", true);
