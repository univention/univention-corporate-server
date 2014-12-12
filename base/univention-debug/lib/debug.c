/*
 * Univention Debug
 *  debug.c
 *
 * Copyright 2004-2012 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
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

static enum uv_debug_level *univention_debug_level;
static const char *univention_debug_filename = NULL;
static FILE *univention_debug_file = NULL;
static enum uv_debug_flag_flush univention_debug_flush;
static enum uv_debug_flag_function univention_debug_function;

static bool univention_debug_ready = false;

static const char *univention_debug_id_text[] = {
	"MAIN       ",
	"LDAP       ",
	"USERS      ",
	"NETWORK    ",
	"SSL        ",
	"SLAPD      ",
	"SEARCH     ",
	"TRANSFILE  ",
	"LISTENER   ",
	"POLICY     ",
	"ADMIN      ",
	"CONFIG     ",
	"LICENSE    ",
	"KERBEROS   ",
	"DHCP       ",
	"PROTOCOL   ",
	"MODULE     ",
	"ACL        ",
	"RESOURCES  ",
	"PARSER     ",
	"LOCALE     ",
	"AUTH       ",
};

static const char *univention_debug_level_text[] = {
	"( ERROR   ) : ",
	"( WARN    ) : ",
	"( PROCESS ) : ",
	"( INFO    ) : ",
	"( ALL     ) : "
};

FILE * univention_debug_init(const char *logfile, enum uv_debug_flag_flush flush, enum uv_debug_flag_function function)
{
	int i;
	struct timeval tv;
	struct tm tm;

	if (univention_debug_ready) {
		return NULL;
	}

	univention_debug_level = malloc(DEBUG_MODUL_COUNT * sizeof(int));
	if (univention_debug_level == NULL) {
		fprintf(stderr, "Could not initialize univention_debug!\n");
		return NULL;
	}

	for (i=0; i<DEBUG_MODUL_COUNT; i++) {
		univention_debug_level[i] = UV_DEBUG_DEFAULT;
	}

	if (!strcmp(logfile,"stderr"))
		univention_debug_file = stderr;
	else if (!strcmp(logfile,"stdout"))
		univention_debug_file = stdout;
	else if (logfile != NULL) {
		if ((univention_debug_file = fopen(logfile, "a+")) == NULL) {
			free(univention_debug_level);
			univention_debug_level = NULL;
			fprintf(stderr, "Could not open logfile \"%s\"\n", logfile);
			return NULL;
		}
	}
	univention_debug_filename = logfile ? strdup(logfile) : NULL;

	univention_debug_flush = flush;
	univention_debug_function = function;

	gettimeofday( &tv, NULL );
	localtime_r(&tv.tv_sec, &tm);

	fprintf(univention_debug_file, "%02d.%02d.%02d %02d:%02d:%02d.%03d  DEBUG_INIT\n", tm.tm_mday, tm.tm_mon+1, tm.tm_year-100, tm.tm_hour,tm.tm_min, tm.tm_sec, ( int ) ( tv.tv_usec / 1000 ) );
	fflush(univention_debug_file);

	univention_debug_ready = true;

	return univention_debug_file;
}

void univention_debug(enum uv_debug_category id, enum uv_debug_level level, const char *fmt, ...)
{
	va_list ap;
	struct tm tm;
	struct timeval tv;

	if (!univention_debug_ready || id < 0 || id >= DEBUG_MODUL_COUNT)
		return;
	if (univention_debug_file && level <= univention_debug_level[id]) {
		gettimeofday( &tv, NULL );
		localtime_r( &tv.tv_sec, &tm );
		fprintf(univention_debug_file,
				"%02d.%02d.%02d %02d:%02d:%02d.%03d  %s %s",
				tm.tm_mday, tm.tm_mon+1, tm.tm_year-100,
				tm.tm_hour, tm.tm_min, tm.tm_sec, ( int ) (tv.tv_usec / 1000 ),
				univention_debug_id_text[id],
				univention_debug_level_text[level]);
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
	if (univention_debug_file && univention_debug_function == UV_DEBUG_FUNCTION) {
		fprintf(univention_debug_file, "UNIVENTION_DEBUG_BEGIN  : %s\n", s);
		if (univention_debug_flush == UV_DEBUG_FLUSH)
			fflush(univention_debug_file);
	}
}

void univention_debug_end(const char *s)
{
	if (univention_debug_file && univention_debug_function == UV_DEBUG_FUNCTION) {
		fprintf(univention_debug_file, "UNIVENTION_DEBUG_END    : %s\n", s);
		if (univention_debug_flush == UV_DEBUG_FLUSH)
			fflush(univention_debug_file);
	}
}

void univention_debug_reopen(void)
{
	if (!univention_debug_ready) {
		return;
	}

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
	else if (univention_debug_filename != NULL) {
		if ((univention_debug_file = fopen(univention_debug_filename, "a+")) == NULL) {
			fprintf(stderr, "Could not open logfile \"%s\"\n", univention_debug_filename);
			return /*1*/;
		}
	}
}

void univention_debug_exit(void)
{
	struct timeval tv;
	struct tm tm;

	if (!univention_debug_ready) {
		return;
	}

	gettimeofday( &tv, NULL );
	localtime_r(&tv.tv_sec, &tm);

	fprintf(univention_debug_file, "%02d.%02d.%02d %02d:%02d:%02d.%03d  DEBUG_EXIT\n", tm.tm_mday, tm.tm_mon+1, tm.tm_year-100, tm.tm_hour,tm.tm_min, tm.tm_sec, ( int ) ( tv.tv_usec / 1000 ) );
	fflush(univention_debug_file);
	fclose(univention_debug_file);
	univention_debug_file = NULL;

	free(univention_debug_filename);
	univention_debug_filename = NULL;

	free(univention_debug_level);
	univention_debug_level = NULL;

	univention_debug_ready = false;
}

void univention_debug_set_level(enum uv_debug_category id, enum uv_debug_level level)
{
	if (!univention_debug_ready || id < 0 || id >= DEBUG_MODUL_COUNT)
		return;
	univention_debug_level[id] = level;
}

enum uv_debug_level univention_debug_get_level(enum uv_debug_category id)
{
	if (!univention_debug_ready || id < 0 || id >= DEBUG_MODUL_COUNT)
		return UV_DEBUG_ERROR;
	return univention_debug_level[id];
}

void univention_debug_set_function(enum uv_debug_flag_function function)
{
	univention_debug_function = function;
}
