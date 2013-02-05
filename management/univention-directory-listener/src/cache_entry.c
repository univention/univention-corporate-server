/*
 * Univention Directory Listener
 *  entries in the cache
 *
 * Copyright 2004-2019 Univention GmbH
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
#include <assert.h>
#include <ldap.h>

#include <univention/debug.h>
#include <univention/config.h>

#include "cache_entry.h"
#include "base64.h"
#include "common.h"
#include "utils.h"

static void cache_free_attribute(CacheEntryAttribute *attr) {
	int j;

	free(attr->name);
	for (j = 0; j < attr->value_count; j++)
		free(attr->values[j]);
	free(attr->values);
	free(attr->length);
	free(attr);
}

static bool memberUidMode;
static bool uniqueMemberMode;

/* Initialize interal setting once. */
void cache_entry_init(void) {
	char *ucrval;

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

int cache_free_entry(char **dn, CacheEntry *entry) {
	int i;

	if (dn != NULL) {
		free(*dn);
		*dn = NULL;
	}

	if (entry->attributes) {
		for (i = 0; i < entry->attribute_count; i++)
			cache_free_attribute(entry->attributes[i]);
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

void cache_dump_entry(char *dn, CacheEntry *entry, FILE *fp) {
	char **module;

	fprintf(fp, "dn: %s\n", dn);
	int i, j;
	for (i = 0; i < entry->attribute_count; i++) {
		CacheEntryAttribute *attribute = entry->attributes[i];
		for (j = 0; j < entry->attributes[i]->value_count; j++) {
			char *value = entry->attributes[i]->values[j];
			char *c;
			int len = attribute->length[j] - 1;
			for (c = value; len >= 0; c++, len--) {
				if (!isgraph(*c))
					break;
			}
			if (len >= 0) {
				char *base64_value;
				size_t srclen = attribute->length[j] - 1;
				base64_value = malloc(BASE64_ENCODE_LEN(srclen) + 1);
				if (!base64_value)
					return;
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
}

int cache_entry_module_add(CacheEntry *entry, char *module) {
	char **cur;

	for (cur = entry->modules; cur != NULL && *cur != NULL; cur++) {
		if (strcmp(*cur, module) == 0)
			return 0;
	}

	entry->modules = realloc(entry->modules, (entry->module_count + 2) * sizeof(char *));
	if (!entry->modules)
		return 1;
	entry->modules[entry->module_count] = strdup(module);
	entry->modules[++entry->module_count] = NULL;

	return 0;
}

int cache_entry_module_remove(CacheEntry *entry, char *module) {
	char **cur;

	for (cur = entry->modules; cur != NULL && *cur != NULL; cur++) {
		if (strcmp(*cur, module) == 0)
			break;
	}

	if (cur == NULL || *cur == NULL)
		return 0;

	/* replace entry that is to be removed with last entry */
	free(*cur);
	entry->modules[cur - entry->modules] = entry->modules[entry->module_count - 1];
	entry->modules[--entry->module_count] = NULL;

	entry->modules = realloc(entry->modules, (entry->module_count + 1) * sizeof(char *));

	return 0;
}

int cache_entry_module_present(CacheEntry *entry, char *module) {
	char **cur;

	if (entry == NULL)
		return 0;
	for (cur = entry->modules; cur != NULL && *cur != NULL; cur++) {
		if (strcmp(*cur, module) == 0)
			return 1;
	}
	return 0;
}

int cache_new_entry_from_ldap(char **dn, CacheEntry *cache_entry, LDAP *ld, LDAPMessage *ldap_entry) {
	BerElement *ber;
	CacheEntryAttribute *c_attr;
	char *attr;
	int rv = 1;

	int i;
	enum { DUPLICATES, UNIQUE_UID, UNIQUE_MEMBER } check;
	size_t len;

	/* convert LDAP entry to cache entry */
	memset(cache_entry, 0, sizeof(CacheEntry));
	if (dn != NULL) {
		char *_dn = ldap_get_dn(ld, ldap_entry);
		if (*dn)
			free(*dn);
		*dn = strdup(_dn);
		ldap_memfree(_dn);
	}

	for (attr = ldap_first_attribute(ld, ldap_entry, &ber); attr != NULL; attr = ldap_next_attribute(ld, ldap_entry, ber)) {
		struct berval **val, **v;

		if ((cache_entry->attributes = realloc(cache_entry->attributes, (cache_entry->attribute_count + 2) * sizeof(CacheEntryAttribute *))) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: realloc of attributes array failed");
			goto result;
		}
		if ((c_attr = malloc(sizeof(CacheEntryAttribute))) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: malloc for CacheEntryAttribute failed");
			goto result;
		}
		c_attr->name = strdup(attr);
		if (!c_attr->name) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: malloc for CacheEntryAttribute.name failed");
			goto result;
		}
		c_attr->values = NULL;
		c_attr->length = NULL;
		c_attr->value_count = 0;
		cache_entry->attributes[cache_entry->attribute_count] = c_attr;
		cache_entry->attributes[++cache_entry->attribute_count] = NULL;

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
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: ignoring bv_val of NULL with bv_len=%ld, ignoring, check attribute: %s of DN: %s", (*v)->bv_len,
				                 c_attr->name, *dn);
				goto result;
			}

			if (memberUidMode && check == UNIQUE_UID) {
				/* avoid duplicate memberUid entries https://forge.univention.org/bugzilla/show_bug.cgi?id=17998 */
				for (i = 0; i < c_attr->value_count; i++) {
					if (!memcmp(c_attr->values[i], (*v)->bv_val, (*v)->bv_len + 1)) {
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Found a duplicate memberUid entry:");
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "DN: %s", *dn);
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "memberUid: %s", c_attr->values[i]);
						break;
					}
				}
				if (i < c_attr->value_count)
					continue;
			}
			if (uniqueMemberMode && check == UNIQUE_MEMBER) {
				/* avoid duplicate uniqueMember entries https://forge.univention.org/bugzilla/show_bug.cgi?id=18692 */
				for (i = 0; i < c_attr->value_count; i++) {
					if (!memcmp(c_attr->values[i], (*v)->bv_val, (*v)->bv_len + 1)) {
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Found a duplicate uniqueMember entry:");
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "DN: %s", *dn);
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "uniqueMember: %s", c_attr->values[i]);
						break;
					}
				}
				if (i < c_attr->value_count)
					continue;
			}
			if (!(c_attr->length = realloc(c_attr->length, (c_attr->value_count + 2) * sizeof(int)))) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: realloc of length array failed");
				goto result;
			}
			if (!(c_attr->values = realloc(c_attr->values, (c_attr->value_count + 2) * sizeof(char *)))) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: realloc of values array failed");
				goto result;
			}
			len = (*v)->bv_len;
			if (!(c_attr->values[c_attr->value_count] = malloc(len + 1))) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_new_entry_from_ldap: malloc for value failed");
				goto result;
			}
			c_attr->length[c_attr->value_count] = len + 1;
			memcpy(c_attr->values[c_attr->value_count], (*v)->bv_val, len);
			c_attr->values[c_attr->value_count][len] = '\0';
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
char **cache_entry_changed_attributes(CacheEntry *new, CacheEntry *old) {
	char **changes = NULL;
	int changes_count = 0;
	CacheEntryAttribute **curn, **curo;

	for (curn = new->attributes; curn != NULL &&*curn != NULL; curn++) {
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

		changes = realloc(changes, (changes_count + 2) * sizeof(char *));
		changes[changes_count] = (*curn)->name;
		changes[++changes_count] = NULL;
	}

	for (curo = old->attributes; curo != NULL && *curo != NULL; curo++) {
		for (curn = new->attributes; curn != NULL &&*curn != NULL; curn++)
			if (strcmp((*curn)->name, (*curo)->name) == 0)
				break;
		if (curn != NULL && *curn != NULL)
			continue;

		changes = realloc(changes, (changes_count + 2) * sizeof(char *));
		changes[changes_count] = (*curo)->name;
		changes[++changes_count] = NULL;
	}

	return changes;
}

