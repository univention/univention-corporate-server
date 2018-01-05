#include <stdbool.h>
#include <ldap.h>

struct test_info {
	const char *name;
	bool (*func)(void);
};
#define _TEST(n)                                                                                          \
	static bool test_##n(void);                                                                           \
	static struct test_info __test_##n __attribute((__section__("my_tests"))) __attribute((__used__)) = { \
	    .name = "test_" #n, .func = test_##n,                                                             \
	}
