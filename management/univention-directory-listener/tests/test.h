#include <stdlib.h>
#include <stdio.h>
#include <stdbool.h>
#include <ldap.h>

struct test_info {
	const char *name;
	bool (*func)(void);
};
extern struct test_info __start_my_tests;
extern struct test_info __stop_my_tests;
#define _TEST(n)                               \
	static bool test_##n(void);            \
	static struct test_info __test_##n     \
	__attribute((__section__("my_tests"))) \
	__attribute((__used__)) = {            \
		.name = "test_" # n,           \
		.func = test_##n,              \
	}

int main(int argc, char *argv[]) {
	int failed = 0;
	struct test_info *iter;
	for (iter = &__start_my_tests; iter < &__stop_my_tests; iter++)
		if (iter->func()) {
			fprintf(stdout, "+%s\n", iter->name);
		} else {
			fprintf(stdout, "-%s\n", iter->name);
			failed++;
		}
	return failed;
}
