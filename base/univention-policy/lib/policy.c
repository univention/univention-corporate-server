/*
 * Univention Policy
 *  C source of the univention policy library
 *
 * Copyright 2003-2019 Univention GmbH
 *
 * https://www.univention.de/
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
 * <https://www.gnu.org/licenses/>.
 */

#include <ldap.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>

#include <univention/debug.h>

#include "internal.h"

/** Deep-free univention_policy_result. */
static void univention_policy_result_free(struct univention_policy_result_s *o) {
	if (o) {
		FREE(o->policy_dn);
		while (o->count-- > 0)
			FREE(o->values[o->count]);
		FREE(o->values);
		FREE(o);
	}
}

/** Deep-free univention_policy_attribute_list. */
static void univention_policy_attribute_list_free(struct univention_policy_attribute_list_s *o) {
	if (o) {
		if (o->values) {
			univention_policy_result_free(o->values);
		}
		FREE(o->name);
		FREE(o);
	}
}

/** Deep-free univention_policy_list. */
static void univention_policy_list_free(struct univention_policy_list_s *o) {
	if (o) {
		struct univention_policy_attribute_list_s *cur, *next;
		FREE(o->name);
		for (cur = o->attributes; cur != NULL; cur = next) {
			next = cur->next;
			univention_policy_attribute_list_free(cur);
		}
		FREE(o);
	}
}

/** Debug print dn. **/
static void dprint_dn(LDAP *ld, LDAPMessage *entry) {
	char *l_dn;
	if ((l_dn = ldap_get_dn(ld, entry)) != NULL) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ALL, "DN: %s", l_dn);
		ldap_memfree(l_dn);
	}
}

/*
 * returns parent dn of dn, NULL if dn doesn't have any parents
 */
static const char *parent_dn(const char *dn)
{
	char* pdn = strchr(dn, ',');
	if (pdn != NULL)
		++pdn;
	return pdn;
}

/*
 * returns object from list if it already exists, create new object otherwise
 */
static struct univention_policy_list_s* univention_policy_list_get(struct univention_policy_list_s** list, const char *name)
{
	struct univention_policy_list_s *new;
	struct univention_policy_list_s *cur;

	for (cur = *list; cur != NULL; cur = cur->next) {
		if (strcmp(cur->name, name) == 0)
			return cur;
	}

	/* policy not found: create new object */
	univention_debug(UV_DEBUG_POLICY, UV_DEBUG_ALL, "policy entry not found, creating new one");
	if ((new = malloc(sizeof(struct univention_policy_list_s))) == NULL)
		return NULL;
	new->name = strdup(name);
	new->attributes = NULL;

	new->next = *list;
	*list = new;

	return new;
}

/*
 * returns object from list if it already exists, create new object otherwise
 */
static struct univention_policy_attribute_list_s* univention_policy_attribute_list_get(struct univention_policy_attribute_list_s **list, const char *name)
{
	struct univention_policy_attribute_list_s *new;
	struct univention_policy_attribute_list_s *cur;

	for (cur = *list; cur != NULL; cur = cur->next) {
		if (strcmp(cur->name, name) == 0)
			return cur;
	}

	/* policy not found: create new object */
	univention_debug(UV_DEBUG_POLICY, UV_DEBUG_ALL, "attribute entry not found, creating new one");
	if ((new = malloc(sizeof(struct univention_policy_attribute_list_s))) == NULL)
		return NULL;
	new->name = strdup(name);
	new->values = NULL;

	new->next = *list;
	*list = new;

	return new;
}

#if 0 /* unused */
/*
 * Remove object from list if it exists.
 */
static void univention_policy_attribute_list_remove(struct univention_policy_attribute_list_s** list, const char *name)
{
	struct univention_policy_attribute_list_s **cur = list;
	while (*cur != NULL) {
		struct univention_policy_attribute_list_s *o = *cur;
		if (strcmp(o->name, name) == 0) {
			*cur = o->next;
			univention_policy_attribute_list_free(o);
		} else
			cur = &((*cur)->next);
	}
}
#endif

/** Check if object_classes contains object_class. */
static bool in_string_array(char **object_classes, const char *object_class)
{
	int i;
	if (object_classes == NULL)
		return false;
	for (i = 0; object_classes[i] != NULL; i++)
		if (strcasecmp(object_classes[i], object_class) == 0)
			return true;
	return false;
}

