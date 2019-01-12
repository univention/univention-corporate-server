/*
 * Univention Directory Listener
 *  ldap listener caching system
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

/* How it works:

   LDAP entries are cached here. If a modification takes place,
   the new LDAP entry is compared with the cache entry, and both,
   old and new entries, are passed to the handler modules.

   Berkeley DB provides a way to store and receive a chunk of data
   with a given key. However, we're not working with cache entries
   as chunks of data later, but use C structures. So we'll need to
   convert the C structure we can work with to chunks of data we
   can store in BDB, and the other way around.

   We have decided on a pretty low level, but straightforward
   binary format for the chunk of data. For manual error recovery, a
   text-based format like LDIF might have been easier.

   The function unparse_entry converts a C structure entry to a data
   chunk, parse_entry does the opposite.

   To convert the entry, unparse_entry walks through all values of
   all attributes, as well as through the list of modules registered
   with it, and write a block for each (attribute, value) pair or
   (, module) [write_header]. Each block starts with an entry_header
   structure that specified the lengths of the following data.
*/


#define _GNU_SOURCE /* for strndup */

#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include <unistd.h>
#include <ctype.h>
#include <sys/types.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <db.h>
#include <stdbool.h>
#include <assert.h>

#include <univention/debug.h>
#include <univention/config.h>

#include "common.h"
#include "cache_bdb.h"
#include "cache_lowlevel.h"
#include "cache_entry.h"
#include "network.h"
#include "signals.h"
#include "filter.h"
#include "utils.h"

#define MASTER_KEY "__master__"
#define MASTER_KEY_SIZE (sizeof MASTER_KEY)

char *bdb_cache_dir = "/var/lib/univention-directory-listener";
char *bdb_ldap_dir = "/var/lib/univention-ldap";

CacheMasterEntry cache_master_entry;

DB *dbp;
#ifdef WITH_DB42
DB_ENV *dbenvp;
#endif
static FILE *lock_fp = NULL;

static struct filter cache_filter;
static struct filter *cache_filters[] = {&cache_filter, NULL};

static void setup_cache_filter(void) {
	FREE(cache_filter.filter);
	FREE(cache_filter.base);
	cache_filter.filter = univention_config_get_string("listener/cache/filter");
	if (cache_filter.filter && cache_filter.filter[0]) {
		cache_filter.base = univention_config_get_string("ldap/base");
		cache_filter.scope = LDAP_SCOPE_SUBTREE;
	}
}

#ifdef WITH_DB42
static void bdb_cache_panic_call(DB_ENV *dbenvp, int errval) {
	exit(1);
}
#endif

static void bdb_cache_error_message(const char *errpfx, char *msg) {
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "database error: %s", msg);
}

int bdb_cache_lock(void) {
	int rv, fd;
	char lock_file[PATH_MAX];

	assert(!lock_fp);

	rv = snprintf(lock_file, PATH_MAX, "%s/cache.db.lock", bdb_cache_dir);
	if (rv < 0 || rv >= PATH_MAX)
		abort();

	if ((lock_fp = fopen(lock_file, "a+e")) == NULL) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Could not open lock file [%s]", lock_file);
		exit(EXIT_FAILURE);
	}
	fd = fileno(lock_fp);

	if (lockf(fd, F_TLOCK, 0) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Could not get lock for database [%s]; "
		                                                    "Is another listener processs running?\n",
		                 lock_file);
		exit(EXIT_FAILURE);
	}

	return fd;
}

int bdb_cache_init(void) {
	int rv;
	char file[PATH_MAX];

	snprintf(file, PATH_MAX, "%s/cache.db", bdb_cache_dir);

#ifdef WITH_DB42
	if ((rv = db_env_create(&dbenvp, 0)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "creating database environment failed");
		return rv;
	}
	dbenvp->set_errcall(dbenvp, bdb_cache_error_message);
	dbenvp->set_paniccall(dbenvp, bdb_cache_panic_call);
	if ((rv = dbenvp->open(dbenvp, bdb_cache_dir, DB_CREATE | DB_INIT_MPOOL |
	                                                  /*DB_INIT_LOCK | */ DB_INIT_LOG | DB_INIT_TXN | DB_RECOVER,
	                       0600)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "opening database environment failed");
		dbenvp->err(dbenvp, rv, "%s", "environment");
		return rv;
	}
	if ((rv = db_create(&dbp, dbenvp, 0)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "creating database handle failed");
		return rv;
	}
	if ((rv = dbp->open(dbp, NULL, "cache.db", NULL, DB_BTREE, DB_CREATE | DB_CHKSUM | DB_AUTO_COMMIT, 0600)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "opening database failed");
		dbp->err(dbp, rv, "open");
		// FIXME: free dbp
		return rv;
	}
#else
	if ((rv = db_create(&dbp, NULL, 0)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "creating database handle failed");
		return rv;
	}
	if ((rv = dbp->open(dbp, file, NULL, DB_BTREE, DB_CREATE, 0600)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "opening database failed");
		dbp->err(dbp, rv, "open");
		// FIXME: free dbp
		return rv;
	}
	dbp->set_errcall(dbp, bdb_cache_error_message);
#endif
	setup_cache_filter();
	return 0;
}

