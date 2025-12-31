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

#define BASECONFIG_MAX_LINE 1024
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

static char *_get_variable(const char *key, int recursion)
{
	FILE *file;
	char line[BASECONFIG_MAX_LINE];
	char *nvalue;
	int len;
	char *ret = NULL;
	enum SCOPE i;

	len = asprintf(&nvalue, "%s: ", key);
	if (len < 0)
		return ret;

	for (i = 0; i < ARRAY_SIZE(LAYERS); i++) {
		const char *name = i ? LAYERS[i] : getenv("UNIVENTION_BASECONF");
		if (!name)
			continue;

		if ((file = fopen(name, "re")) == NULL)
		{
			univention_debug(UV_DEBUG_CONFIG, UV_DEBUG_ERROR, "Error on opening \"%s\"", LAYERS[i]);
			continue;
		}

		while (fgets(line, BASECONFIG_MAX_LINE, file) != NULL)
		{
			if (!strncmp(line, nvalue, len))
			{
				char *value;
				size_t vlen;

				value = line + len; // skip key
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
				ret = strndup(value, vlen);
				fclose(file);
				if (recursion > 0 && i == DEFAULT)
					ret = replace_variable_patterns(ret, recursion);

				goto done;
			}
		}

		fclose(file);
	}

	univention_debug(UV_DEBUG_USERS, UV_DEBUG_INFO, "Did not find \"%s\"", key);
done:
	free(nvalue);
	return ret;
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
