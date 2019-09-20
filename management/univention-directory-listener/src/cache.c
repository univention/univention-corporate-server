/*
 * Univention Directory Listener
 *  ldap listener caching system
 *
 * Copyright 2004-2019 Univention GmbH
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

/* How it works:

   LDAP entries are cached here. If a modification takes place,
   the new LDAP entry is compared with the cache entry, and both,
   old and new entries, are passed to the handler modules.

   MDB provides a way to store and receive a chunk of data
   with a given key. However, we're not working with cache entries
   as chunks of data later, but use C structures. So we'll need to
   convert the C structure we can work with to chunks of data we
   can store in LMDB, and the other way around.

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
#include <lmdb.h>
#include <stdbool.h>
#include <assert.h>
#include <stdint.h>

#include <univention/config.h>

#include "common.h"
#include "cache.h"
#include "cache_dn.h"
#include "cache_lowlevel.h"
#include "cache_entry.h"
#include "network.h"
#include "signals.h"
#include "filter.h"
#include "utils.h"
#include "error.h"

/* id=0 is used for the root-dn='' in id2dn, but otherwise unused.
 * We can use it to store the MasterCacheEntry in id2entry. */
static DNID MASTER_KEY = 0;
#define MASTER_KEY_SIZE (sizeof(DNID))

char *cache_dir = "/var/lib/univention-directory-listener";
char *ldap_dir = "/var/lib/univention-ldap";

CacheMasterEntry cache_master_entry;

static MDB_env *env;
static MDB_dbi id2dn;
static MDB_dbi id2entry;
static int mdb_readonly = 0;
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

/*
int mdb_message_func(const char *msg, void *ctx) {
        univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
                        "%s\n", msg);
        return MDB_SUCCESS;
}
*/

#define ERROR_MDB(rv, msg) LOG(ERROR, "%s: failed: %s (%d)", msg, mdb_strerror(rv), rv)
#define ERROR_MDB_ABORT(rv, msg) \
	do { \
		ERROR_MDB(rv, msg); \
		abort(); \
	} while (0)

int cache_lock(void) {
	int rv, fd;
	char lock_file[PATH_MAX];

	assert(!lock_fp);

	rv = snprintf(lock_file, PATH_MAX, "%s/cache.lock", cache_dir);
	if (rv < 0 || rv >= PATH_MAX)
		abort();

	if ((lock_fp = fopen(lock_file, "a+e")) == NULL) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Could not open lock file [%s]", lock_file);
		exit(EXIT_FAILURE);
	}
	fd = fileno(lock_fp);

	if (lockf(fd, F_TLOCK, 0) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Could not get lock for database [%s]; "
		                                                    "Is another listener process running?\n",
		                 lock_file);
		exit(EXIT_FAILURE);
	}

	return fd;
}

static size_t determine_mapsize_from_ucr() {
#if __SIZEOF_POINTER__ == 8
	const size_t default_mapsize = 2147483648;  // 2 GB
#else
	const size_t default_mapsize = 1992294400;  // 1.9 GB
#endif
	size_t mapsize;
	const char ucr_var_mapsize[] = "listener/cache/mdb/maxsize";
	char *mapsize_str, *endptr;

	mapsize_str = univention_config_get_string(ucr_var_mapsize);
	if (mapsize_str) {
		errno = 0;
		mapsize = strtol(mapsize_str, &endptr, 10);
		free(mapsize_str);

		if ((errno == ERANGE && (mapsize == LONG_MAX || mapsize == LONG_MIN)) || (errno != 0 && mapsize == 0)) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_init: Error parsing value of UCR variable %s as number: %s", ucr_var_mapsize, strerror(errno));
			exit(EXIT_FAILURE);
		}
		if (endptr == mapsize_str) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_init: Value of UCR variable %s is not a number", ucr_var_mapsize);
			mapsize = default_mapsize;
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_init: using default mapsize: %zu", mapsize);
		} else {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "cache_init: using UCR defined mapsize: %zu", mapsize);
		}
	} else {
		mapsize = default_mapsize;
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "cache_init: using default mapsize: %zu", mapsize);
	}
	return mapsize;
}

