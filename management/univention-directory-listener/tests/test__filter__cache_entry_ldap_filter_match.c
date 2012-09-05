#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include "filter.h"

static struct filter filter = {
	.base = "dc=bar,dc=baz",
	.scope = 2, // LDAP.SCOPE_SUBTREE
	.filter = "objectclass=*",
};
static struct filter *filters[2] = {
	&filter,
	NULL,
};
static CacheEntry entry = {
	.attributes = NULL,
	.attribute_count = 0,
	.modules = NULL,
	.module_count = 0,
};

static bool test_match_exact(void) {
	char dn[] = "dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters, dn, &entry);
	return r == 1;
}

static bool test_match_one(void) {
	char dn[] = "dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters, dn, &entry);
	return r == 1;
}

static bool test_match_other(void) {
	char dn[] = "dc=foo";
	int r = cache_entry_ldap_filter_match(filters, dn, &entry);
	return r == 0;
}

static bool test_match_sub(void) {
	char dn[] = "dc=bam,dc=foo,dc=bar,dc=baz";
	int r = cache_entry_ldap_filter_match(filters, dn, &entry);
	return r == 1;
}

static bool test_match_case(void) {
	char dn[] = "dc=foo,dc=bar,dc=BAZ";
	int r = cache_entry_ldap_filter_match(filters, dn, &entry);
	return r == 0;
}

static bool test_match_short(void) {
	char dn[] = "dc=baz";
	int r = cache_entry_ldap_filter_match(filters, dn, &entry);
	return r == 0;
}

static bool test_match_infix(void) {
	char dn[] = "dc=foo,dc=bar,dc=baz,dc=bam";
	int r = cache_entry_ldap_filter_match(filters, dn, &entry);
	return r == 0;
}

#define TEST(n) { .name = "test_" # n, .func = test_##n }
struct tests {
	const char *name;
	bool (*func)(void);
} tests[] = {
	TEST(match_exact),
	TEST(match_one),
	TEST(match_other),
	TEST(match_sub),
	TEST(match_case),
	TEST(match_short),
	TEST(match_infix),
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
