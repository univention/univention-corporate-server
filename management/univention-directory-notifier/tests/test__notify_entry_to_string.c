#include "../src/notify.c"
#include <unistd.h>
#include "test.c"

static inline bool _test(NotifyId id, char *dn, char cmd, const char *expected) {
	NotifyEntry_t entry = {
		.notify_id.id = id,
		.dn = dn,
		.command = cmd,
	};

	char *str = notify_entry_to_string(entry);
	bool result = (str && expected && !strcmp(str, expected)) || (!str && !expected);

	free(str);
	return result;
}
#define TEST(n, id, dn, cmd, str)       \
	static bool test_##n(void) {        \
		return _test(id, dn, cmd, str); \
	}                                   \
	_TEST(n);

TEST(plain, 1, "dc=test", 'n', "1 dc=test n\n");
TEST(empty, 1, NULL, 'n', NULL);
