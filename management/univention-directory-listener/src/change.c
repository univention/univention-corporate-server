/*
 * Univention Directory Listener
 *  abstract change handling
 *
 * Copyright 2004-2014 Univention GmbH
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

/*
 * The name change might be misleading. This is more of an abstraction
 * layer to run handlers (and do a few more tweaks such as updating the
 * schema beforehand). Functions generally take LDAP entries or DNs as
 * input.
 */

#include <stdlib.h>
#include <string.h>
#include <db.h>

#include <univention/debug.h>
#include <univention/config.h>

#include "common.h"
#include "change.h"
#include "cache.h"
#include "handlers.h"
#include "signals.h"
#include "network.h"

extern Handler *handlers;

struct dn_list{
	char *dn;
	long size;
};

static int dn_size_compare(const void *p1, const void *p2)
{
	const struct dn_list *dn1 = p1, *dn2 = p2;
	return dn1->size - dn2->size;
}

/* initialize module */
int change_init_module(univention_ldap_parameters_t *lp, Handler *handler)
{
	LDAPMessage *res, *cur;
	char *attrs[]={"*", "+", NULL};
	struct filter **f;
	int rv;
	CacheEntry cache_entry, old_cache_entry;
	DBC *dbc_cur;
	char *dn = NULL;
	int i;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN,
			"initializing module %s", handler->name);

	memset(&old_cache_entry, 0, sizeof(CacheEntry));
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
			"call handler_clean for module %s", handler->name);
	handler_clean(handler);
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
			"call handler_initialize for module %s", handler->name);
	handler_initialize(handler);

	/* remove old entries for module */
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
			"remove old entries for module %s", handler->name);
	for (rv=cache_first_entry(&dbc_cur, &dn, &cache_entry); rv != DB_NOTFOUND;
			rv=cache_next_entry(&dbc_cur, &dn, &cache_entry)) {
		if (rv == -1) continue;
		if (rv < 0) break;

		cache_entry_module_remove(&cache_entry, handler->name);
		cache_update_or_deleteifunused_entry(0, dn, &cache_entry);
		cache_free_entry(&dn, &cache_entry);
	}
	if(!dn)
		free(dn);

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
			"call cache_free_cursor for module %s", handler->name);
	cache_free_cursor(dbc_cur);

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
			"initialize schema for module %s", handler->name);
	/* initialize schema; if it's not in cache yet (it really should be), it'll
	   be initialized on the regular schema check after ldapsearches */
	if ((rv = cache_get_entry_lower_upper("cn=Subschema", &cache_entry)) != 0 &&
			rv != DB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN,
				"error while reading from database");
		return LDAP_OTHER;
	} else if (rv == 0) {
		signals_block();
		cache_update_entry(0, "cn=subschema", &cache_entry);
		handler_update("cn=Subschema", &cache_entry, &old_cache_entry, handler, 'n', NULL);
		signals_unblock();
		cache_free_entry(NULL, &cache_entry);
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
			"module %s for relating objects", handler->name);
	for (f = handler->filters; f != NULL && *f != NULL; f++) {
		/* When initializing a module, only search for the DNs. If the
		   entry for a DN is already in our cache, we use that one,
		   instead of fetching it from LDAP. It's not only faster, but
		   more importantly we don't need to care about running all
		   other handlers that use the entry since it might have changed.
		   It's not a problem that a newer entry is possibly available;
		   we'll update it later anyway */
		if ((rv =  ldap_search_ext_s(lp->ld, (*f)->base, (*f)->scope, (*f)->filter, NULL, 1,  NULL /*serverctrls*/, NULL /*clientctrls*/, NULL /*timeout*/, 0 /*sizelimit*/, &res)) != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "could not get DNs when initializing %s: %s", handler->name, ldap_err2string(rv));
			return rv;
		}

		long dn_count=0;
		struct dn_list *dns;

		dn_count = ldap_count_entries(lp->ld, res );
		if ( dn_count > 0 ) {
			dns = malloc(dn_count * sizeof(struct dn_list));
		}

		i=0;
		for (cur = ldap_first_entry(lp->ld, res); cur != NULL; cur = ldap_next_entry(lp->ld, cur)) {
			dns[i].dn = ldap_get_dn(lp->ld, cur);
			dns[i].size = strlen(dns[i].dn);
			i+=1;
		}

		if ( dn_count > 1 ) {
			qsort(dns, dn_count, sizeof(struct dn_list), &dn_size_compare);
		}

		if ((rv = change_update_schema(lp)) != LDAP_SUCCESS) {
			ldap_msgfree(res);
			return rv;
		}

		for (i=0; i<dn_count; i++) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "DN: %s", dns[i].dn);

			if ((rv = cache_get_entry_lower_upper(dns[i].dn, &cache_entry)) == DB_NOTFOUND) { /* XXX */
				LDAPMessage *res2, *first;
				if ((rv = ldap_search_ext_s(lp->ld, dns[i].dn, LDAP_SCOPE_BASE, "(objectClass=*)", attrs, 0, NULL /*serverctrls*/, NULL /*clientctrls*/, NULL /*timeout*/, 0 /*sizelimit*/, &res2)) == LDAP_SUCCESS) {
					first = ldap_first_entry(lp->ld, res2);
					cache_new_entry_from_ldap(NULL, &cache_entry, lp->ld, first);
					ldap_msgfree(res2);
				} else if (rv != LDAP_NO_SUCH_OBJECT) {
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "could not get DN %s for handler %s: %s", dns[i].dn, handler->name, ldap_err2string(rv));
					cache_free_entry(NULL, &cache_entry);
					return rv;
				}
				/* Ignore LDAP_NO_SUCH_OBJECT. An object can be
				   deleted after we do the ldapsearch. We
				   shouldn't need to care here. */
			} else if (rv != 0) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error while reading from database");
				rv = LDAP_OTHER;
				break;
			}

			signals_block();

			/* First copy the entry for the local cache to be sure the entry in the cache is untouched. Bug #21914 */
			CacheEntry updated_cache_entry;
			copy_cache_entry(&cache_entry, &updated_cache_entry);
			handler_update(dns[i].dn, &cache_entry, &old_cache_entry, handler, 'n', &updated_cache_entry);
			//compare_cache_entries(&cache_entry, &updated_cache_entry);
			cache_update_entry_lower(0, dns[i].dn, &updated_cache_entry);
			cache_free_entry(NULL, &updated_cache_entry);

			signals_unblock();
			cache_free_entry(NULL, &cache_entry);
		}
		for(i=0; i<dn_count; i++) {
			ldap_memfree(dns[i].dn);
		}
		if ( dn_count > 1) {
		  free(dns);
		}
		ldap_msgfree(res);
	}
	cache_free_entry(NULL, &old_cache_entry);
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN,
			"finished initializing module %s", handler->name);
	return rv;
}

