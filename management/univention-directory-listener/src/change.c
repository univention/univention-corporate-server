/*
 * Univention Directory Listener
 *  abstract change handling
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

/*
 * The name change might be misleading. This is more of an abstraction
 * layer to run handlers (and do a few more tweaks such as updating the
 * schema beforehand). Functions generally take LDAP entries or DNs as
 * input.
 */

#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <lmdb.h>

#include <univention/debug.h>
#include <univention/config.h>

#include "common.h"
#include "change.h"
#include "cache.h"
#include "handlers.h"
#include "signals.h"
#include "network.h"
#include "utils.h"

extern Handler *handlers;

struct dn_list {
	char *dn;
	long size;
};

static int dn_size_compare(const void *p1, const void *p2) {
	const struct dn_list *dn1 = p1, *dn2 = p2;
	return dn1->size - dn2->size;
}

/* initialize module */
static int change_init_module(univention_ldap_parameters_t *lp, Handler *handler) {
	LDAPMessage *res, *cur;
	char *attrs[] = {LDAP_ALL_USER_ATTRIBUTES, LDAP_ALL_OPERATIONAL_ATTRIBUTES, NULL};
	struct filter **f;
	int rv;
	CacheEntry cache_entry, old_cache_entry;
	MDB_cursor *id2entry_cursor_p = NULL;
	MDB_cursor *id2dn_cursor_p = NULL;
	char *dn = NULL;
	int i;
	bool abort_init = false;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "initializing module %s", handler->name);

	memset(&old_cache_entry, 0, sizeof(CacheEntry));
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "call handler_clean for module %s", handler->name);
	handler_clean(handler);
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "call handler_initialize for module %s", handler->name);
	handler_initialize(handler);

	/* remove old entries for module */
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "remove old entries for module %s", handler->name);
	for (rv = cache_first_entry(&id2entry_cursor_p, &id2dn_cursor_p, &dn, &cache_entry); rv != MDB_NOTFOUND; rv = cache_next_entry(&id2entry_cursor_p, &id2dn_cursor_p, &dn, &cache_entry)) {
		if (rv == -1)
			continue;
		if (rv < 0)
			break;

		cache_entry_module_remove(&cache_entry, handler->name);
		cache_update_or_deleteifunused_entry(0, dn, &cache_entry, &id2dn_cursor_p);
		cache_free_entry(&dn, &cache_entry);
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "call cache_free_cursor for module %s", handler->name);
	cache_free_cursor(id2entry_cursor_p, id2dn_cursor_p);

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "initialize schema for module %s", handler->name);
	/* initialize schema; if it's not in cache yet (it really should be), it'll
	   be initialized on the regular schema check after ldapsearches */
	if ((rv = cache_get_entry_lower_upper("cn=Subschema", &cache_entry)) != 0 && rv != MDB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error while reading from database");
		return LDAP_OTHER;
	} else if (rv == 0) {
		signals_block();
		cache_update_entry(0, "cn=subschema", &cache_entry);
		handler_update("cn=Subschema", &cache_entry, &old_cache_entry, handler, 'n');
		signals_unblock();
		cache_free_entry(NULL, &cache_entry);
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "module %s for relating objects", handler->name);
	rv = LDAP_SUCCESS;
	for (f = handler->filters; !abort_init && f != NULL && *f != NULL; f++) {
		/* When initializing a module, only search for the DNs. If the
		   entry for a DN is already in our cache, we use that one,
		   instead of fetching it from LDAP. It's not only faster, but
		   more importantly we don't need to care about running all
		   other handlers that use the entry since it might have changed.
		   It's not a problem that a newer entry is possibly available;
		   we'll update it later anyway */
		char *_attrs[] = {LDAP_NO_ATTRS, NULL};
		int attrsonly1 = 1;
		LDAPControl **serverctrls = NULL;
		LDAPControl **clientctrls = NULL;
		struct timeval timeout = {
		    .tv_sec = ldap_timeout_scans(), .tv_usec = 0,
		};
		int sizelimit0 = 0;
		rv = LDAP_RETRY(lp, ldap_search_ext_s(lp->ld, (*f)->base, (*f)->scope, (*f)->filter, _attrs, attrsonly1, serverctrls, clientctrls, &timeout, sizelimit0, &res));
		if (rv != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "could not get DNs when initializing %s: %s", handler->name, ldap_err2string(rv));
			return rv;
		}

		long dn_count = 0;
		struct dn_list *dns;

		dn_count = ldap_count_entries(lp->ld, res);
		if (dn_count <= 0) {
			ldap_msgfree(res);
			continue;
		}

		if (!(dns = malloc(dn_count * sizeof(struct dn_list)))) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "malloc failed");
			abort();  // FIXME
		}

		i = 0;
		for (cur = ldap_first_entry(lp->ld, res); cur != NULL; cur = ldap_next_entry(lp->ld, cur)) {
			dns[i].dn = ldap_get_dn(lp->ld, cur);
			dns[i].size = strlen(dns[i].dn);
			i += 1;
		}
		ldap_msgfree(res);

		if (dn_count > 1) {
			qsort(dns, dn_count, sizeof(struct dn_list), &dn_size_compare);
		}

		if ((rv = change_update_schema(lp)) != LDAP_SUCCESS) {
			abort_init = true;
			goto cleanup;
		}

		for (i = 0; i < dn_count; i++) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "DN: %s", dns[i].dn);

			if ((rv = cache_get_entry_lower_upper(dns[i].dn, &cache_entry)) == MDB_NOTFOUND) { /* XXX */
				LDAPMessage *res2, *first;
				int attrsonly0 = 0;
				rv = LDAP_RETRY(lp, ldap_search_ext_s(lp->ld, dns[i].dn, LDAP_SCOPE_BASE, "(objectClass=*)", attrs, attrsonly0, serverctrls, clientctrls, &timeout, sizelimit0, &res2));
				if (rv == LDAP_SUCCESS) {
					first = ldap_first_entry(lp->ld, res2);
					cache_new_entry_from_ldap(NULL, &cache_entry, lp->ld, first);
					ldap_msgfree(res2);
				} else if (rv != LDAP_NO_SUCH_OBJECT) {
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "could not get DN %s for handler %s: %s", dns[i].dn, handler->name, ldap_err2string(rv));
					cache_free_entry(NULL, &cache_entry);
					abort_init = true;
					goto cleanup;
				}
				/* Ignore LDAP_NO_SUCH_OBJECT. An object can be
				   deleted after we do the ldapsearch. We
				   shouldn't need to care here. */
			} else if (rv != 0) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error while reading from database");
				rv = LDAP_OTHER;
				abort_init = true;
				goto cleanup;
			}

			signals_block();
			handler_update(dns[i].dn, &cache_entry, &old_cache_entry, handler, 'n');
			cache_update_entry_lower(0, dns[i].dn, &cache_entry);
			signals_unblock();
			cache_free_entry(NULL, &cache_entry);
		}
	cleanup:
		for (i = 0; i < dn_count; i++) {
			ldap_memfree(dns[i].dn);
		}
		free(dns);
	}
	cache_free_entry(NULL, &old_cache_entry);
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "finished initializing module %s with rv=%d", handler->name, rv);
	return rv;
}

