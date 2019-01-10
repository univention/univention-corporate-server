#define FILE_NAME_TF "./data"
#include "../src/notify.c"
#include <unistd.h>
#include "test.c"

long long notifier_lock_time = 1;
long long notifier_lock_count = 1;

static inline bool _test(NotifyId expected, const char *data) {
	FILE *f = fopen(FILE_NAME_TF, "w");
	fwrite(data, strlen(data), 1, f);
	fclose(f);

	NotifyId_t id = { .id = 4711 };
	notify_transaction_get_last_notify_id(&id);

	unlink(FILE_NAME_TF);
	unlink(FILE_NAME_TF ".lock");
	return id.id == expected;
}
#define TEST(n, id, data)        \
	static bool test_##n(void) { \
		return _test(id, data);  \
	}                            \
	_TEST(n);

TEST(empty, 0, "");
TEST(two_lines, 2, "1 foo\n2 bar\n");
TEST(one_without_newline, 1, "1 foo");
TEST(one_with_newline, 1, "1 foo\n");
TEST(large_int, 12, "12 foo\n");