int cache_init(char *cache_mdb_dir, int mdb_flags) {
	int rv;
	MDB_txn *cache_init_txn;
	int mdb_dbi_flags = MDB_INTEGERKEY;
	size_t mapsize = determine_mapsize_from_ucr();

	if ((mdb_flags & MDB_RDONLY) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "cache_init: MDB_RDONLY");
		mdb_readonly = MDB_RDONLY;
	} else {
		mdb_dbi_flags |= MDB_CREATE;
	}

	rv = mdb_env_create(&env);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_init: creating environment handle failed");
		ERROR_MDB_ABORT(rv, "mdb_env_create");
		return rv;
	}

	rv = mdb_env_set_mapsize(env, mapsize);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_init: setting mdb mapsize failed");
		ERROR_MDB_ABORT(rv, "mdb_env_set_mapsize");
		return rv;
	}

	rv = mdb_env_set_maxdbs(env, 2);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_init: setting mdb maxdbs failed");
		ERROR_MDB_ABORT(rv, "mdb_env_set_maxdbs");
		return rv;
	}

	rv = mdb_env_open(env, cache_mdb_dir, mdb_readonly, 0600);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_init: opening database failed");
		ERROR_MDB_ABORT(rv, "mdb_env_open");
		return rv;
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_init: Transaction begin");

	rv = mdb_txn_begin(env, NULL, mdb_readonly, &cache_init_txn);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_txn_begin");
		mdb_env_close(env);
		return rv;
	}

	rv = dntree_init(&id2dn, cache_init_txn, mdb_flags);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "dntree_init");
		mdb_txn_abort(cache_init_txn);
		mdb_env_close(env);
		return rv;
	}

	rv = mdb_dbi_open(cache_init_txn, "id2entry", mdb_dbi_flags, &id2entry);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_dbi_open");
		mdb_txn_abort(cache_init_txn);
		mdb_dbi_close(env, id2dn);
		mdb_env_close(env);
		return rv;
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "Transaction commit");

	rv = mdb_txn_commit(cache_init_txn);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_txn_commit");
		mdb_dbi_close(env, id2dn);
		mdb_dbi_close(env, id2entry);
		mdb_env_close(env);
		return rv;
	}

	setup_cache_filter();

	return 0;
}

int cache_set_schema_id(const NotifierID value) {
	int rv, fd, len;
	char file[PATH_MAX], buf[15];

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "Set Schema ID to %ld", value);
	len = snprintf(buf, sizeof buf, "%ld", value);
	if (len < 0 || len >= sizeof buf)
		return len;

	rv = snprintf(file, PATH_MAX, "%s/schema/id/id", ldap_dir);
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

int cache_get_schema_id(NotifierID *value, const long def) {
	FILE *fp;
	char file[PATH_MAX];
	int rv;

	*value = def;

	snprintf(file, PATH_MAX, "%s/schema/id/id", ldap_dir);
	if ((fp = fopen(file, "r")) == NULL)
		return 1;
	rv = fscanf(fp, "%ld", value);
	return fclose(fp) || (rv != 1);
}

int cache_set_int(char *key, const NotifierID value) {
	int rv;
	FILE *fp;
	char file[PATH_MAX], tmpfile[PATH_MAX];

	rv = snprintf(tmpfile, PATH_MAX, "%s/%s.tmp", cache_dir, key);
	if (rv < 0 || rv >= PATH_MAX)
		return rv;
	if ((fp = fopen(tmpfile, "w")) == NULL)
		abort_io("open", tmpfile);
	fprintf(fp, "%ld", value);
	rv = fclose(fp);
	if (rv != 0)
		abort_io("close", tmpfile);

	rv = snprintf(file, PATH_MAX, "%s/%s", cache_dir, key);
	if (rv < 0 || rv >= PATH_MAX)
		return rv;
	rv = rename(tmpfile, file);
	return rv;
}

