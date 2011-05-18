#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <assert.h>
#include <univention/config.h>

int main(void) {
	char key[] = "test/clib";
	char value[] = "42";
	int r;

	r = univention_config_set_string(key, value);
	assert(r == 0);

	char *c = univention_config_get_string(key);
	assert(c != NULL);
	assert(strcmp(c, value) == 0);
	free(c);

	int i = univention_config_get_int(key);
	assert(i == atoi(value));

	long l = univention_config_get_long(key);
	assert(l == atol(value));

	char *argv[] = {
		"univention-config-registry",
		"unset",
		key,
		NULL
	};
	return execv("/usr/sbin/univention-config-registry", argv);
}
