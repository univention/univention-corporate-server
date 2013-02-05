/*
 * Univention Directory Listener
 *  entries in the cache
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
#include <ctype.h>
#include <stdbool.h>
#include <string.h>
#include <ldap.h>

#include <univention/debug.h>
#include <univention/config.h>

#include "cache_entry.h"
#include "base64.h"

static bool memberUidMode;
static bool uniqueMemberMode;

/* Initialize interal setting once. */
void cache_entry_init(void)
{
	ucrval = univention_config_get_string("listener/memberuid/skip");
	if (ucrval) {
		memberUidMode |= !strcmp(ucrval, "yes") || !strcmp(ucrval, "true");
		free(ucrval);
	}
	ucrval = univention_config_get_string("listener/uniquemember/skip");
	if (ucrval) {
		uniqueMemberMode |= !strcmp(ucrval, "yes") || !strcmp(ucrval, "true");
		free(ucrval);
	}
}

int cache_free_entry(char **dn, CacheEntry *entry)
{
	int i, j;

	if (dn != NULL) {
		free(*dn);
		*dn = NULL;
	}

	if (entry->attributes) {
		for(i = 0; i < entry->attribute_count; i++) {
			if (entry->attributes[i]) {
				free(entry->attributes[i]->name);
				for (j = 0; j < entry->attributes[i]->value_count; j++)
					free(entry->attributes[i]->values[j]);
				free(entry->attributes[i]->values);
				free(entry->attributes[i]->length);
				free(entry->attributes[i]);
			}
		}
		free(entry->attributes);
		entry->attributes = NULL;
		entry->attribute_count = 0;
	}

	if (entry->modules) {
		for (i = 0; i < entry->module_count; i++)
			free(entry->modules[i]);
		free(entry->modules);
		entry->modules = NULL;
		entry->module_count = 0;
	}

	return 0;
}

int cache_dump_entry(char *dn, CacheEntry *entry, FILE *fp)
{
	int i, j;
	char **module;

	fprintf(fp, "dn: %s\n", dn);
	for (i = 0; i < entry->attribute_count; i++) {
		CacheEntryAttribute *attribute = entry->attributes[i];
		for (j = 0; j < entry->attributes[i]->value_count; j++) {
			int len = attribute->length[j] - 1;
			char *c, *value = attribute->values[j];
			for (c = value; len >= 0; c++, len--) {
				if (!isgraph(*c))
					break;
			}
			if (len >= 0) {
				char *base64_value;
				size_t srclen = attribute->length[j] - 1;
				base64_value = malloc(BASE64_ENCODE_LEN(srclen) + 1);
				if (!base64_value)
					return 1;
				base64_encode((u_char *)value, srclen, base64_value, BASE64_ENCODE_LEN(srclen) + 1);
				fprintf(fp, "%s:: %s\n", attribute->name, base64_value);
				free(base64_value);
			} else {
				fprintf(fp, "%s: %s\n", attribute->name, value);
			}
		}
	}
	for (module = entry->modules; module != NULL && *module != NULL; module++) {
		fprintf(fp, "listenerModule: %s\n", *module);
	}

	return 0;
}

int cache_entry_module_add(CacheEntry *entry, char *module)
{
	char **cur;

	for (cur = entry->modules; cur != NULL && *cur != NULL; cur++) {
		if (strcmp(*cur, module) == 0)
			return 0;
	}

	entry->modules = realloc(entry->modules, (entry->module_count + 2) * sizeof(char*));
	if (!entry->modules)
		return 1;
	entry->modules[entry->module_count++] = strdup(module);
	entry->modules[entry->module_count] = NULL;

	return 0;
}

int cache_entry_module_remove(CacheEntry *entry, char *module)
{
	char **cur;

	for (cur = entry->modules; cur != NULL && *cur != NULL; cur++) {
		if (strcmp(*cur, module) == 0)
			break;
	}

	if (cur == NULL || *cur == NULL)
		return 0;

	/* replace entry that is to be removed with last entry */
	free(*cur);
	entry->modules[cur-entry->modules] = entry->modules[entry->module_count - 1];
	entry->modules[--entry->module_count] = NULL;

	entry->modules = realloc(entry->modules, (entry->module_count + 1) * sizeof(char*));

	return 0;
}

