#include "test.c"
#include "filter.h"

static struct filter filter_base = {
    .base = "dc=bar,dc=baz",
    .scope = 0,  // LDAP.SCOPE_BASE
    .filter = "objectclass=*",
};
static struct filter *filters_base[2] = {
    &filter_base, NULL,
};
static struct filter filter_one = {
    .base = "dc=bar,dc=baz",
    .scope = 1,  // LDAP.SCOPE_ONELEVEL
    .filter = "objectclass=*",
};
static struct filter *filters_one[2] = {
    &filter_one, NULL,
};
static struct filter filter_sub = {
    .base = "dc=bar,dc=baz",
    .scope = 2,  // LDAP.SCOPE_SUBTREE
    .filter = "objectclass=*",
};
static struct filter *filters_sub[2] = {
    &filter_sub, NULL,
};
static CacheEntry entry = {
    .attributes = NULL, .attribute_count = 0, .modules = NULL, .module_count = 0,
};

#define TEST(n)   \
	_TEST(n); \
	static bool test_##n(void)
TEST(match_exact_base) {
	char dn[] = "dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_base, dn, &entry);
	return r == 1;
}
TEST(match_exact_one) {
	char dn[] = "dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_one, dn, &entry);
	return r == 0;
}
TEST(match_exact_sub) {
	char dn[] = "dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 1;
}

TEST(match_one_base) {
	char dn[] = "dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_base, dn, &entry);
	return r == 0;
}
TEST(match_one_one) {
	char dn[] = "dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_one, dn, &entry);
	return r == 1;
}
TEST(match_one_sub) {
	char dn[] = "dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 1;
}

TEST(match_other_base) {
	char dn[] = "dc=foo";
	int r = cache_entry_ldap_filter_match(filters_base, dn, &entry);
	return r == 0;
}
TEST(match_other_one) {
	char dn[] = "dc=foo";
	int r = cache_entry_ldap_filter_match(filters_one, dn, &entry);
	return r == 0;
}
TEST(match_other_sub) {
	char dn[] = "dc=foo";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 0;
}

TEST(match_sub_base) {
	char dn[] = "dc=bam,dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_base, dn, &entry);
	return r == 0;
}
TEST(match_sub_one) {
	char dn[] = "dc=bam,dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_one, dn, &entry);
	return r == 0;
}
TEST(match_sub_sub) {
	char dn[] = "dc=bam,dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 1;
}

TEST(match_case_sub) {
	char dn[] = "dc=foo,dc=bar,dc=BAZ";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 0;
}

TEST(match_short_sub) {
	char dn[] = "dc=baz";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 0;
}

TEST(match_infix_sub) {
	char dn[] = "dc=foo,dc=bar,dc=baz,dc=bam";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 0;
}
