#include "test.c"
#include <ldap.h>
#include "../src/cache_entry.c"

#define TEST(n)   \
	_TEST(n); \
	static bool test_##n(void)

static LDAPAVA ava_dc_test = {
    .la_attr = {
        .bv_val = "dc", .bv_len = 2,
    },
    .la_value = {
        .bv_val = "test", .bv_len = 4,
    },
};

static CacheEntry entry_empty;

static char *attr_test[] = {
    "test", NULL,
};
static int len_test[] = {
    5, 0,
};
static CacheEntryAttribute attr_dc_test = {
    .name = "dc", .values = attr_test, .length = len_test, .value_count = 1,
};
static CacheEntryAttribute *attrs_dc_test[] = {
    &attr_dc_test, NULL,
};
static CacheEntry entry_dc_test = {
    .attributes = attrs_dc_test, .attribute_count = 1, .modules = NULL, .module_count = 0,
};

#define ASSERT(cond)                                      \
	do {                                              \
		if (!(cond)) {                            \
			fprintf(stderr, "! " #cond "\n"); \
			return false;                     \
		}                                         \
	} while (0)

TEST(find_attribute_empty) {
	return NULL == _cache_entry_find_attribute(&entry_empty, &ava_dc_test);
}

TEST(find_attribute_existing) {
	return NULL != _cache_entry_find_attribute(&entry_dc_test, &ava_dc_test);
}

TEST(force_attribute_empty) {
	CacheEntryAttribute *attr, init = {
	                               .name = "dc", .values = calloc(1, sizeof(char *)), .length = calloc(1, sizeof(int)), .value_count = 1,
	                           };
	init.values[0] = NULL;
	init.length[0] = 0;
	attr = _cache_entry_force_value(&init, &ava_dc_test);
	ASSERT(attr == &init);
	ASSERT(!strcmp(attr->name, "dc"));
	ASSERT(attr->value_count == 1);
	ASSERT(attr->length[0] == ava_dc_test.la_value.bv_len + 1);
	ASSERT(attr->length[1] == 0);
	ASSERT(!strcmp(attr->values[0], ava_dc_test.la_value.bv_val));
	ASSERT(attr->values[1] == NULL);
	free(attr->values[0]);
	free(attr->values);
	free(attr->length);
	return true;
}

TEST(force_attribute_replace) {
	CacheEntryAttribute *attr, init = {
	                               .name = "dc", .values = calloc(2, sizeof(char *)), .length = calloc(2, sizeof(int)), .value_count = 1,
	                           };
	init.values[0] = "other";
	init.values[1] = NULL;
	init.length[0] = 4;
	init.length[1] = 0;
	attr = _cache_entry_force_value(&init, &ava_dc_test);
	ASSERT(attr == &init);
	ASSERT(!strcmp(attr->name, "dc"));
	ASSERT(attr->value_count == 1);
	ASSERT(attr->length[0] == ava_dc_test.la_value.bv_len + 1);
	ASSERT(attr->length[1] == 0);
	ASSERT(!strcmp(attr->values[0], ava_dc_test.la_value.bv_val));
	ASSERT(attr->values[1] == NULL);
	free(attr->values[0]);
	free(attr->values);
	free(attr->length);
	return true;
}

TEST(add_attribute) {
	CacheEntry entry = {};
	CacheEntryAttribute *attr;
	attr = _cache_entry_add_new_attribute(&entry, &ava_dc_test);
	ASSERT(attr);
	ASSERT(attr->value_count == 1);
	ASSERT(attr->length[0] == ava_dc_test.la_value.bv_len + 1);
	ASSERT(attr->length[1] == 0);
	ASSERT(!strcmp(attr->values[0], ava_dc_test.la_value.bv_val));
	ASSERT(attr->values[1] == NULL);
	cache_free_entry(NULL, &entry);
	return true;
}