int cache_entry_module_present(CacheEntry *entry, char *module)
{
	char **cur;

	if (entry == NULL)
		return 0;
	for (cur = entry->modules; cur != NULL && *cur != NULL; cur++) {
		if (strcmp(*cur, module) == 0)
			return 1;
	}
	return 0;
}

int cache_new_entry_from_ldap(char **dn, CacheEntry *cache_entry, LDAP *ld, LDAPMessage *ldap_entry)
{
	BerElement *ber;
	CacheEntryAttribute *c_attr;
	char *attr;
	int rv = 1;

	int i;
	char *ucrval;
	enum { DUPLICATES, UNIQUE_UID, UNIQUE_MEMBER } check;

	/* convert LDAP entry to cache entry */
	memset(cache_entry, 0, sizeof(CacheEntry));
	if (dn != NULL) {
		char *_dn = ldap_get_dn(ld, ldap_entry);
		if (*dn)
			free(*dn);
		*dn = strdup(_dn);
		ldap_memfree(_dn);
	}

	for (attr = ldap_first_attribute(ld, ldap_entry, &ber);
			attr != NULL;
			attr = ldap_next_attribute(ld, ldap_entry, ber)) {
		struct berval **val, **v;

		if ((cache_entry->attributes = realloc(cache_entry->attributes, (cache_entry->attribute_count + 2) * sizeof(CacheEntryAttribute*))) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: realloc of attributes array failed");
			goto result;
		}
		if ((c_attr = malloc(sizeof(CacheEntryAttribute))) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: malloc for CacheEntryAttribute failed");
			goto result;
		}
		c_attr->name = strdup(attr);
		c_attr->values = NULL;
		c_attr->length = NULL;
		c_attr->value_count = 0;
		cache_entry->attributes[cache_entry->attribute_count++] = c_attr;
		cache_entry->attributes[cache_entry->attribute_count] = NULL;

		if (!strcmp(c_attr->name, "memberUid"))
			check = UNIQUE_UID;
		else if (!strcmp(c_attr->name, "uniqueMember"))
			check = UNIQUE_MEMBER;
		else
			check = DUPLICATES;
		if ((val = ldap_get_values_len(ld, ldap_entry, attr)) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "ldap_get_values failed");
			goto result;
		}
		for (v = val; *v != NULL; v++) {
			if ((*v)->bv_val == NULL) {
				// check here, strlen behavior might be undefined in this case
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: ignoring bv_val of NULL with bv_len=%ld, ignoring, check attribute: %s of DN: %s", (*v)->bv_len, c_attr->name, *dn);
				goto result;
			}
			if (memberUidMode && check == UNIQUE_UID) {
				/* avoid duplicate memberUid entries https://forge.univention.org/bugzilla/show_bug.cgi?id=17998 */
				for (i = 0; i < c_attr->value_count; i++) {
					if (!memcmp(c_attr->values[i], (*v)->bv_val, (*v)->bv_len + 1) ) {
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Found a duplicate memberUid entry:");
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "DN: %s",  *dn);
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "memberUid: %s", c_attr->values[i]);
						break;
					}
				}
				/* skip this memberUid entry if listener/memberuid/skip is set to yes */
				if (i < c_attr->value_count)
					continue;
			}
			if (uniqueMemberMode && check == UNIQUE_MEMBER) {
				/* avoid duplicate uniqueMember entries https://forge.univention.org/bugzilla/show_bug.cgi?id=18692 */
				for (i = 0; i < c_attr->value_count; i++) {
					if (!memcmp(c_attr->values[i], (*v)->bv_val, (*v)->bv_len + 1)) {
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Found a duplicate uniqueMember entry:");
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "DN: %s",  *dn);
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "uniqueMember: %s", c_attr->values[i]);
						break;
					}
				}
				/* skip this uniqueMember entry if listener/uniquemember/skip is set to yes */
				if (i < c_attr->value_count)
					continue;
			}
			if ((c_attr->values = realloc(c_attr->values, (c_attr->value_count + 2) * sizeof(char*))) == NULL) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: realloc of values array failed");
				goto result;
			}
			if ((c_attr->length = realloc(c_attr->length, (c_attr->value_count + 2) * sizeof(int))) == NULL) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: realloc of length array failed");
				goto result;
			}
			if ((*v)->bv_len == strlen((*v)->bv_val)) {
				if ((c_attr->values[c_attr->value_count] = strdup((*v)->bv_val)) == NULL) {
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: strdup of value failed");
					goto result;
				}
				c_attr->length[c_attr->value_count] = strlen(c_attr->values[c_attr->value_count]) + 1;
			} else {	// in this case something is strange about the string in bv_val, maybe contains a '\0'
				// the legacy approach is to copy bv_len bytes, let's stick with this and just terminate to be safe
				if ((c_attr->values[c_attr->value_count] = malloc(((*v)->bv_len + 1) * sizeof(char))) == NULL) {
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: malloc for value failed");
					goto result;
				}
				memcpy(c_attr->values[c_attr->value_count], (*v)->bv_val, (*v)->bv_len);
				c_attr->values[c_attr->value_count][(*v)->bv_len] = '\0'; // terminate the string to be safe
				c_attr->length[c_attr->value_count] = (*v)->bv_len + 1;
			}
			c_attr->values[++c_attr->value_count] = NULL;
		}

		ldap_value_free_len(val);
		ldap_memfree(attr);
	}

	ber_free(ber, 0);
	rv = 0;