int cache_get_int(char *key, NotifierID *value, const long def) {
	FILE *fp;
	char file[PATH_MAX];
	int rv;

	*value = def;

	snprintf(file, PATH_MAX, "%s/%s", cache_dir, key);
	if ((fp = fopen(file, "r")) == NULL)
		return 1;
	rv = fscanf(fp, "%ld", value);
	return fclose(fp) || (rv != 1);
}

int cache_get_master_entry(CacheMasterEntry *master_entry) {
	int rv;
	MDB_txn *read_txn;
	MDB_val key, data;

	memset(&key, 0, sizeof(MDB_val));
	memset(&data, 0, sizeof(MDB_val));

	key.mv_data = &MASTER_KEY;
	key.mv_size = MASTER_KEY_SIZE;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_get_master_entry: Read Transaction begin");

	rv = mdb_txn_begin(env, NULL, MDB_RDONLY, &read_txn);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_txn_begin");
		return rv;
	}

	rv = mdb_get(read_txn, id2entry, &key, &data);
	if (rv == MDB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_get_master_entry: Read Transaction abort"
		                                                  ": %s",
		                 mdb_strerror(rv));
		mdb_txn_abort(read_txn);
		return rv;
	} else if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_get_master_entry: reading master entry from database failed");
		ERROR_MDB_ABORT(rv, "mdb_get");
		mdb_txn_abort(read_txn);
		return rv;
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_get_master_entry: Read Transaction abort");
	mdb_txn_abort(read_txn);

	if (data.mv_size != sizeof(CacheMasterEntry)) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_get_master_entry: master entry has unexpected length");
		return 1;
	}

	memcpy(master_entry, data.mv_data, sizeof(CacheMasterEntry));

	return MDB_SUCCESS;
}

int cache_update_master_entry(CacheMasterEntry *master_entry) {
	int rv;
	MDB_txn *write_txn;
	MDB_val key, data;

	memset(&key, 0, sizeof(MDB_val));
	memset(&data, 0, sizeof(MDB_val));

	key.mv_data = &MASTER_KEY;
	key.mv_size = MASTER_KEY_SIZE;

	data.mv_data = (void *)master_entry;
	data.mv_size = sizeof(CacheMasterEntry);

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_update_master_entry: Transaction begin");
	if ((rv = mdb_txn_begin(env, NULL, 0, &write_txn)) != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_txn_begin");
		return rv;
	}
	rv = mdb_put(write_txn, id2entry, &key, &data, 0);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_update_master_entry: storing master entry in database failed");
		ERROR_MDB_ABORT(rv, "mdb_put");
		mdb_txn_abort(write_txn);
		return rv;
	}
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_update_master_entry: Transaction commit");
	if ((rv = mdb_txn_commit(write_txn)) != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_update_master_entry: storing master entry in database failed");
		ERROR_MDB_ABORT(rv, "mdb_txn_commit");
		return rv;
	}

	return MDB_SUCCESS;
}

/* XXX: The NotifierID is passed for future use. Once the journal is
   implemented, entries other than the most recent one can be returned.
   At the moment, the id parameters for cache_update_entry, and
   cache_delete_entry do nothing */