/* Check if there are modules not initialized yet, and initialize them. */
int change_new_modules(univention_ldap_parameters_t *lp)
{
	Handler	*handler;

	for (handler = handlers; handler != NULL; handler = handler->next) {
		if ((handler->state & HANDLER_READY) != HANDLER_READY) {
			handler->state |= HANDLER_READY;

			if (change_init_module(lp, handler) == LDAP_SUCCESS)
				handler->state |= HANDLER_INITIALIZED;
			else
				handler->state ^= HANDLER_READY;
		}
	}

	return 0;
}

/* This function should be called when a LDAP entry changes. It takes the
   new entry as input, gets the old entry from cache, and then calls the
   handlers.*/
int change_update_entry(univention_ldap_parameters_t *lp, NotifierID id, LDAPMessage *ldap_entry, char command)
{
	char *dn=NULL;
	CacheEntry cache_entry, old_cache_entry, updated_cache_entry;
	int rv = 0;

	memset(&cache_entry, 0, sizeof(CacheEntry));
	memset(&old_cache_entry, 0, sizeof(CacheEntry));
	memset(&updated_cache_entry, 0, sizeof(CacheEntry));

	if ((rv=cache_new_entry_from_ldap(&dn, &cache_entry, lp->ld, ldap_entry)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error while converting LDAP entry to cache entry");
		goto result;
	}
	if ((rv = cache_get_entry_lower_upper(dn, &old_cache_entry)) != 0 && rv != DB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error while reading from database");
		rv = LDAP_OTHER;
	} else {
		signals_block();
		/* First copy the entry for the local cache to be sure the entry in the cache is untouched. Bug #21914 */
		copy_cache_entry(&cache_entry, &updated_cache_entry);
		handlers_update(dn, &cache_entry, &old_cache_entry, command, &updated_cache_entry);
		//compare_cache_entries(&cache_entry, &updated_cache_entry);
		if ((rv=cache_update_entry_lower(id, dn, &updated_cache_entry)) != 0) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error while writing to database");
		}
		rv=0;
		signals_unblock();
	}

result:
	cache_free_entry(&dn, &cache_entry);
	cache_free_entry(NULL, &old_cache_entry);
	cache_free_entry(NULL, &updated_cache_entry);

	return rv;
}