result:
	if (rv != 0)
		cache_free_entry(dn, cache_entry);

	return rv;
}

/* return list of changes attributes between new and old; the caller will
   only need to free the (char**); the strings themselves are stolen from
   the new and old entries */
char** cache_entry_changed_attributes(CacheEntry *new, CacheEntry *old)
{
	char **changes = NULL;
	int changes_count = 0;
	CacheEntryAttribute **curn, **curo;

	for (curn = new->attributes; curn != NULL && *curn != NULL; curn++) {
		for (curo = old->attributes; curo != NULL && *curo != NULL; curo++)
			if (strcmp((*curn)->name, (*curo)->name) == 0)
				break;
		if (curo != NULL && *curo != NULL && (*curn)->value_count == (*curo)->value_count) {
			int i;
			for (i = 0; i < (*curn)->value_count; i++)
				if (memcmp((*curn)->values[i], (*curo)->values[i], (*curn)->length[i]) != 0)
					break;
			if (i == (*curn)->value_count)
				continue;
		}

		changes = realloc(changes, (changes_count + 2) * sizeof(char*));
		changes[changes_count++] = (*curn)->name;
		changes[changes_count] = NULL;
	}

	for (curo = old->attributes; curo != NULL && *curo != NULL; curo++) {
		for (curn = new->attributes; curn != NULL && *curn != NULL; curn++)
			if (strcmp((*curn)->name, (*curo)->name) == 0)
				break;
		if (curn != NULL && *curn != NULL)
			continue;

		changes = realloc(changes, (changes_count + 2) * sizeof(char*));
		changes[changes_count++] = (*curo)->name;
		changes[changes_count] = NULL;
	}

	return changes;
}