/* Check if there are modules not initialized yet, and initialize them. */
int change_new_modules(univention_ldap_parameters_t *lp) {
	Handler *handler;
	int old_init_only = INIT_ONLY;

	INIT_ONLY = 1;
	for (handler = handlers; handler != NULL; handler = handler->next) {
		if ((handler->state & HANDLER_READY) != HANDLER_READY) {
			handler->state |= HANDLER_READY;

			if (change_init_module(lp, handler) == LDAP_SUCCESS)
				handler->state |= HANDLER_INITIALIZED;
			else
				handler->state ^= HANDLER_READY;

			handler_write_state(handler);
		}
	}
	INIT_ONLY = old_init_only;

	return 0;
}

/* This function should be called when a LDAP entry changes. It takes the
   new entry as input, gets the old entry from cache, and then calls the
   handlers.*/
int change_update_entry(univention_ldap_parameters_t *lp, NotifierID id, LDAPMessage *ldap_entry, char command) {
	char *dn = NULL;
	CacheEntry cache_entry, old_cache_entry;
	int rv = 0;

	memset(&cache_entry, 0, sizeof(CacheEntry));
	memset(&old_cache_entry, 0, sizeof(CacheEntry));

	if ((rv = cache_new_entry_from_ldap(&dn, &cache_entry, lp->ld, ldap_entry)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error while converting LDAP entry to cache entry");
		goto result;
	}
	if ((rv = cache_get_entry_lower_upper(dn, &old_cache_entry)) != 0 && rv != MDB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error while reading from database");
		rv = LDAP_OTHER;
	} else {
		signals_block();
		handlers_update(dn, &cache_entry, &old_cache_entry, command);
		if ((rv = cache_update_entry_lower(id, dn, &cache_entry)) != 0) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error while writing to database");
		}
		rv = 0;
		signals_unblock();
	}

result:
	cache_free_entry(&dn, &cache_entry);
	cache_free_entry(NULL, &old_cache_entry);

	return rv;
}

