#include "test.c"
#include <ldap.h>

#include "../src/utils.h"

static inline bool _test(const char *input, const char *expected) {
	char *output = lower_utf8(input);
	int ret = strcmp(output, expected);
	if (ret)
		fprintf(stderr, " i=%s\n o=%s\n e=%s\n", input, output, expected);
	free(output);
	return ret == 0;
}
#define TEST(n, i, e)                \
	static bool test_##n(void) { \
		return _test(i, e);  \
	}                            \
	_TEST(n)

TEST(same, "cn=foo,dc=univention,dc=de", "cn=foo,dc=univention,dc=de");
TEST(mixed, "cn=Foo,dc=univention,dc=de", "cn=foo,dc=univention,dc=de");
TEST(german, "cn=FÄÖÜß,dc=univention,dc=de", "cn=fäöüß,dc=univention,dc=de");
TEST(greek, "cn=FΩ,dc=univention,dc=de", "cn=fω,dc=univention,dc=de");
TEST(turkish, "cn=âÇçĞğİiIıîŞş,dc=univention,dc=de", "cn=âççğğiiiıîşş,dc=univention,dc=de");
/* not: "cn=âççğği̇iııîşş,dc=univention,dc=de"); */
