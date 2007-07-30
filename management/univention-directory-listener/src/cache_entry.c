/*
 * Univention LDAP Listener
 *  entries in the cache
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

#include <stdlib.h>
#include <ctype.h>
#include <string.h>
#include <ldap.h>

#include <univention/debug.h>

#include "cache_entry.h"
#include "base64.h"

int cache_free_entry(char **dn, CacheEntry *entry)
{
	CacheEntryAttribute **attribute;
	char **module;

	if (dn != NULL) {
		free(*dn);
		*dn = NULL;
	}
	
	for (attribute=entry->attributes; attribute != NULL && *attribute != NULL; attribute++) {
		char **value;
		free((*attribute)->name);
		for (value=(*attribute)->values; value != NULL && *value != NULL; value++) {
			free(*value);
		}
		free((*attribute)->values);
		free(*attribute);
	}
	free(entry->attributes);
	entry->attributes = NULL;
	entry->attribute_count = 0;

	for (module=entry->modules; module != NULL && *module != NULL; module++) {
		free(*module);
	}
	free(entry->modules);
	entry->modules = NULL;
	entry->module_count = 0;
	
	return 0;
}

int cache_dump_entry(char *dn, CacheEntry *entry, FILE *fp)
{
	CacheEntryAttribute **attribute;
	char **module;
	char **value;
	
	fprintf(fp, "dn: %s\n", dn);
	for (attribute=entry->attributes; attribute != NULL && *attribute != NULL; attribute++) {
		for (value=(*attribute)->values; *value != NULL; value++) {
			char *c;
			for (c=*value; *c != '\0'; c++) {
				if (!isgraph(*c))
					break;
			}
			if (*c != '\0') {
				char *base64_value;
				size_t srclen = strlen(*value);
				base64_value = malloc(BASE64_ENCODE_LEN(srclen)+1);
				base64_encode(*value, srclen, base64_value, BASE64_ENCODE_LEN(srclen)+1);
				fprintf(fp, "%s:: %s\n", (*attribute)->name, base64_value);
				free(base64_value);
			} else {
				fprintf(fp, "%s: %s\n", (*attribute)->name, *value);
			}
		}
	}
	for (module=entry->modules; module != NULL && *module != NULL; module++) {
		fprintf(fp, "listenerModule: %s\n", *module);
	}

	return 0;
}

int cache_entry_module_add(CacheEntry *entry, char *module)
{
	char **cur;

	for (cur=entry->modules; cur != NULL && *cur != NULL; cur++) {
		if (strcmp(*cur, module) == 0)
			return 0;
	}
	
	entry->modules = realloc(entry->modules, (entry->module_count+2)*sizeof(char*));
	entry->modules[entry->module_count] = strdup(module);
	entry->modules[entry->module_count+1] = NULL;
	entry->module_count++;

	return 0;
}

int cache_entry_module_remove(CacheEntry *entry, char *module)
{
	char **cur;
	
	for (cur=entry->modules; cur != NULL && *cur != NULL; cur++) {
		if (strcmp(*cur, module) == 0)
			break;
	}
	
	if (cur == NULL || *cur == NULL)
		return 0;

	/* replace entry that is to be removed with last entry */
	free(*cur);
	entry->modules[cur-entry->modules] = entry->modules[entry->module_count-1];
	entry->modules[entry->module_count-1] = NULL;
	entry->module_count--;

	entry->modules = realloc(entry->modules, (entry->module_count+1)*sizeof(char*));

	return 0;
}

int cache_entry_module_present(CacheEntry *entry, char *module)
{
	char **cur;

	if (entry == NULL)
		return 0;
	for (cur=entry->modules; cur != NULL && *cur != NULL; cur++) {
		if (strcmp(*cur, module) == 0)
			return 1;
	}
	return 0;
}