/* Call this function to remove a DN. */
static void change_delete(struct transaction *trans) {
	int rv;

	signals_block();

	rv = handlers_delete(trans->cur.notify.dn, &trans->cur.cache, 'd');
	if (rv == 0)
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "deleted from cache: %s", trans->cur.notify.dn);
	if (cache_entry_valid(&trans->cur.cache)) {
		if (rv != 0)
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "at least one delete handler failed");
		cache_delete_entry_lower_upper(trans->cur.notify.id, trans->cur.notify.dn);
		cache_free_entry(NULL, &trans->cur.cache);
	} else {
		if (rv != 0)
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "not in cache: %s", trans->cur.notify.dn);
	}

	signals_unblock();
}

/* Make sure schema is up-to-date */
int change_update_schema(univention_ldap_parameters_t *lp) {
	NotifierID new_id = 0;
	LDAPMessage *res, *cur;
	char *attrs[] = {LDAP_ALL_USER_ATTRIBUTES, LDAP_ALL_OPERATIONAL_ATTRIBUTES, NULL};
	int rv = 0;
	int attrsonly0 = 0;
	LDAPControl **serverctrls = NULL;
	LDAPControl **clientctrls = NULL;
	struct timeval timeout = {
	    .tv_sec = 5 * 60, .tv_usec = 0,
	};
	int sizelimit0 = 0;
	char *server_role;

	server_role = univention_config_get_string("server/role");
	if (server_role && !strcmp(server_role, "domaincontroller_master")) {
		free(server_role);
		return LDAP_SUCCESS;
	}

	free(server_role);

	if ((notifier_get_schema_id_s(NULL, &new_id)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to get schema DN");
		return LDAP_OTHER;
	}

	if (new_id > cache_master_entry.schema_id) {
		rv = LDAP_RETRY(lp, ldap_search_ext_s(lp->ld, "cn=Subschema", LDAP_SCOPE_BASE, "(objectClass=*)", attrs, attrsonly0, serverctrls, clientctrls, &timeout, sizelimit0, &res));
		if (rv == LDAP_SUCCESS) {
			if ((cur = ldap_first_entry(lp->ld, res)) == NULL) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "got no entry for schema");
				return LDAP_OTHER;
			} else {
				rv = change_update_entry(lp, new_id, cur, 'n');
			}
			ldap_memfree(res);
		} else {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "could not receive schema (%s)", ldap_err2string(rv));
		}
		cache_master_entry.schema_id = new_id;
		rv = cache_update_master_entry(&cache_master_entry);
		if (cache_set_schema_id(new_id))
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "failed to write schema ID");
	}

	return rv;
}