static inline int cache_update_entry_in_transaction(NotifierID id, char *dn, CacheEntry *entry, MDB_cursor **id2dn_cursor_pp) {
	int rv;
	DNID dnid;
	MDB_txn *write_txn;
	MDB_val key, data;
	u_int32_t tmp_size = 0;

	memset(&data, 0, sizeof(MDB_val));
	rv = unparse_entry(&data.mv_data, &tmp_size, entry);
	data.mv_size = tmp_size;
	if (rv != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_update_entry: unparsing entry failed");
		return rv;
	}

	signals_block();

	rv = dntree_get_id4dn(*id2dn_cursor_pp, dn, &dnid, true);
	if (rv != MDB_SUCCESS) {
		goto out;
	}

	key.mv_data = &dnid;
	key.mv_size = sizeof(DNID);

	write_txn = mdb_cursor_txn(*id2dn_cursor_pp);
	rv = mdb_put(write_txn, id2entry, &key, &data, 0);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_update_entry: storing entry in database failed: %s", dn);
		ERROR_MDB_ABORT(rv, "mdb_put");
		goto out;
	}
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "put %zu bytes for %s", data.mv_size, dn);

out:
	signals_unblock();

	free(data.mv_data);
	return rv;
}

inline int cache_update_entry(NotifierID id, char *dn, CacheEntry *entry) {
	int rv;
	MDB_txn *write_txn;
	MDB_cursor *id2dn_write_cursor_p;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_update_entry: Transaction begin");
	rv = mdb_txn_begin(env, NULL, 0, &write_txn);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_txn_begin");
		return rv;
	}

	rv = mdb_cursor_open(write_txn, id2dn, &id2dn_write_cursor_p);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_cursor_open");
		return rv;
	}

	rv = cache_update_entry_in_transaction(id, dn, entry, &id2dn_write_cursor_p);

	mdb_cursor_close(id2dn_write_cursor_p);

	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_update_entry: Transaction abort");
		mdb_txn_abort(write_txn);
		return rv;
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_update_entry: Transaction commit");
	rv = mdb_txn_commit(write_txn);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_update_entry: storing updated entry in database failed");
		ERROR_MDB_ABORT(rv, "mdb_txn_commit");
		return rv;
	}

	return rv;
}

int cache_update_entry_lower(NotifierID id, char *dn, CacheEntry *entry) {
	char *lower_dn;
	int rv = 0;

	if (cache_filter.filter && cache_entry_ldap_filter_match(cache_filters, dn, entry)) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "Not caching %s, filtered out.", dn);
		return rv;
	}

	lower_dn = lower_utf8(dn);
	rv = cache_update_entry(id, lower_dn, entry);

	free(lower_dn);
	return rv;
}

static inline int cache_delete_entry_in_transaction(NotifierID id, char *dn, MDB_cursor **id2dn_cursor_pp) {
	int rv;
	DNID dnid;
	MDB_txn *write_txn;
	MDB_val key;

	signals_block();

	rv = dntree_get_id4dn(*id2dn_cursor_pp, dn, &dnid, false);
	if (rv != MDB_SUCCESS) {
		signals_unblock();
		return rv;
	}

	key.mv_data = &dnid;
	key.mv_size = sizeof(DNID);

	write_txn = mdb_cursor_txn(*id2dn_cursor_pp);
	rv = mdb_del(write_txn, id2entry, &key, 0);
	if (rv != MDB_SUCCESS && rv != MDB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_delete_entry: removing from database failed: %s", dn);
		ERROR_MDB_ABORT(rv, "mdb_del");
		signals_unblock();
		return rv;
	}

	rv = dntree_del_id(*id2dn_cursor_pp, dnid);
	if (rv != MDB_SUCCESS) {
		signals_unblock();
		return rv;
	}

	signals_unblock();

	return rv;
}

int cache_delete_entry(NotifierID id, char *dn) {
	int rv;
	MDB_txn *write_txn;
	MDB_cursor *id2dn_write_cursor_p;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_delete_entry: Transaction begin");
	rv = mdb_txn_begin(env, NULL, 0, &write_txn);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_txn_begin");
		return rv;
	}

	rv = mdb_cursor_open(write_txn, id2dn, &id2dn_write_cursor_p);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_cursor_open");
		return rv;
	}

	rv = cache_delete_entry_in_transaction(id, dn, &id2dn_write_cursor_p);

	mdb_cursor_close(id2dn_write_cursor_p);

	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_update_entry: Transaction abort");
		mdb_txn_abort(write_txn);
		return rv;
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_delete_entry: Transaction commit");
	rv = mdb_txn_commit(write_txn);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_delete_entry: storing entry removal from database failed");
		ERROR_MDB_ABORT(rv, "mdb_txn_commit");
	}

	return rv;
}