int copy_cache_entry(CacheEntry *cache_entry, CacheEntry *backup_cache_entry) {
	CacheEntryAttribute **curs, **curb;
	int i;
	int rv = 1;

	memset(backup_cache_entry, 0, sizeof(CacheEntry));
	for (curs = cache_entry->attributes; curs != NULL && *curs != NULL; curs++) {
		if ((backup_cache_entry->attributes = realloc(backup_cache_entry->attributes, (backup_cache_entry->attribute_count + 2) * sizeof(CacheEntryAttribute*))) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: realloc of attributes array failed");
			goto result;
		}
		if ((backup_cache_entry->attributes[backup_cache_entry->attribute_count] = malloc(sizeof(CacheEntryAttribute))) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: malloc for CacheEntryAttribute failed");
			goto result;
		}
		curb = &backup_cache_entry->attributes[backup_cache_entry->attribute_count];
		(*curb)->name = strdup((*curs)->name);
		(*curb)->values = NULL;
		(*curb)->length = NULL;
		(*curb)->value_count = 0;
		backup_cache_entry->attributes[backup_cache_entry->attribute_count + 1] = NULL;

		for (i = 0; i < (*curs)->value_count; i++) {
			if (((*curb)->values = realloc((*curb)->values, ((*curb)->value_count + 2) * sizeof(char*))) == NULL) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: realloc of values array failed");
				goto result;
			}
			if (((*curb)->length = realloc((*curb)->length, ((*curb)->value_count + 2) * sizeof(int))) == NULL) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: realloc of length array failed");
				goto result;
			}
			if ((*curs)->length[i] == strlen((*curs)->values[i]) + 1) {
				if (((*curb)->values[(*curb)->value_count] = strdup((*curs)->values[i])) == NULL) {
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: strdup of value failed");
					goto result;
				}
				(*curb)->length[(*curb)->value_count] = strlen((*curb)->values[(*curb)->value_count]) + 1;
			} else {
				if (((*curb)->values[(*curb)->value_count] = malloc(((*curs)->length[i]) * sizeof(char))) == NULL) {
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: malloc for value failed");
					goto result;
				}
				memcpy((*curb)->values[(*curb)->value_count], (*curs)->values[i], (*curs)->length[i]);
				(*curb)->length[(*curb)->value_count] = (*curs)->length[i];
			}
			(*curb)->values[(*curb)->value_count+1] = NULL;
			(*curb)->value_count++;
		}
		backup_cache_entry->attribute_count++;
	}
	char **module_ptr;
	for (module_ptr = cache_entry->modules; module_ptr != NULL && *module_ptr != NULL; module_ptr++) {
		backup_cache_entry->modules = realloc(backup_cache_entry->modules, (backup_cache_entry->module_count + 2) * sizeof(char*));
		backup_cache_entry->modules[backup_cache_entry->module_count] = strdup(*module_ptr);
		backup_cache_entry->modules[backup_cache_entry->module_count +1] = NULL;
		backup_cache_entry->module_count++;
	}
	rv = 0;
result:
	return rv;
}

void compare_cache_entries(CacheEntry *lentry, CacheEntry *rentry)
{
	char **changes;
	char **cur;
	int i;

	changes = cache_entry_changed_attributes(lentry, rentry);

	for (cur = changes; cur != NULL && *cur != NULL; cur++) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "ALERT:     %s differs\n", *cur);

		for (i = 0; lentry->attributes != NULL && lentry->attributes[i] != NULL; i++) {
			if (strcmp(lentry->attributes[i]->name, *cur) == 0)
				break;
		}
		if (lentry->attributes == NULL || lentry->attributes[i] == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "ALERT:         lentry = []\n");
		} else {
			int j;
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "ALERT:         lentry = [");
			for (j = 0; lentry->attributes[i]->values &&
					lentry->attributes[i]->values[j] != NULL;
					j++) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, j == 0 ? "%s" : ", %s", lentry->attributes[i]->values[j]);
			}
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "]\n");
		}

		for (i = 0; rentry->attributes != NULL && rentry->attributes[i] != NULL; i++) {
			if (strcmp(rentry->attributes[i]->name, *cur) == 0)
				break;
		}
		if (rentry->attributes == NULL || rentry->attributes[i] == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "ALERT:         rentry = []\n");
		} else {
			int j;
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "ALERT:         rentry = [");
			for (j = 0; rentry->attributes[i]->values &&
					rentry->attributes[i]->values[j] != NULL;
					j++) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, j == 0 ? "%s" : ", %s", rentry->attributes[i]->values[j]);
			}
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "]\n");
		}
	}
	free(changes);

	char **curl, **curr;

	for (curl = lentry->modules; curl != NULL && *curl != NULL; curl++) {
		for (curr = rentry->modules; curr != NULL && *curr != NULL; curr++)
			if (strcmp(*curl, *curr) == 0)
				break;
		if (curr != NULL && *curr != NULL)
			continue;
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "ALERT:     module %s on lentry missing on rentry\n", *curl);
	}
	for (curr = rentry->modules; curr != NULL && *curr != NULL; curr++) {
		for (curl = lentry->modules; curl != NULL && *curl != NULL; curl++)
			if (strcmp(*curl, *curr) == 0)
				break;
		if (curl != NULL && *curl != NULL)
			continue;
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "ALERT:     module %s on rentry missing on lentry\n", *curr);
	}
}