static bool is_move(struct transaction *trans) {
	return trans->cur.notify.command == 'a' && trans->prev.notify.command == 'r' && trans->prev.notify.id + 1 == trans->cur.notify.id;
}


static int fake_container(struct transaction *trans, char *dn) {
	int rv;
	int rdn;
	int flags = 0;
	CacheEntry cache_entry = {};
	CacheEntry dummy = {};
	LDAPDN ldap_dn = NULL;
	char *name = NULL;

	// 1. Set basic values
	cache_entry_add1(&cache_entry, "entryDN", dn);
	cache_entry_add1(&cache_entry, "description", "Univention Directory Listener intermediate fake object");
	cache_entry_add1(&cache_entry, "entryUUID", "00000000-0000-0000-0000-000000000000");

	rv = ldap_str2dn(dn, &ldap_dn, flags);
	if (rv != LDAP_SUCCESS || !ldap_dn)
		goto out;

	// 2. Set objectClass
	for (rdn = 0; ldap_dn[0][rdn]; rdn++) {
		if (BER2STR(&ldap_dn[0][rdn]->la_attr, &name) <= 0 || !name) {
			rv = LDAP_OTHER;
			goto out;
		}

		if (!strcasecmp(name, "cn")) {
			cache_entry_add1(&cache_entry, "objectClass", "organizationalRole");
		} else if (!strcasecmp(name, "ou")) {
			cache_entry_add1(&cache_entry, "objectClass", "organizationalUnit");
		} else if (!strcasecmp(name, "dc")) {
			cache_entry_add1(&cache_entry, "objectClass", "domain");
		} else {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "unknown container: %s", name);
			goto out;
		}
		free(name);

		// 3. Set RDN values
		cache_entry_update_rdn1(&cache_entry, ldap_dn[0][rdn]);
	}

	// 4. Call handlers for add
	signals_block();
	rv = handlers_update(dn, &cache_entry, &dummy, 'n');
	signals_unblock();

	// 5. Store cache entry at intermediate location
	if ((rv = cache_update_entry_lower(trans->cur.notify.id, dn, &cache_entry)) != 0)
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error while writing to database");

out:
	free(name);
	ldap_dnfree(ldap_dn);
	return rv;
}