int copy_cache_entry(CacheEntry *src, CacheEntry *dst) {
	int rv = 1;

	memset(dst, 0, sizeof(CacheEntry));

	int a, a_count = src->attribute_count;
	if (!(dst->attributes = calloc(a_count + 1, sizeof(CacheEntryAttribute *)))) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: malloc of attributes array failed");
		goto result;
	}
	for (a = 0; a < a_count; a++) {
		CacheEntryAttribute *a_dst, *a_src = src->attributes[a];
		int v, v_count = a_src->value_count;

		if ((a_dst = malloc(sizeof(CacheEntryAttribute))) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: malloc for CacheEntryAttribute failed");
			goto result;
		}
		memset(a_dst, 0, sizeof(CacheEntryAttribute));
		dst->attributes[a] = a_dst;

		if (!(a_dst->name = strdup(a_src->name))) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: strdup for CacheEntryAttribute.name failed");
			goto result;
		}

		a_dst->value_count = v_count;
		if (!(a_dst->values = calloc(a_dst->value_count + 1, sizeof(char *)))) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: realloc of values array failed");
			goto result;
		}
		if (!(a_dst->length = calloc(a_dst->value_count + 1, sizeof(int)))) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: realloc of length array failed");
			goto result;
		}
		for (v = 0; v < v_count; v++) {
			char *v_dst, *v_src = a_src->values[v];
			int len = a_src->length[v];

			if (!(v_dst = malloc(len))) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: malloc of value failed");
				goto result;
			}
			memcpy(v_dst, v_src, len);
			a_dst->values[v] = v_dst;
			a_dst->length[v] = len;
		}
		a_dst->values[v] = NULL;
	}
	dst->attributes[a] = NULL;

	int m, m_count = src->module_count;
	if (!(dst->modules = calloc(m_count + 1, sizeof(char *)))) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: malloc of module array failed");
		goto result;
	}
	for (m = 0; m < m_count; m++) {
		if (!(dst->modules[m] = strdup(src->modules[m]))) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "copy_cache_entry: strdup of module failed");
			goto result;
		}
	}
	dst->modules[m] = NULL;

	rv = 0;