void bdb_cache_sync(void) {
	if (dbp) {
		dbp->sync(dbp, 0);
	}
}

int bdb_cache_set_schema_id(const NotifierID value) {
	int rv, fd, len;
	char file[PATH_MAX], buf[15];

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "Set Schema ID to %ld", value);
	len = snprintf(buf, sizeof buf, "%ld", value);
	if (len < 0 || len >= sizeof buf)
		return len;

	rv = snprintf(file, PATH_MAX, "%s/schema/id/id", bdb_ldap_dir);
	if (rv < 0 || rv >= PATH_MAX)
		return rv;
	fd = open(file, O_WRONLY | O_CREAT, 0644);
	if (fd < 0)
		return fd;
	rv = write(fd, buf, len);
	if (rv != len) {
		close(fd);
		return 1;
	}
	rv = ftruncate(fd, len);
	if (rv != 0)
		return rv;
	rv = close(fd);
	if (rv != 0)
		return rv;
	return 0;
}

int bdb_cache_get_schema_id(NotifierID *value, const long def) {
	FILE *fp;
	char file[PATH_MAX];
	int rv;

	*value = def;

	snprintf(file, PATH_MAX, "%s/schema/id/id", bdb_ldap_dir);
	if ((fp = fopen(file, "r")) == NULL)
		return 1;
	rv = fscanf(fp, "%ld", value);
	return fclose(fp) || (rv != 1);
}

int bdb_cache_set_int(char *key, const NotifierID value) {
	int rv;
	FILE *fp;
	char file[PATH_MAX], tmpfile[PATH_MAX];

	rv = snprintf(tmpfile, PATH_MAX, "%s/%s.tmp", bdb_cache_dir, key);
	if (rv < 0 || rv >= PATH_MAX)
		return rv;
	if ((fp = fopen(tmpfile, "w")) == NULL)
		abort_io("open", tmpfile);
	fprintf(fp, "%ld", value);
	rv = fclose(fp);
	if (rv != 0)
		abort_io("close", tmpfile);

	rv = snprintf(file, PATH_MAX, "%s/%s", bdb_cache_dir, key);
	if (rv < 0 || rv >= PATH_MAX)
		return rv;
	rv = rename(tmpfile, file);
	return rv;
}

int bdb_cache_get_int(char *key, NotifierID *value, const long def) {
	FILE *fp;
	char file[PATH_MAX];
	int rv;

	*value = def;

	snprintf(file, PATH_MAX, "%s/%s", bdb_cache_dir, key);
	if ((fp = fopen(file, "r")) == NULL)
		return 1;
	rv = fscanf(fp, "%ld", value);
	return fclose(fp) || (rv != 1);
}

int bdb_cache_get_master_entry(CacheMasterEntry *master_entry) {
	DBT key, data;
	int rv;

	memset(&key, 0, sizeof(DBT));
	memset(&data, 0, sizeof(DBT));

	key.data = MASTER_KEY;
	key.size = MASTER_KEY_SIZE;
	data.flags = DB_DBT_REALLOC;

	if ((rv = dbp->get(dbp, NULL, &key, &data, 0)) == DB_NOTFOUND)
		return rv;
	else if (rv != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "reading master entry from database failed");
		dbp->err(dbp, rv, "get");
		return rv;
	}

	if (data.size != sizeof(CacheMasterEntry)) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "master entry has unexpected length");
		return 1;
	}

	memcpy(master_entry, data.data, sizeof(CacheMasterEntry));
	free(data.data);

	return 0;
}

int bdb_cache_update_master_entry(CacheMasterEntry *master_entry, DB_TXN *dbtxnp) {
	DBT key, data;
	int rv;
	int flags;

	memset(&key, 0, sizeof(DBT));
	memset(&data, 0, sizeof(DBT));

	key.data = MASTER_KEY;
	key.size = MASTER_KEY_SIZE;

	data.data = (void *)master_entry;
	data.size = sizeof(CacheMasterEntry);

#ifdef WITH_DB42
	if (dbtxnp == NULL)
		flags = DB_AUTO_COMMIT;
	else
#endif
		flags = 0;

	if ((rv = dbp->put(dbp, dbtxnp, &key, &data, flags)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "storing master entry in database failed");
		dbp->err(dbp, rv, "put");
		return rv;
	}

	bdb_cache_sync();

	return 0;
}