static int check_parent_dn(struct transaction *trans, char *dn) {
	int rv = 0;
	int flags = 0;
	LDAPDN ldap_dn = NULL;

	if (trans->lp_local->host == NULL)  // not a replicating system
		return LDAP_SUCCESS;

	if (same_dn(dn, trans->lp_local->base)) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "Ignore parent_dn check because dn is ldap base.");
		return LDAP_SUCCESS;
	}

	rv = ldap_str2dn(dn, &ldap_dn, flags);
	if (rv != LDAP_SUCCESS || !ldap_dn)
		return rv;

	char *parent_dn = NULL;
	rv = ldap_dn2str(&ldap_dn[1], &parent_dn, LDAP_DN_FORMAT_LDAPV3);  // skip left most rdn
	ldap_dnfree(ldap_dn);
	if (rv != LDAP_SUCCESS)
		return rv;

	if (same_dn(parent_dn, trans->lp_local->base)) {
		// univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "parent of DN: %s is base", dn);
		goto out;
	}

	LDAPMessage *res, *cur;
	char filter[] = "(objectClass=*)";
	char *attrs_local[] = {"dn", NULL};
	char *attrs[] = {LDAP_ALL_USER_ATTRIBUTES, LDAP_ALL_OPERATIONAL_ATTRIBUTES, NULL};
	int attrsonly0 = 0;
	LDAPControl **serverctrls = NULL;
	LDAPControl **clientctrls = NULL;
	struct timeval timeout = {
	    .tv_sec = 5 * 60, .tv_usec = 0,
	};
	int sizelimit0 = 0;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "checking parent_dn of %s in local LDAP", dn);

	/* try to open a connection to the local LDAP for the parent DN check */
	if (trans->lp_local->ld == NULL) {
		rv = univention_ldap_open(trans->lp_local);
		if (rv != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "check_parent_dn: bind to local LDAP failed");
			goto out;
		}
	}

	/* search for parent_dn in local LDAP */
	rv = LDAP_RETRY(trans->lp_local, ldap_search_ext_s(trans->lp_local->ld, parent_dn, LDAP_SCOPE_BASE, filter, attrs_local, attrsonly0, serverctrls, clientctrls, &timeout, sizelimit0, &res));
	ldap_msgfree(res);
	if (rv == LDAP_NO_SUCH_OBJECT) {                /* parent_dn not present in local LDAP */
		rv = check_parent_dn(trans, parent_dn); /* check if parent of parent_dn is here */
		if (rv == LDAP_SUCCESS) {               /* parent of parent_dn found in local LDAP */
			/* lookup parent_dn object in remote LDAP */
			rv = LDAP_RETRY(trans->lp, ldap_search_ext_s(trans->lp->ld, parent_dn, LDAP_SCOPE_BASE, filter, attrs, attrsonly0, serverctrls, clientctrls, &timeout, sizelimit0, &res));
			if (rv == LDAP_NO_SUCH_OBJECT) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "could not find parent container of dn: %s from %s (%s)", dn, trans->lp->host, ldap_err2string(rv));
				if (is_move(trans))
					rv = fake_container(trans, parent_dn);
			} else { /* parent_dn found in remote LDAP */
				cur = ldap_first_entry(trans->lp->ld, res);
				if (cur == NULL) {
					/* entry exists (since we didn't get NO_SUCH_OBJECT),
					 * but was probably excluded through ACLs which makes it
					 * non-existent for us */
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "could not get parent object of dn: %s from %s (%s)", dn, trans->lp->host, ldap_err2string(rv));
					if (is_move(trans))
						rv = fake_container(trans, parent_dn);
					else
						rv = LDAP_INSUFFICIENT_ACCESS;
				} else { /* found data for parent_dn in remote LDAP */
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_PROCESS, "change_update_entry for parent_dn: %s", parent_dn);
					rv = change_update_entry(trans->lp, trans->cur.notify.id, cur, 'n'); /* add parent_dn object */
				}
			}
			ldap_msgfree(res);
		}
	}
out:
	ldap_memfree(parent_dn);
	return rv; /* LDAP_SUCCESS or other than LDAP_NO_SUCH_OBJECT */
}

static void _free_transaction_op(struct transaction_op *op) {
	ldap_memfree(op->ldap_dn);
	op->ldap_dn = NULL;
	free(op->uuid);
	op->uuid = NULL;
	cache_free_entry(NULL, &op->cache);
}

void change_free_transaction_op(struct transaction_op *op) {
	_free_transaction_op(op);
	notifier_entry_free(&op->notify);
	memset(op, 0, sizeof(struct transaction_op));
}


static bool same_rdn(LDAPRDN left, LDAPRDN right) {
	int i, j;

	for (i = 0; left[i]; i++) {
		for (j = 0; right[j]; j++) {
			if (left[i]->la_attr.bv_len != right[j]->la_attr.bv_len)
				continue;  // inner
			if (left[i]->la_value.bv_len != right[j]->la_value.bv_len)
				continue;  // inner
			if (memcmp(left[i]->la_attr.bv_val, right[j]->la_attr.bv_val, left[i]->la_attr.bv_len) == 0 && memcmp(left[i]->la_value.bv_val, right[j]->la_value.bv_val, left[i]->la_value.bv_len) == 0)
				break;  // to outer
		}
		if (!right[j])
			return false;
	}

	for (j = 0; right[j]; j++)
		;
	return i == j;
}