result:
	return rv;
}

const char *cache_entry_get1(CacheEntry *entry, const char *key) {
	int i;

	for (i = 0; i < entry->attribute_count; i++) {
		CacheEntryAttribute *attr = entry->attributes[i];

		if (STRNEQ(attr->name, key))
			continue;
		assert(attr->value_count == 1);
		return attr->values[0];
	}
	return NULL;
}

void cache_entry_set1(CacheEntry *entry, const char *key, const char *value) {
	int i;

	for (i = 0; i < entry->attribute_count; i++) {
		CacheEntryAttribute *attr = entry->attributes[i];

		if (STRNEQ(attr->name, key))
			continue;
		assert(attr->value_count == 1);
		free(attr->values[0]);
		attr->values[0] = strdup(value);
		assert(attr->values[0]);
		attr->length[0] = strlen(value) + 1;
		return;
	}
	cache_entry_add1(entry, key, value);
}

static CacheEntryAttribute *_cache_entry_find_attribute(CacheEntry *entry, LDAPAVA *ava) {
	int att;
	for (att = 0; att < entry->attribute_count; att++) {
		CacheEntryAttribute *attr = entry->attributes[att];
		if (BERSTREQ(&ava->la_attr, attr->name, strlen(attr->name)))
			return attr;
	}
	return NULL;
}
static CacheEntryAttribute *_cache_entry_force_value(CacheEntryAttribute *attr, LDAPAVA *ava) {
	void *tmp;

	attr->value_count = 0;

	tmp = realloc(attr->values, (attr->value_count + 2) * sizeof(char *));
	if (!tmp) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s:%d realloc() failed", __FILE__, __LINE__);
		return NULL;
	}
	attr->values = tmp;

	tmp = realloc(attr->length, (attr->value_count + 2) * sizeof(int));
	if (!tmp) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s:%d realloc() failed", __FILE__, __LINE__);
		return NULL;
	}
	attr->length = tmp;

	attr->length[attr->value_count] = BER2STR(&ava->la_value, &attr->values[attr->value_count]) + 1;
	if (!attr->values[attr->value_count]) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s:%d BER2STR() failed", __FILE__, __LINE__);
		return NULL;
	}
	attr->value_count++;
	attr->length[attr->value_count] = 0;
	attr->values[attr->value_count] = NULL;
	return attr;
}
static CacheEntryAttribute *_cache_entry_add_new_attribute(CacheEntry *entry, LDAPAVA *ava) {
	CacheEntryAttribute *attr = malloc(sizeof(CacheEntryAttribute));
	if (!attr) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s:%d malloc() failed", __FILE__, __LINE__);
		return NULL;
	}
	memset(attr, 0, sizeof(CacheEntryAttribute));

	void *tmp = realloc(entry->attributes, (entry->attribute_count + 2) * sizeof(CacheEntryAttribute *));
	if (!tmp) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s:%d realloc() failed", __FILE__, __LINE__);
		goto error;
	}
	entry->attributes = tmp;

	BER2STR(&ava->la_attr, &attr->name);
	if (!&attr->name) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s:%d BER2STR() failed", __FILE__, __LINE__);
		goto error;
	}
	if (!_cache_entry_force_value(attr, ava))
		goto error;

	entry->attributes[entry->attribute_count] = attr;
	entry->attributes[++entry->attribute_count] = NULL;

	return attr;
error:
	cache_free_attribute(attr);
	return NULL;
}
CacheEntryAttribute *cache_entry_update_rdn1(CacheEntry *entry, LDAPAVA *ava) {
	CacheEntryAttribute *attr = _cache_entry_find_attribute(entry, ava);
	if (attr == NULL)
		attr = _cache_entry_add_new_attribute(entry, ava);
	else
		attr = _cache_entry_force_value(attr, ava);

	return attr;
}
void cache_entry_update_rdn(struct transaction *trans, LDAPRDN new_dn) {
	int rdn;
	CacheEntry *entry = &trans->cur.cache;

	for (rdn = 0; new_dn[rdn]; rdn++)
		cache_entry_update_rdn1(entry, new_dn[rdn]);
}

CacheEntryAttribute *cache_entry_add1(CacheEntry *entry, const char *key, const char *value) {
	LDAPAVA ava = {
	    .la_attr = {
	        .bv_val = (char *)key, .bv_len = strlen(key),
	    },
	    .la_value = {
	        .bv_val = (char *)value, .bv_len = strlen(value),
	    },
	};
	return _cache_entry_add_new_attribute(entry, &ava);
}