/* Call this function to remove a DN. */
int change_delete_dn(NotifierID id, char *dn, char command)
{
	CacheEntry entry;
	int rv;

	if ((rv = cache_get_entry_lower_upper(dn, &entry)) == DB_NOTFOUND) {
		signals_block();
		/* run handlers anyway */
		if (handlers_delete(dn, &entry, command) == 0) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "deleted from cache: %s", dn);
		} else {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "not in cache: %s", dn);
		}
		signals_unblock();
		return LDAP_SUCCESS;
	} else if (rv != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "reading from cache failed: %s", dn);
		return LDAP_OTHER;
	}

	signals_block();
	if (handlers_delete(dn, &entry, command) == 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "deleted from cache: %s", dn);
		cache_delete_entry_lower_upper(id, dn);
	} else {
		/* update information which modules failed and are still to be run */
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "at least one delete handler failed");
		cache_update_entry_lower(id, dn, &entry);
	}
	signals_unblock();
	cache_free_entry(NULL, &entry);

	return LDAP_SUCCESS;
}

/* Make sure schema is up-to-date */
int change_update_schema(univention_ldap_parameters_t *lp)
{
#ifdef WITH_DB42
	CacheMasterEntry	 master_entry;
#else
	NotifierID		 id = 0;
#endif
	NotifierID		 new_id = 0;
	LDAPMessage		*res,
				*cur;
	char			*attrs[]={"*", "+", NULL};
	int			 rv = 0;
	struct timeval timeout;
	char *server_role;

	server_role = univention_config_get_string("server/role");

	if (STREQ(server_role, "domaincontroller_master")) {
		free(server_role);
		return LDAP_SUCCESS;
	}

	free(server_role);
	/* max wait for 5 minutes */
	timeout.tv_sec = 300;
	timeout.tv_usec = 0;

#ifdef WITH_DB42
	if ((rv=cache_get_master_entry(&master_entry)) == DB_NOTFOUND) {
		master_entry.id = 0;
		master_entry.schema_id = 0;
	 } else if (rv != 0)
		return rv;
#else
	cache_get_schema_id("notifier_schema_id", &id, 0);
#endif
	if ((notifier_get_schema_id_s(NULL, &new_id)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to get schema DN");
		return LDAP_OTHER;
	}

#ifdef WITH_DB42
	if (new_id > master_entry.schema_id) {
#else
	if (new_id > id) {
#endif
		if ((rv=ldap_search_ext_s(lp->ld, "cn=Subschema", LDAP_SCOPE_BASE, "(objectClass=*)", attrs, 0, NULL /*serverctrls*/, NULL /*clientctrls*/, &timeout, 0 /*sizelimit*/, &res)) == LDAP_SUCCESS) {
			if ((cur=ldap_first_entry(lp->ld, res)) == NULL) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "got no entry for schema");
				return LDAP_OTHER;
			} else {
				rv = change_update_entry(lp, new_id, cur, 'n');
			}
			ldap_memfree(res);
		} else {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "could not receive schema (%s)", ldap_err2string(rv));
		}

#ifndef WITH_DB42
		if (rv == 0)
			cache_set_schema_id("notifier_schema_id", new_id);
#endif
	}

	return rv;
}