static int process_move(struct transaction *trans) {
	LDAPDN old_dn = NULL, new_dn = NULL;
	CacheEntry dummy = {};
	int rv;
	bool final = same_dn(trans->cur.notify.dn, trans->cur.ldap_dn);
	char *current_dn = final ? trans->cur.ldap_dn : trans->cur.notify.dn;

	// 1. remove old cache entry
	/* run handlers_delete and remove the entry from cache: Bug #26069, Bug #20605, Bug #34355 */
	rv = cache_delete_entry_lower_upper(trans->prev.notify.id, trans->prev.notify.dn);

	// 2. on rename update cache entry to reflect new RDN
	rv = ldap_str2dn(trans->prev.notify.dn, &old_dn, 0);
	if (rv != LDAP_SUCCESS || !old_dn)
		goto out;
	rv = ldap_str2dn(current_dn, &new_dn, 0);
	if (rv != LDAP_SUCCESS || !new_dn)
		goto out;
	if (!same_rdn(old_dn[0], new_dn[0]))
		cache_entry_update_rdn(trans, new_dn[0]);

	// 3. Update entryDN
	cache_entry_set1(&trans->cur.cache, "entryDN", current_dn);

	// 4. Call handlers for move
	rv = check_parent_dn(trans, current_dn);
	signals_block();
	if (same_dn(trans->prev.notify.dn, current_dn))
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_PROCESS, "move_same_dn(%s)", current_dn);
	rv = handlers_delete(trans->prev.notify.dn, &trans->prev.cache, 'r');
	rv = handlers_update(current_dn, &trans->cur.cache, &dummy, 'a');
	signals_unblock();

	// 5. Store cache entry at new location
	if ((rv = cache_update_entry_lower(trans->cur.notify.id, current_dn, &trans->cur.cache)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error while writing to database");
	}

	// 6. Check for final destination
	if (final) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "Object finally moved to '%s'", current_dn);
		rv = change_update_entry(trans->lp, trans->cur.notify.id, trans->ldap, 'm');
	}

out:
	ldap_dnfree(old_dn);
	ldap_dnfree(new_dn);
	return rv;
}

static int change_update_cache(struct transaction *trans) {
	int rv;

	/* entry exists, so make sure the schema is up-to-date and
	* then update it */
	if ((rv = change_update_schema(trans->lp)) != LDAP_SUCCESS)
		goto out;

	trans->cur.ldap_dn = ldap_get_dn(trans->lp->ld, trans->ldap);
	if (!trans->cur.ldap_dn) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to get current DN %s", trans->cur.notify.dn);
		goto out;
	}

	switch (trans->cur.notify.command) {
	case 'm':  // modify
		if (!same_dn(trans->cur.notify.dn, trans->cur.ldap_dn)) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_PROCESS, "Delaying update for '%s' until moved to '%s'", trans->cur.notify.dn, trans->cur.ldap_dn);
		} else {
			rv = check_parent_dn(trans, trans->cur.ldap_dn);
			rv = change_update_entry(trans->lp, trans->cur.notify.id, trans->ldap, trans->cur.notify.command);
		}
		break;
	case 'a':                                                               // add | move_to
		if (is_move(trans) && cache_entry_valid(&trans->prev.cache)) {  // move_to
			rv = process_move(trans);
		} else {  // add
			if (!same_dn(trans->cur.notify.dn, trans->cur.ldap_dn))
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "Schizophrenia: a NEW object '%s' is added, which ALREADY is in our cache for '%s'?", trans->cur.ldap_dn, trans->cur.notify.dn);
			rv = check_parent_dn(trans, trans->cur.ldap_dn);
			rv = change_update_entry(trans->lp, trans->cur.notify.id, trans->ldap, trans->cur.notify.command);
		}
		break;
	case 'd':  // delete
		if (!same_dn(trans->cur.notify.dn, trans->cur.ldap_dn))
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "Resurrection: DELETED object '%s' will re-appear at '%s'?", trans->cur.notify.dn, trans->cur.ldap_dn);
		change_delete(trans);
		rv = 0;
		break;
	case 'r':  // move_from
		// delay this 'r' until the following 'a' to decide if this is really a move or a delete.
		trans->prev = trans->cur;
		memset(&trans->cur, 0, sizeof(struct transaction_op));
		rv = 0;
		break;
	default:
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Unknown command: %c", trans->cur.notify.command);
	}

