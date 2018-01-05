#include "test.c"
#include <ldap.h>

#include "../src/utils.h"

#define TEST(n, a, b, e)                   \
	static bool test_##n(void) {       \
		return same_dn(a, b) == e; \
	}                                  \
	_TEST(n)

#define BUG !

TEST(same, "cn=foo,dc=univention,dc=de", "cn=foo,dc=univention,dc=de", true);
TEST(case, "cn=foo,dc=univention,dc=de", "cn=fOO,dc=Univention,dc=DE", true);
TEST(different, "cn=foo,dc=univention,dc=de", "cn=bar,dc=univention,dc=de", false);
TEST(same_rdn, "cn=foo+cn=bar,dc=univention,dc=de", "cn=foo+cn=bar,dc=univention,dc=de", true);
TEST(different_rdn, "cn=foo+cn=baz,dc=univention,dc=de", "cn=bar+cn=baz,dc=univention,dc=de", false);
TEST(subset_rdn, "cn=foo,dc=univention,dc=de", "cn=foo+cn=bar,dc=univention,dc=de", false);
TEST(swapped_rdn, "cn=foo+cn=bar,dc=univention,dc=de", "cn=bar+cn=foo,dc=univention,dc=de", BUG true);
TEST(canonical, "cn=foo,dc=univention,dc=de", "commonName=foo,dc=univention,dc=de", BUG true);

// <http://www.ietf.org/rfc/rfc2253.txt>

// Implementations MUST allow a semicolon character to be used instead of a comma to separate RDNs in a distinguished name
TEST(semicolon, "cn=foo,dc=univention,dc=de", "cn=foo;dc=univention;dc=de", BUG true);
// and MUST also allow whitespace characters to be present on either side of the comma or semicolon.  The whitespace characters are ignored
TEST(space, "cn=foo,dc=univention,dc=de", " cn = foo , dc = univention , dc = de ", BUG true);
// Implementations MUST allow an oid in the attribute type to be prefixed by one of the character strings "oid." or "OID."
TEST(oid, "2.5.4.3=foo,dc=univention,dc=de", "oid.2.5.4.3=foo;dc=univention;dc=de", BUG true);
TEST(OID, "2.5.4.3=foo,dc=univention,dc=de", "OID.2.5.4.3=foo;dc=univention;dc=de", BUG true);
// Implementations MUST allow a value to be surrounded by quote ('"' ASCII 34) characters
TEST(quoted, "cn=foo\\,bar,dc=univention,dc=de", "cn=\"foo bar\",dc=univention,dc=de", BUG true);

TEST(octothorpe, "cn=foo,dc=univention,dc=de", "cn=#666f6f,dc=univention,dc=de", false);  // LDAP_AVA_STRING != LDAP_AVA_BINARY

TEST(umlaut, "cn=föö,dc=univention,dc=de", "cn=FÖÖ,dc=univention,dc=de", true);

TEST(germansz, "cn=fuß,dc=univention,dc=de", "cn=fuss,dc=univention,dc=de", false);

TEST(turkishi, "cn=iIıİ,dc=univention,dc=de", "cn=Iiıi,dc=univention,dc=de", true);

TEST(greek, "cn=ωΩ,dc=univention,dc=de", "cn=Ωω,dc=univention,dc=de", true);

#if 0
TEST(leading_hash, "cn=\\#foo,dc=univention,dc=de", ..., ...)
TEST(leading_space, "cn=\\ foo,dc=univention,dc=de", ..., ...)
TEST(trailing_space, "cn=foo\\ ,dc=univention,dc=de", ..., ...)
TEST(single, "CN=Steve Kille,O=Isode Limited,C=GB", ..., ...)
TEST(multi, "OU=Sales+CN=J. Smith,O=Widget Inc.,C=US", ..., ...)
TEST(comma, "CN=L. Eagle,O=Sue\\, Grabbit and Runn,C=GB", ..., ...)
TEST(newline, "CN=Before\\0DAfter,O=Test,C=GB", ..., ...)
TEST(octet, "1.3.6.1.4.1.1466.0=#04024869,O=Test,C=GB", ..., ...)
TEST(utf8, "SN=Lu\\C4\\8Di\\C4\\87", ..., ...)
#endif
