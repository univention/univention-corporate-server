/*
 * Univention LDAP Listener
 *  filter.c
 *
 * Copyright (C) 2004, 2005, 2006 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Binary versions of this file provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

/*
 * Functions to match LDAP filters to cache entries. Currently, we don't
 * use any schema information. However, to do this properly, we'd need to.
 */

#define _GNU_SOURCE /* for strndup */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "common.h"
#include "filter.h"

int cache_entry_match_attribute_value(char *attribute, char *value, CacheEntry *entry)
{
	CacheEntryAttribute	**a;
	char			**v;
	int			  len;
	int			  rv = 0;
	char			 *substr = NULL;
	int			  begins = 0,
				  ends = 0;
	
	for (a=entry->attributes; a != NULL && *a != NULL; a++) {
		if (strcmp((*a)->name, attribute) == 0)
			break;
	}
	if (a == NULL || *a == NULL)
		return 0;
	
	if (strcmp(value, "*") == 0)
		return 1;
	
	len = strlen(value);
	begins = value[0] == '*';
	ends = value[len-1] == '*';
	if (begins || ends)
		substr = strndup(value+begins, len-begins-ends);

	for (v=(*a)->values; v != NULL && *v != NULL; v++) {
		char *match;
		if (strcmp(*v, value) == 0) {
			rv = 1;
			break;
		} else if (substr != NULL && (match = strstr(*v, substr)) != NULL) {
			rv = (begins || match == *v) && (ends || strcmp(match, substr) == 0);
			if (rv) break;
		}
	}
	
	free(substr);
	return rv;
}

static int __cache_entry_ldap_filter_match(char* filter, int first, int last, CacheEntry *entry)
{
	/* sanity check */
	if (filter[first] != '(' || filter[last] != ')')
		return -1;
	
	if (filter[first+1] == '&' || filter[first+1] == '|' || filter[first+1] == '!') {
		int i;
		int begin = -1;
		int depth = 0;
		
		/* sanity check */
		if (filter[first+2] != '(' || filter[last-1] != ')')
			return -1;

		for (i = first+2; i <= last-1; i++) {
			if (filter[i] == '(') {
				if (begin == -1)
					begin = i;
				++depth;
			} else if (filter[i] == ')' && begin != -1) {
				int cond_is_true;
				
				--depth;
				if (depth != 0)
					continue;
				
				cond_is_true = __cache_entry_ldap_filter_match(filter, begin, i, entry);
				if (!cond_is_true && filter[first+1] == '&')
					return 0;
				else if (cond_is_true && filter[first+1] == '|')
					return 1;
				else if (filter[first+1] == '!')
					return !cond_is_true;
				
				begin = -1;
			}
		}

		if (filter[first+1] == '&')
			return 1;
		else if (filter[first+1] == '|')
			return 0;
		else /* '!', we shouldn't get here */
			return -1;
	} else {
		int type = -1; /* 0: =; 1: ~=; 2: >=; 3: <= */
		char *attr, *val;
		int i;
		int rv;
		
		for (i = first+1; i <= last-1; i++) {
			if (filter[i] == '=' && i > first+1) {
				if (filter[i-1] == '~')
					type = 1;
				else if (filter[i-1] == '>')
					type = 2;
				else if (filter[i-1] == '<')
					type = 3;
				else
					type = 0;
				break;
			}
		}
		if (type != 0) /* (type == -1) */
			return -1;

		attr = strndup(filter+first+1, i-first-1);
		val = strndup(filter+i+1, last-i-1);

		rv = cache_entry_match_attribute_value(attr, val, entry);
		
		free(attr);
		free(val);
		
		return rv;
	}

	return -1;
}

int cache_entry_ldap_filter_match(struct filter **filter, char *dn, CacheEntry *entry)
{
	struct filter **f;

	for (f = filter; f != NULL && *f != NULL; f++) {
		int len = strlen((*f)->filter);

		/* check if base and scope match */
		if ((*f)->base != NULL && (*f)->base[0] != '\0') {
			char *p = strstr(dn, (*f)->base);
		
			/* strstr only finds the first occurance of the needle in the
			 * haystack; hence, we keep on looping thru the results while
			 * the result isn't at the end of the haystack */
			while (p != NULL && p+strlen(p) != (*f)->base+strlen((*f)->base)) {
				p = strstr(p+1, (*f)->base);
			}
			if (p == NULL) /* base doesn't match at all*/
				continue;

			if ( /* scope doesn't match */
					((*f)->scope == LDAP_SCOPE_BASE && strchr(dn, ',') <= p) ||
					((*f)->scope == LDAP_SCOPE_ONELEVEL && strchr(dn, ',')+1 != p))
				continue;
		}

		
		if (__cache_entry_ldap_filter_match((*f)->filter, 0, len-1, entry))
			return 1;
	}
	return 0;
}