out:
	ldap_memfree(trans->cur.ldap_dn);
	trans->cur.ldap_dn = NULL;
	return rv;
}

/* Update DN from LDAP; this is a higher level interface for
   change_update_entry  */
int change_update_dn(struct transaction *trans) {
	LDAPMessage *res;
	char *base;
	int scope;
	char filter[64]; /* "(entryUUID=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX)" */
	char *attrs[] = {LDAP_ALL_USER_ATTRIBUTES, LDAP_ALL_OPERATIONAL_ATTRIBUTES, NULL};
	int attrsonly0 = 0;
	LDAPControl **serverctrls = NULL;
	LDAPControl **clientctrls = NULL;
	struct timeval timeout = {
	    .tv_sec = 5 * 60, .tv_usec = 0,
	};
	int sizelimit0 = 0;
	int rv;
	const char *uuid = NULL;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_PROCESS, "updating '%s' command %c", trans->cur.notify.dn, trans->cur.notify.command);

	rv = cache_get_entry_lower_upper(trans->cur.notify.dn, &trans->cur.cache);
	if (rv != 0 && rv != MDB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error reading database for %s", trans->cur.notify.dn);
		return LDAP_OTHER;
	}
	switch (trans->prev.notify.command) {
	case '\0':  // no previous pending command
		if (rv == 0)
			uuid = cache_entry_get1(&trans->cur.cache, "entryUUID");
		break;
	case 'r':  // move_from ... move_to
		if (!cache_entry_valid(&trans->prev.cache)) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "move_to without history '%s'", trans->prev.notify.dn);
			break;
		}
		if (rv == 0) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "move_to collision at '%s'", trans->cur.notify.dn);
			cache_free_entry(NULL, &trans->cur.cache);
		}
		if (is_move(trans)) {
			rv = copy_cache_entry(&trans->prev.cache, &trans->cur.cache);
			if (rv)
				goto out;
			uuid = trans->prev.uuid;
			break;
		}
	default:
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "non consecutive move: %ld:%c:%s << %ld:%c:%s", trans->prev.notify.id, trans->prev.notify.command, trans->prev.notify.dn, trans->cur.notify.id,
		                 trans->cur.notify.command, trans->cur.notify.dn);
		rv = 1;
		goto out;
	}

	if (uuid) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "updating by UUID %s", uuid);
		base = trans->lp->base;
		scope = LDAP_SCOPE_SUBTREE;
		snprintf(filter, sizeof(filter), "(entryUUID=%s)", uuid);
		trans->cur.uuid = strdup(uuid);
	} else {
	retry_dn:
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "updating by DN %s", trans->cur.notify.dn);
		base = trans->cur.notify.dn;
		scope = LDAP_SCOPE_BASE;
		snprintf(filter, sizeof(filter), "(objectClass=*)");
	}

	bool delete = false;
	rv = LDAP_RETRY(trans->lp, ldap_search_ext_s(trans->lp->ld, base, scope, filter, attrs, attrsonly0, serverctrls, clientctrls, &timeout, sizelimit0, &res));
	if (rv == LDAP_NO_SUCH_OBJECT) {
		delete = true;
	} else if (rv == LDAP_SUCCESS) {
		if ((trans->ldap = ldap_first_entry(trans->lp->ld, res)) == NULL) {
			/* entry exists (since we didn't get NO_SUCH_OBJECT),
			* but was probably excluded through ACLs which makes it
			* non-existent for us */
			delete = true;
		} else {
			rv = change_update_cache(trans);
		}
		trans->ldap = NULL;
	} else {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "error searching DN %s: %d", trans->cur.notify.dn, rv);
		_free_transaction_op(&trans->cur);
	}
	ldap_msgfree(res);
	if (delete) {
		if (uuid) {
			uuid = NULL;
			goto retry_dn;
		}
		change_delete(trans);
		rv = 0;
	}

out:
	return rv;
}
