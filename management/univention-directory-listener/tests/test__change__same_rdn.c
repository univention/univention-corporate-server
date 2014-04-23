#include "test.h"
#include <ldap.h>
//#include "change.h"

static bool
same_rdn(LDAPRDN left, LDAPRDN right)
{
	int i, j;

	for (i = 0; left[i]; i++) {
		for (j = 0; right[j]; j++) {
			if (left[i]->la_attr.bv_len != right[j]->la_attr.bv_len)
				continue; // inner
			if (left[i]->la_value.bv_len != right[j]->la_value.bv_len)
				continue; // inner
			if (memcmp(left[i]->la_attr.bv_val, right[j]->la_attr.bv_val, left[i]->la_attr.bv_len) == 0 &&
			    memcmp(left[i]->la_value.bv_val, right[j]->la_value.bv_val, left[i]->la_value.bv_len) == 0)
				break; // to outer
		}
		if (!right[j])
			return false;
	}

	for (j = 0; right[j]; j++)
		;
	return i == j;
}

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
#define TEST(n, a, b, e)                                      \
	static bool test_##n(void) { return _test(a, b, e); } \
	_TEST(n)

TEST(same,
	"cn=foo,dc=univention,dc=de",
	"cn=foo,dc=univention,dc=de", true);
TEST(different,
	"cn=foo,dc=univention,dc=de",
	"cn=bar,dc=univention,dc=de", false);
TEST(same_rdn,
	"cn=foo+cn=bar,dc=univention,dc=de",
	"cn=foo+cn=bar,dc=univention,dc=de", true);
TEST(different_rdn,
	"cn=foo+cn=baz,dc=univention,dc=de",
	"cn=bar+cn=baz,dc=univention,dc=de", false);
TEST(subset_rdn,
	"cn=foo,dc=univention,dc=de",
	"cn=foo+cn=bar,dc=univention,dc=de", false);
TEST(swapped_rdn,
	"cn=foo+cn=bar,dc=univention,dc=de",
	"cn=bar+cn=foo,dc=univention,dc=de", true);
