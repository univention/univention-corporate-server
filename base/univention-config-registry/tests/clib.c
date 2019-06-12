#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <assert.h>
#include <univention/config.h>
#include <sys/types.h>
#include <sys/wait.h>

static char ucr_bin[] = "/usr/sbin/univention-config-registry";
static char ucr_name[] = "univention-config-registry";
static char key[] = "test/clib";
static char *LAYER[] = {
	"--ldap-policy",
	"--schedule",
	"--force",
	NULL,
};

int fork_exec(char *const *argv) {
	pid_t pid;
	int status;

	pid = fork();
	switch (pid) {
	case -1: // error
		abort();

	case 0: // child
		return execv(ucr_bin, argv);

	default: // parent
		pid = wait(&status);
		assert(WIFEXITED(status) && WEXITSTATUS(status) == 0);
		return 0;
	}
}

void test_layer(void) {
	char assign[64];
	int r, layer;

	for (layer = 0; LAYER[layer]; layer++) {
		size_t size;

		size = snprintf(assign, sizeof assign, "%s=%s", key, LAYER[layer]);
		assert(0 < size && size < sizeof assign);
		char *const argv[] = {
			ucr_name,
			"set",
			LAYER[layer],
			assign,
			NULL
		};
		fprintf(stderr, "set %s %s\n", LAYER[layer], assign);
		fork_exec(argv);

		char *c = univention_config_get_string(key);
		fprintf(stderr, "should=%s is=%s\n", LAYER[layer], c);
		r = strcmp(c, LAYER[layer]);
		assert(r == 0);
	}

	for (layer = 0; LAYER[layer]; layer++) {
		char *const argv[] = {
			ucr_name,
			"unset",
			LAYER[layer],
			key,
			NULL
		};
		fprintf(stderr, "unset %s %s\n", LAYER[layer], key);
		fork_exec(argv);
	}
}

int main(void) {
	char value[] = "42";
	int r;

	r = univention_config_set_string(key, value);
	fprintf(stderr, "set %s=%s [%d]\n", key, value, r);
	assert(r == 0);

	char *c = univention_config_get_string(key);
	fprintf(stderr, "get_str %s=%s\n", key, c);
	assert(c != NULL);
	assert(strcmp(c, value) == 0);
	free(c);

	int i = univention_config_get_int(key);
	fprintf(stderr, "get_int %s=%d\n", key, i);
	assert(i == atoi(value));

	long l = univention_config_get_long(key);
	fprintf(stderr, "get_long %s=%ld\n", key, l);
	assert(l == atol(value));

	test_layer();

	char *const argv[] = {
		ucr_name,
		"unset",
		key,
		NULL
	};
	fprintf(stderr, "unset %s\n", key);
	return execv(ucr_bin, argv);
}