int check_parent_dn(univention_ldap_parameters_t *lp, NotifierID id, char *dn, univention_ldap_parameters_t *lp_local)
{
	int rv = 0;
	int flags = 0;
	LDAPDN ldap_dn = NULL;

	if (STREQ(dn, lp_local->base)) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "Ignore parent_dn check because dn is ldap base.");
		return LDAP_SUCCESS;
	}

	rv = ldap_str2dn(dn, &ldap_dn, flags);
	if ( rv != LDAP_SUCCESS || ! ldap_dn )
		return rv;

	char *parent_dn = NULL;
	rv = ldap_dn2str(&ldap_dn[1], &parent_dn, LDAP_DN_FORMAT_LDAPV3); // skip left most rdn
	ldap_dnfree( ldap_dn );
	if ( rv != LDAP_SUCCESS )
		return rv;

	if (STREQ(parent_dn, lp_local->base)) {
		// univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "parent of DN: %s is base", dn);
		ldap_memfree( parent_dn );
		return LDAP_SUCCESS;
	}

	LDAPMessage	*res,
			*cur;
	char *attrs_local[] = {"dn", NULL};
	char *attrs[] = {"*", "+", NULL};
	struct timeval timeout;
	/* max wait for 60 seconds */
	timeout.tv_sec = 60;
	timeout.tv_usec = 0;

		/* TODO: fix indentation */
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "checking parent_dn of %s in local LDAP", dn);

		/* try to open a connection to the local LDAP for the parent DN check */
		if (lp_local->ld == NULL) {
			/* XXX: Fix when using krb5 */
			rv = univention_ldap_open(lp_local);
			if ( rv != LDAP_SUCCESS) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "check_parent_dn: bind to local LDAP failed");
				ldap_memfree( parent_dn );
				return rv;
			}
		}

		/* search for parent_dn in local LDAP */
		rv = ldap_search_ext_s(lp_local->ld, parent_dn, LDAP_SCOPE_BASE, "(objectClass=*)", attrs_local, 0, NULL /*serverctrls*/, NULL /*clientctrls*/, &timeout, 0 /*sizelimit*/, &res);
		ldap_msgfree( res );
		if ( rv == LDAP_NO_SUCH_OBJECT ) {		/* parent_dn not present in local LDAP */
			rv = check_parent_dn(lp, id, parent_dn, lp_local);	/* check if parent of parent_dn is here */
			if (rv == LDAP_SUCCESS) {			/* parent of parent_dn found in local LDAP */
				/* lookup parent_dn object in remote LDAP */
				rv = ldap_search_ext_s(lp->ld, parent_dn, LDAP_SCOPE_BASE, "(objectClass=*)", attrs, 0, NULL /*serverctrls*/, NULL /*clientctrls*/, &timeout, 0 /*sizelimit*/, &res);
				if ( rv == LDAP_NO_SUCH_OBJECT ) {
					 univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "could not find parent container of dn: %s from %s (%s)", dn, lp->host, ldap_err2string(rv));
					ldap_memfree( parent_dn );
					ldap_msgfree( res );
					return rv;
				} else { /* parent_dn found in remote LDAP */
					cur=ldap_first_entry(lp->ld, res);
					if (cur == NULL) {
						/* entry exists (since we didn't get NO_SUCH_OBJECT),
						 * but was probably excluded thru ACLs which makes it
						 * non-existent for us */
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "could not get parent object of dn: %s from %s (%s)", dn, lp->host, ldap_err2string(rv));
						ldap_memfree( parent_dn );
						ldap_msgfree( res );
						return LDAP_INSUFFICIENT_ACCESS;
					} else { /* found data for parent_dn in remote LDAP */
						univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_PROCESS, "change_update_entry for parent_dn: %s", parent_dn);
						rv = change_update_entry(lp, id, cur, 'n');	/* add parent_dn object */
						ldap_memfree( parent_dn );
						ldap_msgfree( res );	// cur points into res
						return rv;
					}
					return LDAP_OTHER; /* safetybelt, should not get here */
				}
				return LDAP_OTHER; /* safetybelt, should not get here */
			}
			ldap_memfree( parent_dn );
			return rv; /* check_parent_dn(parent_dn) failed, something is wrong with parent_dn */
		}
		ldap_memfree( parent_dn );
		return rv;	/* LDAP_SUCCESS or other than LDAP_NO_SUCH_OBJECT */
}