int cache_delete_entry_lower_upper(NotifierID id, char *dn) {
	char *lower_dn;
	bool mixedcase = false;
	int rv, rv2;

	// convert to a lowercase dn
	lower_dn = lower_utf8(dn);
	rv = cache_delete_entry(id, lower_dn);
	if (strcmp(dn, lower_dn) != 0) {
		mixedcase = true;
		// try again with original dn
		rv2 = cache_delete_entry(id, dn);
	}

	free(lower_dn);
	if (mixedcase) {
		return rv ? rv2 : rv;  // if rv was bad (!=0) return rv2, otherwise return rv
	} else {
		return rv;
	}
}

int cache_update_or_deleteifunused_entry(NotifierID id, char *dn, CacheEntry *entry, MDB_cursor **id2dn_cursor_pp) {
	if (entry->module_count == 0)
		return cache_delete_entry_in_transaction(id, dn, id2dn_cursor_pp);
	else
		return cache_update_entry_in_transaction(id, dn, entry, id2dn_cursor_pp);
}

int cache_get_entry(char *dn, CacheEntry *entry) {
	int rv;
	DNID dnid;
	MDB_txn *read_txn;
	MDB_cursor *id2dn_read_cursor_p;
	MDB_val key, data;

	memset(&key, 0, sizeof(MDB_val));
	memset(&data, 0, sizeof(MDB_val));
	memset(entry, 0, sizeof(CacheEntry));

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_get_entry: Read Transaction begin");

	rv = mdb_txn_begin(env, NULL, MDB_RDONLY, &read_txn);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_txn_begin");
		return rv;
	}

	rv = mdb_cursor_open(read_txn, id2dn, &id2dn_read_cursor_p);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_cursor_open");
		mdb_txn_abort(read_txn);
		return rv;
	}

	rv = dntree_get_id4dn(id2dn_read_cursor_p, dn, &dnid, false);
	mdb_cursor_close(id2dn_read_cursor_p);
	if (rv == MDB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_get_entry: Read Transaction abort");
		mdb_txn_abort(read_txn);
		return rv;
	}

	key.mv_data = &dnid;
	key.mv_size = sizeof(DNID);

	// signals_block();	// TODO: Is this really required?
	rv = mdb_get(read_txn, id2entry, &key, &data);
	// signals_unblock();

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_get_entry: Read Transaction abort");
	mdb_txn_abort(read_txn);

	if (rv == MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "got %zu bytes for %s", data.mv_size, dn);
	} else if (rv == MDB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "cache_get_entry: no cache entry found for %s", dn);
		return rv;
	} else {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "reading %s from database failed", dn);
		ERROR_MDB_ABORT(rv, "mdb_get");
		return rv;
	}

	assert(data.mv_size <= UINT32_MAX);
	rv = parse_entry(data.mv_data, data.mv_size, entry);
	if (rv != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_get_entry: parsing entry failed");
		exit(1);
	}

	return rv;
}

int cache_get_entry_lower_upper(char *dn, CacheEntry *entry) {
	char *lower_dn;
	bool mixedcase = false;
	int rv;

	// convert to a lowercase dn
	lower_dn = lower_utf8(dn);
	if (strcmp(dn, lower_dn) != 0) {
		mixedcase = true;
	}

	rv = cache_get_entry(lower_dn, entry);
	if (rv == MDB_NOTFOUND && mixedcase) {
		// try again with original dn
		rv = cache_get_entry(dn, entry);
	}

	free(lower_dn);
	return rv;
}

