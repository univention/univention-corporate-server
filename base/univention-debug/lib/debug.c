/*
 * Univention Debug
 *  debug.c
 *
 * SPDX-FileCopyrightText: 2004-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#include <stdlib.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <time.h>
#include <sys/time.h>

#include <univention/debug.h>

#define UV_DEBUG_DEFAULT        UV_DEBUG_WARN

static enum uv_debug_level univention_debug_level[DEBUG_MODUL_COUNT];
static char *univention_debug_filename = NULL;
static FILE *univention_debug_file = NULL;
static enum uv_debug_flag_flush univention_debug_flush;
static enum uv_debug_flag_function univention_debug_function;

static bool univention_debug_ready = false;
static enum uv_debug_flag_structured univention_debug_structured = UV_DEBUG_UNSTRUCTURED;

static const char *const univention_debug_id_text[] = {
	"MAIN",
	"LDAP",
	"USERS",
	"NETWORK",
	"SSL",
	"SLAPD",
	"SEARCH",
	"TRANSFILE",
	"LISTENER",
	"POLICY",
	"ADMIN",
	"CONFIG",
	"LICENSE",
	"KERBEROS",
	"DHCP",
	"PROTOCOL",
	"MODULE",
	"ACL",
	"RESOURCES",
	"PARSER",
	"LOCALE",
	"AUTH",
};

static const char *const univention_debug_level_text[] = {
	"ERROR",
	"WARN",
	"PROCESS",
	"INFO",
	"ALL",
	"TRACE"
};

static const char *const univention_debug_level_structured_text[] = {
	"ERROR",
	"WARNING",
	"PROCESS",
	"INFO",
	"DEBUG",
	"TRACE"
};

#define LOG(fmt, ...) do { \
	struct timeval tv; \
	struct tm tm; \
	gettimeofday(&tv, NULL); \
	localtime_r(&tv.tv_sec, &tm); \
	if (!univention_debug_structured) { \
		fprintf(univention_debug_file, "%02d.%02d.%02d %02d:%02d:%02d.%03d  " fmt, tm.tm_mday, tm.tm_mon + 1, tm.tm_year - 100, tm.tm_hour,tm.tm_min, tm.tm_sec, (int)(tv.tv_usec / 1000), ##__VA_ARGS__); \
	} else { \
		fprintf(univention_debug_file, "%04d-%02d-%02dT%02d:%02d:%02d.%06d%c%02ld:%02ld " fmt, \
			tm.tm_year + 1900,\
			tm.tm_mon + 1,\
			tm.tm_mday,\
			tm.tm_hour,\
			tm.tm_min,\
			tm.tm_sec,\
			tv.tv_usec,\
			(tm.tm_gmtoff >= 0 ? '+' : '-'),\
			labs(tm.tm_gmtoff) / 3600,\
			(labs(tm.tm_gmtoff) % 3600) / 60, \
			##__VA_ARGS__);\
	} \
} while (0)


FILE * univention_debug_init(const char *logfile, enum uv_debug_flag_flush flush, enum uv_debug_flag_function function)
{
	int i;

	if (univention_debug_ready)
		return NULL;
	if (!logfile)
		return NULL;

	for (i=0; i<DEBUG_MODUL_COUNT; i++) {
		univention_debug_level[i] = UV_DEBUG_DEFAULT;
	}

	if (!strcmp(logfile,"stderr"))
		univention_debug_file = stderr;
	else if (!strcmp(logfile,"stdout"))
		univention_debug_file = stdout;
	else {
		if ((univention_debug_file = fopen(logfile, "a+")) == NULL) {
			fprintf(stderr, "Could not open logfile \"%s\"\n", logfile);
			return NULL;
		}
	}
	univention_debug_filename = strdup(logfile);

	univention_debug_flush = flush;
	univention_debug_function = function;

	if (univention_debug_structured) {
		LOG("%8s \n", "INIT");
	} else {
		LOG("DEBUG_INIT\n");
	}
	fflush(univention_debug_file);

	univention_debug_ready = true;

	return univention_debug_file;
}

void univention_debug(enum uv_debug_category id, enum uv_debug_level level, const char *fmt, ...)
{
	va_list ap;

	if (!univention_debug_ready)
		return;
	if (id < 0)
		return;
	if (id >= DEBUG_MODUL_COUNT)
		return;
	if (!univention_debug_file)
		return;
	if (level > univention_debug_level[id])
		return;

	if (univention_debug_structured) {
	    if (level >= UV_DEBUG_ERROR && level <= UV_DEBUG_TRACE) {
			LOG("%8s ", univention_debug_level_structured_text[level]);
		} else {
			LOG("%8d ", level);
		}
	} else {
		if (level >= UV_DEBUG_ERROR && level <= UV_DEBUG_TRACE) {
			LOG("%-11s ( %-7s ) : ", univention_debug_id_text[id], univention_debug_level_text[level]);
		} else {
			LOG("%-11s ( %-7d ) : ", univention_debug_id_text[id], level);
		}
	}
	{
		va_start(ap, fmt);
		vfprintf(univention_debug_file, fmt, ap);
		va_end(ap);
		fprintf(univention_debug_file, "\n");
		if (univention_debug_flush == UV_DEBUG_FLUSH) {
			fflush(univention_debug_file);
		}
	}
}

void univention_debug_begin(const char *s)
{
	if (!univention_debug_file)
		return;
	if (univention_debug_function != UV_DEBUG_FUNCTION)
		return;

	{
		fprintf(univention_debug_file, "UNIVENTION_DEBUG_BEGIN  : %s\n", s);
		if (univention_debug_flush == UV_DEBUG_FLUSH)
			fflush(univention_debug_file);
	}
}

void univention_debug_end(const char *s)
{
	if (!univention_debug_file)
		return;
	if (univention_debug_function != UV_DEBUG_FUNCTION)
		return;

	{
		fprintf(univention_debug_file, "UNIVENTION_DEBUG_END    : %s\n", s);
		if (univention_debug_flush == UV_DEBUG_FLUSH)
			fflush(univention_debug_file);
	}
}

void univention_debug_reopen(void)
{
	if (!univention_debug_ready)
		return;
	if (!univention_debug_filename)
		return;

	if (univention_debug_file == stderr || univention_debug_file == stdout)
		return;
	if (univention_debug_file != NULL) {
		fclose(univention_debug_file);
		univention_debug_file = NULL;
	}

	if (!strcmp(univention_debug_filename, "stderr" ))
		univention_debug_file = stderr;
	else if (!strcmp(univention_debug_filename ,"stdout"))
		univention_debug_file = stdout;
	else {
		if ((univention_debug_file = fopen(univention_debug_filename, "a+")) == NULL) {
			fprintf(stderr, "Could not open logfile \"%s\"\n", univention_debug_filename);
			return /*1*/;
		}
	}
}