static int cache_lookup_uuid(char *dn, char **uuid) {
	CacheEntry entry;
	int rv;
	int i;

	rv = cache_get_entry_lower_upper(dn, &entry);
	if (rv == 0) {
		for (i = 0; i < entry.attribute_count; i++) {
			if (STRNEQ("entryUUID", entry.attributes[i]->name))
				continue;
			if (entry.attributes[i]->value_count != 1)
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR,
						"wrong entryUUID count: %d", entry.attributes[i]->value_count);
			else if (entry.attributes[i]->length[0] < 36 || entry.attributes[i]->length[0] > 37)
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR,
						"wrong entryUUID length: %d", entry.attributes[i]->length[0]);
			else
				*uuid = strdup(entry.attributes[i]->values[0]);
			break;
		}
	}
	cache_free_entry(NULL, &entry);

	return rv;
}

/* Update DN from LDAP; this is a higher level interface for
   change_update_entry  */
int change_update_dn(univention_ldap_parameters_t *lp, NotifierID id, char *dn, char command, univention_ldap_parameters_t *lp_local)
{
	LDAPMessage *res, *cur;
	char *base;
	int scope;
	char filter[64]; /* "(entryUUID=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX)" */
	char *attrs[] = {"*", "+", NULL};
	int attrsonly = 0;
	LDAPControl **serverctrls = NULL;
	LDAPControl **clientctrls = NULL;
	struct timeval timeout = {
		.tv_sec = 5*60,
		.tv_usec = 0,
	};
	int sizelimit = 0;
	int rv;
	char *uuid = NULL;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "updating %s", dn);
	if ( command == 'r' ) {
		/* if the entry has been renamed, run handlers_delete and remove the entry from cache, Bug #26069, updated for Bug #20605*/
		return change_delete_dn(id, dn, command);
	}

	rv = cache_lookup_uuid(dn, &uuid);
	if (rv != 0 && rv != DB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error while reading from database");
		return LDAP_OTHER;
	}

	if (uuid) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "updating UUID %s", uuid);
		base = lp->base;
		scope = LDAP_SCOPE_SUBTREE;
		snprintf(filter, sizeof(filter), "(entryUUID=%s)", uuid);
		free(uuid);
	} else {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "no entryUUID %s", dn);
		base = dn;
		scope = LDAP_SCOPE_BASE;
		snprintf(filter, sizeof(filter), "(objectClass=*)");
	}

	rv = ldap_search_ext_s(lp->ld, base, scope, filter, attrs, attrsonly, serverctrls, clientctrls, &timeout, sizelimit, &res);
	if (rv == LDAP_NO_SUCH_OBJECT) {
		rv = change_delete_dn(id, dn, command);
	} else if (rv == LDAP_SUCCESS) {
		if ((cur=ldap_first_entry(lp->ld, res)) == NULL) {
			/* entry exists (since we didn't get NO_SUCH_OBJECT),
			* but was probably excluded through ACLs which makes it
			* non-existent for us */
			rv = change_delete_dn(id, dn, command);
		} else {
			/* entry exists, so make sure the schema is up-to-date and
			* then update it */
			if ((rv = change_update_schema(lp)) == LDAP_SUCCESS) {
				if (lp_local->host != NULL)     // we are a replicating system
					rv = check_parent_dn(lp, id, dn, lp_local);
				rv = change_update_entry(lp, id, cur, command);
			}
		}
	} else {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error searching dn %s: %d", dn, rv);
	}
	ldap_msgfree(res);

	return rv;
}
