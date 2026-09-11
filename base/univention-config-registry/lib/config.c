/*
 * Univention Configuration Registry
 *  C library for univention config registry
 *
 * SPDX-FileCopyrightText: 2004-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <unistd.h>
#ifndef __USE_GNU
# define __USE_GNU
#endif
#include <string.h>
#include <stdbool.h>
#include <sys/wait.h>

#include <univention/config.h>
#include <univention/debug.h>

#define MAX_RECURSION 10

#define VARIABLE_TOKEN "@%@"
#define VARIABLE_TOKEN_LEN (strlen(VARIABLE_TOKEN))

enum SCOPE { CUSTOM, FORCED, SCHEDULE, LDAP, NORMAL, DEFAULT };
static const char *LAYERS[] = {
	[CUSTOM] = NULL,
	[FORCED] = "/etc/univention/base-forced.conf",
	[SCHEDULE] = "/etc/univention/base-schedule.conf",
	[LDAP] = "/etc/univention/base-ldap.conf",
	[NORMAL] = "/etc/univention/base.conf",
	[DEFAULT] = "/etc/univention/base-defaults.conf",
};
#define ARRAY_SIZE(A) (sizeof (A) / sizeof ((A)[0]))

static char *replace_variable_patterns(char *key, int recursion);

typedef int (*_layer_cb)(const char *key, const char *value, enum SCOPE scope, int recursion, void *userdata);

static void _iter_all_layers(const char *prefix, _layer_cb cb, int recursion, void *userdata)
{
	FILE *file;
	char *line = NULL;
	size_t prefix_len = prefix ? strlen(prefix) : 0;
	enum SCOPE i;
	size_t line_capacity = 0;

	for (i = 0; i < ARRAY_SIZE(LAYERS); i++) {
		const char *name = i ? LAYERS[i] : getenv("UNIVENTION_BASECONF");
		if (!name)
			continue;

		if ((file = fopen(name, "re")) == NULL)
		{
			univention_debug(UV_DEBUG_CONFIG, UV_DEBUG_ERROR, "Error on opening \"%s\"", LAYERS[i]);
			continue;
		}

		while (getline(&line, &line_capacity, file) != -1)
		{
			char *colon;
			char *value;
			size_t vlen;

			/* prefix filter - NULL or empty string means match all */
			if (prefix_len && strncmp(line, prefix, prefix_len) != 0)
				continue;

			colon = strstr(line, ": ");
			if (!colon)
				continue;

			*colon = '\0';
			value = colon + 2;  /* skip ": " */

			/* trim trailing newline */
			vlen = strlen(value);
			while (vlen > 0) {
				switch (value[vlen - 1]) {
					case '\n':
					case '\r':
						value[--vlen] = '\0';
						continue;
				}
				break;
			}

			if (cb(line, value, i, recursion, userdata)) {
				free(line);
				fclose(file);
				return;
			}
		}

		fclose(file);
	}
	free(line);
}

static int _get_variable_cb(const char *key, const char *value, enum SCOPE scope, int recursion, void *userdata)
{
	char **result = userdata;

	*result = strndup(value, strlen(value));
	if (scope == DEFAULT && *result)
		*result = replace_variable_patterns(*result, recursion);

	return 1;  /* stop after first match */
}

static char *_get_variable(const char *key, int recursion)
{
	char *result = NULL;
	int len;
	char *prefix;

	len = asprintf(&prefix, "%s: ", key);
	if (len < 0)
		return NULL;

	_iter_all_layers(prefix, _get_variable_cb, recursion, &result);

	if (!result)
		univention_debug(UV_DEBUG_USERS, UV_DEBUG_INFO, "Did not find \"%s\"", key);

	free(prefix);

	return result;
}

char *univention_config_get_string(const char *key)
{
	return _get_variable(key, MAX_RECURSION);
}

static char *replace_variable_patterns(char *key, int recursion)
{
	char *start, *end, *result = key, *next = key;

	if (!key)
		return NULL;

	while (recursion > 0 && (start = strstr(next, VARIABLE_TOKEN)) && (end = strstr(start + VARIABLE_TOKEN_LEN, VARIABLE_TOKEN)))
	{
		*start = *end = '\0';

		char *content = _get_variable(start + VARIABLE_TOKEN_LEN, recursion - 1);
		int ret = asprintf(&result, "%s%s%s", key, content ? content : "", end + VARIABLE_TOKEN_LEN);
		free(content);
		free(key);
		if (ret < 0) {
			univention_debug(UV_DEBUG_CONFIG, UV_DEBUG_ERROR, "asprintf() failed");
			result = NULL;
			break;
		}
		next = result + (start - key) + (content ? strlen(content) : 0);
		key = result;
	}

	return result;
}

