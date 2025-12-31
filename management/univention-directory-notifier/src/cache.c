/*
 * Univention Directory Notifier
 *  cache.c
 *
 * SPDX-FileCopyrightText: 2004-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <univention/debug.h>

#include "cache.h"
#include "notify.h"


extern unsigned long long notifier_cache_size;

static notify_cache_t *cache;
static int entry_min_pos = 0;
static int max_filled = 0;

#define MIN(x,y) (((x)<(y))?(x):(y))

int notifier_cache_init ( unsigned long max_id)
{
	unsigned int i;
	int size;
	int count = 0;
	char *buffer;

	cache = malloc( sizeof(notify_cache_t) * notifier_cache_size);
	entry_min_pos=0;

	for ( i = 0; i<notifier_cache_size; i++) {
		cache[i].dn=NULL;
		cache[i].id=0;
		cache[i].command='n';
	}

	for ( i=max_id - MIN(max_id, notifier_cache_size) + 1; i <= max_id; i++) {
		char *p, *pp;

		buffer=notify_transcation_get_one_dn ( i );
		if ( buffer == NULL ) {
			max_filled=count;
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "max_filled = %d", max_filled);
			return 1;
		}

		sscanf(buffer, "%ld", &(cache[count].id));
		cache[count].command=buffer[strlen(buffer)-1];
		p=index(buffer, ' ');
		pp=rindex(buffer, ' ');
		size=pp-p;
		cache[count].dn=malloc((size)*sizeof(char));
		memcpy( cache[count].dn, p+1, pp-p);
		cache[count].dn[size-1]='\0';

		free(buffer);
		count+=1;

	}

	max_filled=count;
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "max_filled = %d", max_filled);

	return 0;
}

void notifier_cache_free() {
	int i;
	for (i = 0; i < notifier_cache_size; i++)
		free(cache[i].dn);
	free(cache);
	cache = NULL;
}

int notifier_cache_add(unsigned long id, char *dn, char cmd)
{
	if ( dn == NULL ) {
		return 0;
	}

	if ( max_filled < (notifier_cache_size-1) ) {
		max_filled += 1;

		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "Added to cache pos %d, id %ld", max_filled, id);

		cache[max_filled].id = id;
		cache[max_filled].dn = malloc ( ( strlen(dn) + 1 ) * sizeof(char) );
		strcpy ( cache[max_filled].dn, dn );

		cache[max_filled].command = cmd;
	} else {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "Added to cache pos %d, id %ld", entry_min_pos, id);

		cache[entry_min_pos].id = id;
		free(cache[entry_min_pos].dn);
		cache[entry_min_pos].dn = malloc ( ( strlen(dn) + 1 ) * sizeof(char) );
		strcpy ( cache[entry_min_pos].dn, dn );
		cache[entry_min_pos].command = cmd;

		if ( entry_min_pos < (notifier_cache_size-1) ) {
			entry_min_pos += 1;
		} else {
			entry_min_pos = 0;
		}
	}

	return 0;
}

char* notifier_cache_get(unsigned long id)
{
	char *str;
	int i;

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "searching cache id = %ld", id);
	for(i = 0; i < max_filled; i++ ) {
		if ( cache[i].id == id ) {
			str= malloc(8192); /* FIXME */
			sprintf(str, "%ld %s %c", cache[i].id, cache[i].dn, cache[i].command);
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "string: [%s]", str);
			return str;
		}
	}

	return NULL;
}
