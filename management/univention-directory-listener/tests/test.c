#include <stdlib.h>
#include <stdio.h>
#include "test.h"

extern struct test_info __start_my_tests;
extern struct test_info __stop_my_tests;

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