void univention_debug_exit(void)
{
	if (!univention_debug_ready)
		return;

	if (univention_debug_structured) {
		LOG("%8s \n", "EXIT");
	} else {
		LOG("DEBUG_EXIT\n");
	}
	if (univention_debug_file) {
		fflush(univention_debug_file);
		if (univention_debug_file != stderr && univention_debug_file != stdout)
			fclose(univention_debug_file);
		univention_debug_file = NULL;
	}

	free(univention_debug_filename);
	univention_debug_filename = NULL;

	univention_debug_ready = false;
}

void univention_debug_set_level(enum uv_debug_category id, enum uv_debug_level level)
{
	if (id < 0)
		return;
	if (id >= DEBUG_MODUL_COUNT)
		return;

	univention_debug_level[id] = level;
}

void univention_debug_set_structured(enum uv_debug_flag_structured use_structured)
{
	univention_debug_structured = use_structured;
}

enum uv_debug_level univention_debug_get_level(enum uv_debug_category id)
{
	if (!univention_debug_ready)
		return UV_DEBUG_ERROR;
	if (id < 0)
		return UV_DEBUG_ERROR;
	if (id >= DEBUG_MODUL_COUNT)
		return UV_DEBUG_ERROR;

	return univention_debug_level[id];
}

void univention_debug_set_function(enum uv_debug_flag_function function)
{
	univention_debug_function = function;
}