DB_TXN *bdb_cache_new_transaction(NotifierID id, char *dn) {
#ifdef WITH_DB42
	DB_TXN *dbtxnp;
	CacheMasterEntry master_entry;
	NotifierID *old_id;

	dbenvp->txn_begin(dbenvp, NULL, &dbtxnp, 0);

	if (id != 0) {
		if (bdb_cache_get_master_entry(&master_entry) != 0) {
			dbtxnp->abort(dbtxnp);
			return NULL;
		}

		if (strcmp(dn, "cn=Subschema") == 0)
			old_id = &master_entry.schema_id;
		else
			old_id = &master_entry.id;

		if (*old_id >= id) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "New ID (%ld) is not greater than old"
			                                                    " ID (%ld): %s",
			                 id, *old_id, dn);
			dbtxnp->abort(dbtxnp);
			return NULL;
		} else
			*old_id = id;

		if (bdb_cache_update_master_entry(&master_entry, dbtxnp) != 0) {
			dbtxnp->abort(dbtxnp);
			return NULL;
		}
	}

	return dbtxnp;
#else
	return NULL;
#endif
}


/* XXX: The NotifierID is passed for future use. Once the journal is
   implemented, entries other than the most recent one can be returned.
   At the moment, the id parameters for bdb_cache_update_entry, and
   bdb_cache_delete_entry do nothing (at least if WITH_DB42 is undefined) */
inline int bdb_cache_update_entry(NotifierID id, char *dn, CacheEntry *entry) {
	DBT key, data;
	DB_TXN *dbtxnp;
	int rv = 0;

	memset(&key, 0, sizeof(DBT));
	memset(&data, 0, sizeof(DBT));

	if ((rv = unparse_entry(&data.data, &data.size, entry)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "unparsing entry failed");
		return rv;
	}


	signals_block();
#ifdef WITH_DB42
	dbtxnp = bdb_cache_new_transaction(id, dn);
	if (dbtxnp == NULL) {
		signals_unblock();
		free(data.data);
		return 1;
	}
#else
	dbtxnp = NULL;
#endif

	key.data = dn;
	key.size = strlen(dn) + 1;

	if ((rv = dbp->put(dbp, dbtxnp, &key, &data, 0)) != 0) {
		signals_unblock();
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "storing entry in database failed: %s", dn);
		dbp->err(dbp, rv, "put");
#ifdef WITH_DB42
		dbtxnp->abort(dbtxnp);
#endif
		free(data.data);
		return rv;
	}
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "put %d bytes for %s", data.size, dn);


#ifdef WITH_DB42
	dbtxnp->commit(dbtxnp, 0);
#endif
	bdb_cache_sync();
	signals_unblock();

	free(data.data);
	return rv;
}

int bdb_cache_update_entry_lower(NotifierID id, char *dn, CacheEntry *entry) {
	char *lower_dn;
	int rv = 0;

	if (cache_filter.filter && cache_entry_ldap_filter_match(cache_filters, dn, entry)) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "Not caching %s, filtered out.", dn);
		return rv;
	}

	lower_dn = lower_utf8(dn);
	rv = bdb_cache_update_entry(id, lower_dn, entry);

	free(lower_dn);
	return rv;
}

int bdb_cache_delete_entry(NotifierID id, char *dn) {
	DB_TXN *dbtxnp;
	DBT key;
	int rv;

	memset(&key, 0, sizeof(DBT));

	key.data = dn;
	key.size = strlen(dn) + 1;

	signals_block();
#ifdef WITH_DB42
	dbtxnp = bdb_cache_new_transaction(id, dn);
	if (dbtxnp == NULL) {
		signals_unblock();
		return 1;
	}
#else
	dbtxnp = NULL;
#endif

	if ((rv = dbp->del(dbp, dbtxnp, &key, 0)) != 0 && rv != DB_NOTFOUND) {
		signals_unblock();
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "removing from database failed: %s", dn);
		dbp->err(dbp, rv, "del");
	}

#ifdef WITH_DB42
	dbtxnp->commit(dbtxnp, 0);
#endif
	bdb_cache_sync();
	signals_unblock();

	return rv;
}

int bdb_cache_delete_entry_lower_upper(NotifierID id, char *dn) {
	char *lower_dn;
	bool mixedcase = false;
	int rv, rv2;

	// convert to a lowercase dn
	lower_dn = lower_utf8(dn);
	rv = bdb_cache_delete_entry(id, lower_dn);
	if (strcmp(dn, lower_dn) != 0) {
		mixedcase = true;
		// try again with original dn
		rv2 = bdb_cache_delete_entry(id, dn);
	}

	free(lower_dn);
	if (mixedcase) {
		return rv ? rv2 : rv;  // if rv was bad (!=0) return rv2, otherwise return rv
	} else {
		return rv;
	}
}

