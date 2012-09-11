#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include "filter.h"

static struct filter filter_base = {
	.base = "dc=bar,dc=baz",
	.scope = 0, // LDAP.SCOPE_BASE
	.filter = "objectclass=*",
};
static struct filter *filters_base[2] = {
	&filter_base,
	NULL,
};
static struct filter filter_one = {
	.base = "dc=bar,dc=baz",
	.scope = 1, // LDAP.SCOPE_ONELEVEL
	.filter = "objectclass=*",
};
static struct filter *filters_one[2] = {
	&filter_one,
	NULL,
};
static struct filter filter_sub = {
	.base = "dc=bar,dc=baz",
	.scope = 2, // LDAP.SCOPE_SUBTREE
	.filter = "objectclass=*",
};
static struct filter *filters_sub[2] = {
	&filter_sub,
	NULL,
};
static CacheEntry entry = {
	.attributes = NULL,
	.attribute_count = 0,
	.modules = NULL,
	.module_count = 0,
};

static bool test_match_exact_base(void) {
	char dn[] = "dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_base, dn, &entry);
	return r == 1;
}
static bool test_match_exact_one(void) {
	char dn[] = "dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_one, dn, &entry);
	return r == 0;
}
static bool test_match_exact_sub(void) {
	char dn[] = "dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 1;
}

static bool test_match_one_base(void) {
	char dn[] = "dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_base, dn, &entry);
	return r == 0;
}
static bool test_match_one_one(void) {
	char dn[] = "dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_one, dn, &entry);
	return r == 1;
}
static bool test_match_one_sub(void) {
	char dn[] = "dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 1;
}

static bool test_match_other_base(void) {
	char dn[] = "dc=foo";
	int r = cache_entry_ldap_filter_match(filters_base, dn, &entry);
	return r == 0;
}
static bool test_match_other_one(void) {
	char dn[] = "dc=foo";
	int r = cache_entry_ldap_filter_match(filters_one, dn, &entry);
	return r == 0;
}
static bool test_match_other_sub(void) {
	char dn[] = "dc=foo";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 0;
}

static bool test_match_sub_base(void) {
	char dn[] = "dc=bam,dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_base, dn, &entry);
	return r == 0;
}
static bool test_match_sub_one(void) {
	char dn[] = "dc=bam,dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_one, dn, &entry);
	return r == 0;
}
static bool test_match_sub_sub(void) {
	char dn[] = "dc=bam,dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 1;
}

static bool test_match_case_sub(void) {
	char dn[] = "dc=foo,dc=bar,dc=BAZ";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 0;
}

static bool test_match_short_sub(void) {
	char dn[] = "dc=baz";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 0;
}

static bool test_match_infix_sub(void) {
	char dn[] = "dc=foo,dc=bar,dc=baz,dc=bam";
	int r = cache_entry_ldap_filter_match(filters_sub, dn, &entry);
	return r == 0;
}

#define TEST(n) { .name = "test_" # n, .func = test_##n }
struct tests {
	const char *name;
	bool (*func)(void);
} tests[] = {
	TEST(match_exact_base),
	TEST(match_exact_one),
	TEST(match_exact_sub),
	TEST(match_one_base),
	TEST(match_one_one),
	TEST(match_one_sub),
	TEST(match_other_base),
	TEST(match_other_one),
	TEST(match_other_sub),
	TEST(match_sub_base),
	TEST(match_sub_one),
	TEST(match_sub_sub),
	TEST(match_case_sub),
	TEST(match_short_sub),
	TEST(match_infix_sub),
};
#define ARRAY_SIZE(x) (sizeof(x) / sizeof(*(x)))

int main(int argc, char *argv[]) {
	int i, failed = 0;
	for (i = 0; i < ARRAY_SIZE(tests); i++)
		if (tests[i].func()) {
			fprintf(stdout, "+%s\n", tests[i].name);
		} else {
			fprintf(stdout, "-%s\n", tests[i].name);
			failed++;
		}
	return failed;
}