#if 0 /* unused */
static void print_string_array(char **object_classes)
{
	int i;
	for (i = 0; object_classes[i] != NULL; i++)
		printf("%s\n", object_classes[i]);
}
#endif

/* clean up handle by removing empty attributes. */
static void univention_policy_cleanup(univention_policy_handle_t* handle)
{
	struct univention_policy_list_s* policy;
	for (policy = handle->policies; policy != NULL; policy = policy->next) {
		struct univention_policy_attribute_list_s **cur = &policy->attributes;
		while (*cur != NULL) {
			struct univention_policy_attribute_list_s *o = *cur;
			if (o->values == NULL || o->values->values == NULL) {
				*cur = o->next;
				univention_policy_attribute_list_free(o);
			} else
				cur = &((*cur)->next);
		}
	}
}

/* Retrieve policy 'dn' */
static void univention_policy_merge(LDAP *ld, const char *dn, univention_policy_handle_t *handle, char **object_classes, const char *objectdn)
{
	int		rc;
	LDAPMessage	*res;
	struct  timeval	timeout = {.tv_sec=10, .tv_usec=0};

	univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "considering policy: %s", dn);

	rc = ldap_search_ext_s(ld, dn, LDAP_SCOPE_BASE, "(objectClass=univentionPolicy)", NULL, 0, NULL, NULL, &timeout, 0, &res);
	if (rc == LDAP_NO_SUCH_OBJECT) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "Not found");
	} else if (rc != LDAP_SUCCESS) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "ldap_search_ext_s returned ERROR");
	} else {
		LDAPMessage	*entry;

		/* BASE search returns at most one entry. */
		for (entry = ldap_first_entry(ld, res);
			 entry != NULL;
			 entry = ldap_next_entry(ld, entry)) {

			struct univention_policy_list_s *policy = NULL;
			char **fixed_attributes = NULL;
			char **empty_attributes = NULL;
			struct berval **vals;
			bool apply = true;
			int i;

			dprint_dn(ld, entry);

			/* iterate over attributes of policy and parse general policy attributes. */
			if ((vals = ldap_get_values_len(ld, entry, "objectClass")) != NULL) {
				for (i = 0; (vals[i] != NULL && vals[i]->bv_val != NULL); i++) {
					/* bv_val is "umcPolicy" or "univentionMailQuota" or
					   bv_val starts with "univentionPolicy" but is not "univentionPolicy" */
					if (!strcmp(vals[i]->bv_val, "umcPolicy") ||
						!strcmp(vals[i]->bv_val, "univentionMailQuota") ||
						(strcmp(vals[i]->bv_val, "univentionPolicy") &&
							!strncmp(vals[i]->bv_val, "univentionPolicy" , strlen("univentionPolicy")))) {

						if (policy != NULL) {
							univention_debug(UV_DEBUG_POLICY, UV_DEBUG_ERROR, "more than one policy type has been determined for this policy!");
						}
						policy = univention_policy_list_get(&handle->policies, vals[i]->bv_val);
						univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "current policy type is %s", policy->name);
					}
				}
				ldap_value_free_len(vals);
			}
			if ((vals = ldap_get_values_len(ld, entry, "requiredObjectClasses")) != NULL) {
				for (i = 0; (vals[i] != NULL && vals[i]->bv_val != NULL); i++) {
					if (!in_string_array(object_classes, vals[i]->bv_val)) {
						univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "objectclass %s is required", vals[i]->bv_val);
						apply = false;
						break;
					}
				}
				ldap_value_free_len(vals);
			}
			if (apply && (vals = ldap_get_values_len(ld, entry, "prohibitedObjectClasses")) != NULL) {
				for (i = 0; (vals[i] != NULL && vals[i]->bv_val != NULL); i++) {
					if (in_string_array(object_classes, vals[i]->bv_val)) {
						univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "objectclass %s is prohibited", vals[i]->bv_val);
						apply = false;
						break;
					}
				}
				ldap_value_free_len(vals);
			}

			if (apply && (vals = ldap_get_values_len(ld, entry, "ldapFilter")) != NULL) {
				int ldap_filter_rc;
				for (i = 0; (vals[i] != NULL && vals[i]->bv_val != NULL); i++) {
					LDAPMessage *ldap_filter_res;
					char *search_attrs[] = { LDAP_NO_ATTRS, NULL };
					ldap_filter_rc = ldap_search_ext_s(ld, objectdn, LDAP_SCOPE_BASE, vals[i]->bv_val, search_attrs, 0, NULL, NULL, &timeout, 0, &ldap_filter_res);
					if (ldap_filter_rc != LDAP_SUCCESS) {
						univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "search filter '%s' caused error: %s: %s", vals[i]->bv_val, objectdn, ldap_err2string(ldap_filter_rc));
					} else {
						if (!ldap_count_entries(ld, ldap_filter_res))
							apply = false;
					}
					ldap_msgfree(ldap_filter_res);
					break;  // single-value
				}
				ldap_value_free_len(vals);
			}

			if (fixed_attributes == NULL && (vals = ldap_get_values_len(ld, entry, "fixedAttributes")) != NULL) {
				i = ldap_count_values_len(vals);
				if ((fixed_attributes = calloc(i + 1, sizeof(char *))) == NULL)
					perror("calloc");
				for (i = 0; (vals[i] != NULL && vals[i]->bv_val != NULL); i++)
					fixed_attributes[i] = strdup(vals[i]->bv_val);
				fixed_attributes[i] = NULL;
				ldap_value_free_len(vals);
			}
			if (empty_attributes == NULL && (vals = ldap_get_values_len(ld, entry, "emptyAttributes")) != NULL) {
				i = ldap_count_values_len(vals);
				if ((empty_attributes = calloc(i + 1, sizeof(char *))) == NULL)
					perror("calloc");
				for (i = 0; (vals[i] != NULL && vals[i]->bv_val != NULL); i++)
					empty_attributes[i] = strdup(vals[i]->bv_val);
				empty_attributes[i] = NULL;
				ldap_value_free_len(vals);
			}

			if (policy != NULL && apply) {
				char *attr;
				BerElement *ber;

				univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "applying policy: %s", dn);

				/* clear attributes defined in emptyAttributes; empty value entries
				 * will be removed by _cleanup; they are necessary for now to mark that
				 * attribute has been set (even though empty) */
				for (i = 0; empty_attributes != NULL && empty_attributes[i] != NULL; i++) {
#if 0
					univention_policy_attribute_list_remove(&policy->attributes, empty_attributes[i]);
#endif
					struct univention_policy_attribute_list_s* policy_attr;

					univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "considering %s/%s (EA)", policy->name, empty_attributes[i]);
					policy_attr = univention_policy_attribute_list_get(&policy->attributes, empty_attributes[i]);
					if (policy_attr->values == NULL || in_string_array(fixed_attributes, empty_attributes[i])) {
						univention_policy_result_free(policy_attr->values);
						if ((policy_attr->values = malloc(sizeof(univention_policy_result_t))) == NULL)
							perror("malloc");

						policy_attr->values->policy_dn = strdup(dn);
						policy_attr->values->count = 0;
						policy_attr->values->values = calloc(policy_attr->values->count + 1, sizeof(char*));
						policy_attr->values->values[0] = NULL;
					} else {
						univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "not setting attribute (EA)");
					}
				}

				/* iterate over attributes of policy and parse remaining attributes. */
				for (attr = ldap_first_attribute(ld, entry, &ber);
					 attr != NULL;
					 attr = ldap_next_attribute(ld, entry, ber)) {

					if (strcmp(attr, "cn") &&
						strcmp(attr, "objectClass") &&
						strcmp(attr, "fixedAttributes") &&
						strcmp(attr, "emptyAttributes") &&
						strcmp(attr, "requiredObjectClasses") &&
						strcmp(attr, "prohibitedObjectClasses") &&
						strcmp(attr, "ldapFilter") &&
						strcmp(attr, "univentionObjectType") &&
						(vals = ldap_get_values_len(ld, entry, attr)) != NULL) {

						struct univention_policy_attribute_list_s* policy_attr;

						univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "considering %s/%s", policy->name, attr);
						policy_attr = univention_policy_attribute_list_get(&policy->attributes, attr);
						if (policy_attr->values == NULL || in_string_array(fixed_attributes, attr)) {
							univention_policy_result_free(policy_attr->values);
							if ((policy_attr->values = malloc(sizeof(univention_policy_result_t))) == NULL)
								perror("malloc");

							univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "setting attribute");
							policy_attr->values->policy_dn = strdup(dn);
							policy_attr->values->count = ldap_count_values_len(vals);
							policy_attr->values->values = calloc(policy_attr->values->count + 1, sizeof(char*));
							for (i = 0; (vals[i] != NULL && vals[i]->bv_val != NULL); i++) {
								policy_attr->values->values[i] = strdup(vals[i]->bv_val);
							}
							policy_attr->values->values[i] = NULL;
						} else {
							univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "not setting attribute");
						}
						ldap_value_free_len( vals );
					}
					ldap_memfree(attr);
				}
				if (ber != NULL) {
					ber_free(ber, 0);
					ber = NULL;
				}
			} /* apply */
			FREE_ARRAY(fixed_attributes);
			FREE_ARRAY(empty_attributes);
		}
	}

	ldap_msgfree( res );
	univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ALL, "Search done.");
}