int bdb_cache_update_or_deleteifunused_entry(NotifierID id, char *dn, CacheEntry *entry) {
	if (entry->module_count == 0)
		return bdb_cache_delete_entry(id, dn);
	else
		return bdb_cache_update_entry(id, dn, entry);
}

int bdb_cache_get_entry(char *dn, CacheEntry *entry) {
	DBT key, data;
	int rv = 0;

	memset(&key, 0, sizeof(DBT));
	memset(&data, 0, sizeof(DBT));
	memset(entry, 0, sizeof(CacheEntry));

	key.data = dn;
	key.size = strlen(dn) + 1;
	data.flags = DB_DBT_REALLOC;

	signals_block();
	rv = dbp->get(dbp, NULL, &key, &data, 0);
	signals_unblock();

	if (rv != 0 && rv != DB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "reading %s from database failed", dn);
		dbp->err(dbp, rv, "get");
		return rv;
	} else if (rv == DB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "no cache entry found for %s", dn);
		return rv;
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "got %d bytes for %s", data.size, dn);

	if ((rv = parse_entry(data.data, data.size, entry)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "parsing entry failed");
		free(data.data);
		exit(1);
	}

	free(data.data);
	return rv;
}

int bdb_cache_get_entry_lower_upper(char *dn, CacheEntry *entry) {
	char *lower_dn;
	bool mixedcase = false;
	int rv;

	// convert to a lowercase dn
	lower_dn = lower_utf8(dn);
	if (strcmp(dn, lower_dn) != 0) {
		mixedcase = true;
	}

	rv = bdb_cache_get_entry(lower_dn, entry);
	if (rv == DB_NOTFOUND && mixedcase) {
		// try again with original dn
		rv = bdb_cache_get_entry(dn, entry);
	}

	free(lower_dn);
	return rv;
}

int bdb_cache_first_entry(DBC **cur, char **dn, CacheEntry *entry) {
	int rv;

	if ((rv = dbp->cursor(dbp, NULL, cur, 0)) != 0) {
		dbp->err(dbp, rv, "cursor");
		return rv;
	}

	return bdb_cache_next_entry(cur, dn, entry);
}

int bdb_cache_print_entries(char *dn) {
	DBT key, data;
	DBC *cur;
	memset(&key, 0, sizeof(DBT));
	memset(&data, 0, sizeof(DBT));
	key.data = strdup(dn);
	key.size = strlen(dn) + 1;
	key.flags = DB_DBT_REALLOC;
	data.flags = DB_DBT_REALLOC;

	dbp->cursor(dbp, NULL, &cur, 0);
	cur->c_get(cur, &key, &data, DB_FIRST);
	do {
		printf("%s\n", (char *)key.data);
	} while (cur->c_get(cur, &key, &data, DB_NEXT) == 0);

	cur->c_close(cur);
	free(key.data);
	free(data.data);
	return 0;
}

int bdb_cache_next_entry(DBC **cur, char **dn, CacheEntry *entry) {
	DBT key, data;
	int rv;

	memset(&key, 0, sizeof(DBT));
	key.flags = DB_DBT_REALLOC;
	memset(&data, 0, sizeof(DBT));
	data.flags = DB_DBT_REALLOC;

	if ((rv = (*cur)->c_get(*cur, &key, &data, DB_NEXT)) == DB_NOTFOUND) {
		return rv;
	} else if (rv != 0) {
		dbp->err(dbp, rv, "c_get");
		return rv;
	}

	/* skip master entry */
	if (strcmp(key.data, MASTER_KEY) == 0) {
		free(key.data);
		free(data.data);
		return bdb_cache_next_entry(cur, dn, entry);
	}

	if (*dn)
		free(*dn);
	*dn = strdup(key.data);

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "got %d bytes", data.size);

	if ((rv = parse_entry(data.data, data.size, entry)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "parsing entry failed: %s", *dn);
		printf("%d\n", data.size);
		free(key.data);
		free(data.data);
		return rv;
	}

	free(key.data);
	free(data.data);

	return 0;
}

int bdb_cache_free_cursor(DBC *cur) {
	return cur->c_close(cur);
}

int bdb_cache_close(void) {
	int rv = 0;

	if (dbp && (rv = dbp->close(dbp, 0)) != 0) {
		dbp->err(dbp, rv, "close");
	}
	dbp = NULL;
#ifdef WITH_DB42
	if ((rv = dbenvp->close(dbenvp, 0)) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "closing database environment failed");
	}
#endif
	if (lock_fp != NULL) {
		fclose(lock_fp);
		lock_fp = NULL;
	}
	return rv;
}