int cache_first_entry(MDB_cursor **id2entry_read_cursor_pp, MDB_cursor **id2dn_read_cursor_pp, char **dn, CacheEntry *entry) {
	MDB_txn *read_txn;
	int rv;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_first_entry: Transaction begin");

	rv = mdb_txn_begin(env, NULL, mdb_readonly, &read_txn);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_txn_begin");
		return rv;
	}

	rv = mdb_cursor_open(read_txn, id2entry, id2entry_read_cursor_pp);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_cursor_open");
		mdb_txn_abort(read_txn);
		return rv;
	}

	rv = mdb_cursor_open(read_txn, id2dn, id2dn_read_cursor_pp);
	if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_cursor_open");
		mdb_txn_abort(read_txn);
		return rv;
	}

	/*
	// mdb_reader_list(env, &mdb_message_func, NULL);
	MDB_envinfo stat;
	MDB_env *env = mdb_txn_env(read_txn);
	mdb_env_info(env, &stat);
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL,
	        "LAST COMMITTED TXN: %zu", stat.me_last_txnid);
	*/

	return cache_next_entry(id2entry_read_cursor_pp, id2dn_read_cursor_pp, dn, entry);
}

int cache_next_entry(MDB_cursor **id2entry_read_cursor_pp, MDB_cursor **id2dn_read_cursor_pp, char **dn, CacheEntry *entry) {
	MDB_val key, data;
	DNID dnid;
	int rv;

	memset(&key, 0, sizeof(MDB_val));
	memset(&data, 0, sizeof(MDB_val));

	/* Get the next entry data */
	rv = mdb_cursor_get(*id2entry_read_cursor_pp, &key, &data, MDB_NEXT);
	if (rv == MDB_NOTFOUND) {
		return rv;
	} else if (rv != MDB_SUCCESS) {
		ERROR_MDB_ABORT(rv, "mdb_cursor_get");
		return rv;
	}

	// skip root node
	dnid = *(DNID *)key.mv_data;
	if (dnid == MASTER_KEY) {
		return cache_next_entry(id2entry_read_cursor_pp, id2dn_read_cursor_pp, dn, entry);
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "got %zu bytes", data.mv_size);

	assert(data.mv_size <= UINT32_MAX);
	rv = parse_entry(data.mv_data, (u_int32_t)data.mv_size, entry);
	if (rv != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_next_entry: parsing entry failed: %s", *dn);
		printf("%zu\n", data.mv_size);
		return rv;
	}

	/* Get the corresponding dn */
	if (*dn) {
		free(*dn);
		*dn = NULL;
	}

	rv = dntree_lookup_dn4id(*id2dn_read_cursor_pp, dnid, dn);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_next_entry: DB corruption, DN entry for id %d not found", *(int *)key.mv_data);
		ERROR_MDB_ABORT(rv, "mdb_get");
		return rv;
	}

	return 0;
}

int cache_free_cursor(MDB_cursor *id2entry_read_cursor_pp, MDB_cursor *id2dn_read_cursor_pp) {
	int rv = 0;
	MDB_txn *read_txn;

	read_txn = mdb_cursor_txn(id2entry_read_cursor_pp);
	mdb_cursor_close(id2entry_read_cursor_pp);
	mdb_cursor_close(id2dn_read_cursor_pp);

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "cache_free_cursor: Transaction commit");
	rv = mdb_txn_commit(read_txn);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "cache_free_cursor: Transaction commit failed");
		ERROR_MDB_ABORT(rv, "mdb_txn_commit");
	}
	return rv;
}

void cache_close(void) {
	mdb_close(env, id2dn);
	mdb_close(env, id2entry);
	mdb_env_close(env);

	if (lock_fp != NULL) {
		fclose(lock_fp);
		lock_fp = NULL;
	}
}