/*
 * reads policies for dn from conn
 */
univention_policy_handle_t* univention_policy_open(LDAP* ld, const char *base, const char *dn)
{
	const char* pdn;
	int rc;
	LDAPMessage *res;

	struct timeval timeout = {.tv_sec=10, .tv_usec=0};
	LDAPMessage	*entry;
	struct berval		**vals;
	int		i;
	const char *filter = "(objectClass=*)";
	char*		attrs[] = {"objectClass", "univentionPolicyReference", NULL};

	univention_policy_handle_t*	handle;
	char **object_classes = NULL;

	univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "univention_policy_open with dn = %s", dn);
	if ((handle = malloc(sizeof(univention_policy_handle_t))) == NULL)
		return NULL;
	handle->policies = NULL;

	/* iterate over all parent tree nodes. */
	for (pdn = dn; pdn != NULL; pdn = parent_dn(pdn)) {
		univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "processing dn %s", pdn);

		rc = ldap_search_ext_s(ld, pdn, LDAP_SCOPE_BASE, filter, attrs, 0, NULL, NULL, &timeout, 0, &res);
		if (rc == LDAP_NO_SUCH_OBJECT) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "Not found");
		} else if (rc != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "%s: %s", pdn, ldap_err2string(rc));
			ldap_msgfree(res);
			univention_policy_close(handle);
			return NULL;
		} else {
			/* BASE search returns at most one entry. */
			for (entry = ldap_first_entry(ld, res);
				 entry != NULL;
				 entry = ldap_next_entry(ld, entry)) {

				dprint_dn(ld, entry);

				/* only get all 'objectClass' attributes from dn. */
				if (pdn == dn && (vals = ldap_get_values_len(ld, entry, "objectClass")) != NULL) {
					univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "get object classes for %s", pdn);
					i = ldap_count_values_len(vals);
					if ((object_classes = calloc(i + 1, sizeof(char *))) == NULL)
						perror("calloc");
					for (i = 0; (vals[i] != NULL && vals[i]->bv_val != NULL); i++) {
						univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "   object class: %s", vals[i]->bv_val);
						object_classes[i] = strdup(vals[i]->bv_val);
					}
					object_classes[i] = NULL;
					ldap_value_free_len(vals);
				}

				/* iterate over all 'univentionPolicyReference' attributes. */
				if ((vals = ldap_get_values_len(ld, entry, "univentionPolicyReference")) != NULL) {
					univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "found policies for %s", pdn);
					for (i = 0; (vals[i] != NULL && vals[i]->bv_val != NULL); i++) {
						univention_debug(UV_DEBUG_POLICY, UV_DEBUG_INFO, "   policy: %s", vals[i]->bv_val);
						univention_policy_merge(ld, vals[i]->bv_val, handle, object_classes, dn);
					}
					ldap_value_free_len(vals);
				}
			}
		}

		ldap_msgfree( res );
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ALL, "Search done.");

		if (strcmp(pdn, base) == 0)
			break;

		filter = "(objectClass=univentionPolicyReference)";
	}
	FREE_ARRAY(object_classes);

	univention_policy_cleanup(handle);

	return handle;
}

/*
 * returns values for policy/attribute
 */
univention_policy_result_t* univention_policy_get(univention_policy_handle_t* handle, const char *policy_name, const char *attribute_name)
{
	struct univention_policy_list_s* policy;
	struct univention_policy_attribute_list_s* attribute;
	policy = univention_policy_list_get(&handle->policies, policy_name);
	attribute = univention_policy_attribute_list_get(&policy->attributes, attribute_name);
	return attribute->values;
}

/*
 * frees policy handle
 */
void univention_policy_close(univention_policy_handle_t* handle)
{
	struct univention_policy_list_s *cur, *next;
	for (cur = handle->policies; cur != NULL; cur = next) {
		next = cur->next;
		univention_policy_list_free(cur);
	}
	FREE(handle);
}
