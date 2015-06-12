#include "test.h"
#include <ldap.h>

#include "../src/cache.c"

static inline bool _test(const char *input, const char *expected) {
	char *output = _convert_to_lower(input);
	int ret = strcmp(output, expected);
	free(output);
	return ret == 0;
}
#define TEST(n, i, e)                                  \
	static bool test_##n(void) { return _test(i, e); } \
	_TEST(n)

TEST(same,
	"cn=foo,dc=univention,dc=de",
	"cn=foo,dc=univention,dc=de");
TEST(mixed,
	"cn=Foo,dc=univention,dc=de",
	"cn=foo,dc=univention,dc=de");
TEST(german,
	"cn=FÄÖÜß,dc=univention,dc=de",
	"cn=fäöüß,dc=univention,dc=de");
TEST(greek,
	"cn=FΩ,dc=univention,dc=de",
	"cn=fω,dc=univention,dc=de");