int cache_new_entry_from_ldap(char **dn, CacheEntry *cache_entry, LDAP *ld, LDAPMessage *ldap_entry)
{
	BerElement *ber;
	char *attr;
	char *_dn;
	int rv = 0;

	/* convert LDAP entry to cache entry */
	memset(cache_entry, 0, sizeof(CacheEntry));
	if (dn != NULL) {
		_dn = ldap_get_dn(ld, ldap_entry);
		*dn = strdup(_dn);
		ldap_memfree(_dn);
	}

	for (attr=ldap_first_attribute(ld, ldap_entry, &ber); attr != NULL; attr=ldap_next_attribute(ld, ldap_entry, ber)) {
		struct berval **val, **v;
	
		if ((cache_entry->attributes = realloc(cache_entry->attributes, (cache_entry->attribute_count+2)*sizeof(CacheEntryAttribute*))) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "realloc failed");
			rv = 1;
			goto result;
		}
		if ((cache_entry->attributes[cache_entry->attribute_count] = malloc(sizeof(CacheEntryAttribute))) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "malloc failed");
			rv = 1;
			goto result;
		}
		cache_entry->attributes[cache_entry->attribute_count]->name=strdup(attr);
		cache_entry->attributes[cache_entry->attribute_count]->values=NULL;
		cache_entry->attributes[cache_entry->attribute_count]->length=NULL;
		cache_entry->attributes[cache_entry->attribute_count]->value_count=0;
		cache_entry->attributes[cache_entry->attribute_count+1]=NULL;
		
		if ((val=ldap_get_values_len(ld, ldap_entry, attr)) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "ldap_get_values failed");
			rv = 1;
			goto result;
		}
		for (v = val; *v != NULL; v++) {
			if ((cache_entry->attributes[cache_entry->attribute_count]->values = realloc(cache_entry->attributes[cache_entry->attribute_count]->values, (cache_entry->attributes[cache_entry->attribute_count]->value_count+2)*sizeof(char*))) == NULL) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "realloc failed");
				rv = 1;
				goto result;
			}
			if ((cache_entry->attributes[cache_entry->attribute_count]->length = realloc(cache_entry->attributes[cache_entry->attribute_count]->length, (cache_entry->attributes[cache_entry->attribute_count]->value_count+2)*sizeof(int))) == NULL) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "realloc failed");
				rv = 1;
				goto result;
			}
			if ((*v)->bv_len != strlen((*v)->bv_val)) {
				cache_entry->attributes[cache_entry->attribute_count]->values[cache_entry->attributes[cache_entry->attribute_count]->value_count]=malloc(((*v)->bv_len+1)*sizeof(char));
				memcpy(cache_entry->attributes[cache_entry->attribute_count]->values[cache_entry->attributes[cache_entry->attribute_count]->value_count],(*v)->bv_val,(*v)->bv_len);
				cache_entry->attributes[cache_entry->attribute_count]->length[cache_entry->attributes[cache_entry->attribute_count]->value_count]=(*v)->bv_len+1;
			} else {
				cache_entry->attributes[cache_entry->attribute_count]->values[cache_entry->attributes[cache_entry->attribute_count]->value_count]=strdup((*v)->bv_val);
				cache_entry->attributes[cache_entry->attribute_count]->length[cache_entry->attributes[cache_entry->attribute_count]->value_count]=strlen(cache_entry->attributes[cache_entry->attribute_count]->values[cache_entry->attributes[cache_entry->attribute_count]->value_count])+1;
			}
			cache_entry->attributes[cache_entry->attribute_count]->values[cache_entry->attributes[cache_entry->attribute_count]->value_count+1]=NULL;
			cache_entry->attributes[cache_entry->attribute_count]->value_count++;
		}
		cache_entry->attribute_count++;

		ldap_value_free_len(val);
		ldap_memfree(attr);
	}

	ldap_memfree(ber);

result:
	if (rv != 0)
		cache_free_entry(NULL, cache_entry);
	
	return rv;
}

/* return list of changes attributes between new and old; the caller will
   only need to free the (char**); the strings themselves are stolen from
   the new and old entries */
char** cache_entry_changed_attributes(CacheEntry *new, CacheEntry *old)
{
	char **changes = NULL;
	int changes_count = 0;
	CacheEntryAttribute **cur1, **cur2;

	for (cur1 = new->attributes; cur1 != NULL && *cur1 != NULL; cur1++) {

		for (cur2 = old->attributes; cur2 != NULL && *cur2 != NULL; cur2++)
			if (strcmp((*cur1)->name, (*cur2)->name) == 0)
				break;
		if (cur2 != NULL && *cur2 != NULL && (*cur1)->value_count == (*cur2)->value_count) {
			int i;
			for (i = 0; i < (*cur1)->value_count; i++)
				if (strcmp((*cur1)->values[i], (*cur2)->values[i]) != 0)
					break;
			if (i == (*cur1)->value_count)
				continue;
		}

		changes = realloc(changes, (changes_count+2)*sizeof(char*));
		changes[changes_count] = (*cur1)->name;
		changes[changes_count+1] = NULL;
		changes_count++;
	}
	for (cur2 = old->attributes; cur2 != NULL && *cur2 != NULL; cur2++) {

		for (cur1 = new->attributes; cur1 != NULL && *cur1 != NULL; cur1++)
			if (strcmp((*cur1)->name, (*cur2)->name) == 0)
				break;
		if (cur1 != NULL && *cur1 != NULL)
			continue;

		changes = realloc(changes, (changes_count+2)*sizeof(char*));
		changes[changes_count] = (*cur2)->name;
		changes[changes_count+1] = NULL;
		changes_count++;

	}

	return changes;
}