int univention_config_get_int(const char *key)
{
	int ret = -1;
	char *s = univention_config_get_string(key);
	if (s) {
		ret = atoi(s);
		free(s);
	}
	return ret;
}

long univention_config_get_long(const char *key)
{
	long ret = -1;
	char *s = univention_config_get_string(key);
	if (s) {
		ret = atol(s);
		free(s);
	}
	return ret;
}

int univention_config_set_string(const char *key, const char *value)
{
	size_t len;
	char *str;
	int pid, status;

	len = strlen(key) + strlen(value) + 2;
	str = malloc(len);
	if (!str)
		return -1;
	snprintf(str, len, "%s=%s", key, value);

	pid = fork();
	if (pid == -1)
		return -1;
	if (pid == 0) {
		/* child */
		char *const argv[] = {
			"univention-config-registry",
			"set",
			str,
			NULL
		};
		execve("/usr/sbin/univention-config-registry", argv, NULL);
		exit(127);
	}
	/* parent */
	do {
		if (waitpid(pid, &status, 0) == -1) {
			if (errno != EINTR)
				return -1;
		} else
			return status;
	} while(1);

	return 0;
}

bool univention_config_is_true(const char *key, bool default_value)
{
	char *s = univention_config_get_string(key);
	if (s == NULL) {
		return default_value;
	}
	return !strcasecmp(s, "yes") || !strcasecmp(s, "true") || !strcmp(s, "1") || !strcasecmp(s, "enable") || !strcasecmp(s, "enabled") || !strcasecmp(s, "on");
}

/* State for univention_config_iterate_prefix callback */
struct _prefix_iter_state {
	const char *prefix;
	size_t prefix_len;
	void (*callback)(const char *key, const char *value, void *userdata);
	void *userdata;
	char **seen;
	size_t seen_count;
	size_t seen_cap;
	int recursion;
};

static int _prefix_iter_seen(struct _prefix_iter_state *state, const char *key)
{
	size_t i;
	for (i = 0; i < state->seen_count; i++) {
		if (strcmp(state->seen[i], key) == 0)
			return 1;
	}
	return 0;
}

static void _prefix_iter_mark_seen(struct _prefix_iter_state *state, const char *key)
{
	if (state->seen_count >= state->seen_cap) {
		state->seen_cap = state->seen_cap ? state->seen_cap * 2 : 16;
		state->seen = realloc(state->seen, state->seen_cap * sizeof(char *));
	}
	state->seen[state->seen_count++] = strdup(key);
}

static int _prefix_iter_cb(const char *key, const char *value, enum SCOPE scope, int recursion, void *userdata)
{
	struct _prefix_iter_state *state = userdata;

	if (_prefix_iter_seen(state, key))
		return 0;  /* skip but continue - more keys may follow */

	_prefix_iter_mark_seen(state, key);

	char *result = strndup(value, strlen(value));
	if (scope == DEFAULT && result)
		result = replace_variable_patterns(result, recursion);

	state->callback(key, result, state->userdata);
	free(result);

	return 0;  /* always continue - we want all matching keys */
}

void univention_config_iterate_prefix(
	const char *prefix,
	void (*callback)(const char *key, const char *value, void *userdata),
	void *userdata
) {
	struct _prefix_iter_state state = {
		.prefix = prefix,
		.prefix_len = prefix ? strlen(prefix) : 0,
		.callback = callback,
		.userdata = userdata,
		.seen = NULL,
		.seen_count = 0,
		.seen_cap = 0,
		.recursion = MAX_RECURSION,
	};

	_iter_all_layers(prefix, _prefix_iter_cb, MAX_RECURSION, &state);

	size_t i;
	for (i = 0; i < state.seen_count; i++)
		free(state.seen[i]);
	free(state.seen);
}

void univention_config_iterate(
    void (*callback)(const char *key, const char *value, void *userdata),
    void *userdata
) {
    univention_config_iterate_prefix("", callback, userdata);
}
