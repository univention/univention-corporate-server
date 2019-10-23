/*
 * Univention Directory Listener
 *  implementation for LMDB dntree adjacency list
 *
 * Copyright 2016-2019 Univention GmbH
 * Copyright 2016-2017 Arvid Requate
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

/*
 * Derived From: This code is derived from dn2id.c written by Howard Chu.
 * The code of dn2id.c has been published under OpenLDAP Public License.
 *
 * A copy of this license is available in the file LICENSE in the
 * top-level directory of the distribution or, alternatively, at
 * <http://www.OpenLDAP.org/license.html>.
 */

#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <unistd.h>
#include <assert.h>
#include "cache_dn.h"
#include <univention/debug.h>

static int mdb_dupsort(const MDB_val *a, const MDB_val *b) {
	int diff;
	subDN *sdn_a, *sdn_b;

	sdn_a = (subDN *)a->mv_data;
	sdn_b = (subDN *)b->mv_data;

	diff = sdn_a->type - sdn_b->type;
	if (diff) {
		return diff;
	}
	if (sdn_a->type == SUBDN_TYPE_LINK) {
		return strcmp(sdn_a->data, sdn_b->data);
	} else {
		return 0;
	}
}

static unsigned int num_rdns(LDAPDN dn) {
	unsigned int iRDN;

	for (iRDN = 0; dn[iRDN]; iRDN++)
		;

	return iRDN;
}

/* climb the dntree */
static int dntree_lookup_id4ldapdn(MDB_cursor *cur, LDAPDN dn, DNID *dnid_out, int *found_out) {
	int rv = MDB_NOTFOUND, iRDN, found;
	MDB_val key, data;
	DNID parent, id = 0;
	char *rdn;
	subDN *subdn;

	key.mv_size = sizeof(DNID);

	found = 0;
	iRDN = num_rdns(dn);
	for (iRDN--; iRDN >= 0; iRDN--) {
		rv = ldap_rdn2str(dn[iRDN], &rdn, LDAP_DN_FORMAT_LDAPV3);
		if (rv != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: ldap_rdn2str failed: %s (%d)", __func__, ldap_err2string(rv), rv);
			return rv;
		}

		key.mv_data = &parent;
		parent = id;

		data.mv_size = sizeof(subDN) + strlen(rdn);
		subdn = calloc(1, data.mv_size);
		if (subdn == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: calloc failed", __func__);
			ldap_memfree(rdn);
			abort();
		}
		subdn->type = SUBDN_TYPE_LINK;
		strcpy(subdn->data, rdn);
		ldap_memfree(rdn);
		data.mv_data = subdn;

		rv = mdb_cursor_get(cur, &key, &data, MDB_GET_BOTH);
		free(subdn);

		if (rv == MDB_NOTFOUND) {
			break;
		}
		if (rv != MDB_SUCCESS) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: mdb_cursor_get failed: %s (%d)", __func__, mdb_strerror(rv), rv);
			return rv;
		};

		subdn = (subDN *)data.mv_data;
		id = subdn->id;
		found++;
	}

	if (rv == MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "%s: found id=%lu", __func__, id);
	} else if (rv != MDB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: failed: %s (%d)", __func__, mdb_strerror(rv), rv);
	}

	*dnid_out = id;
	if (found_out) {
		*found_out = found;
	};

	return rv;
}

int dntree_lookup_dn4id(MDB_cursor *cur, DNID dnid, char **dn) {
	int rv;
	MDB_val key, data;
	subDN *subdn;
	DNID id = dnid;

	key.mv_size = sizeof(DNID);
	key.mv_data = &id;

	data.mv_size = sizeof(subDN);
	data.mv_data = &(subDN){0, SUBDN_TYPE_NODE, ""};

	rv = mdb_cursor_get(cur, &key, &data, MDB_GET_BOTH);
	data.mv_data = NULL;
	data.mv_size = 0;

	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: mdb_cursor_get (MDB_GET_BOTH): %s (%d)", __func__, mdb_strerror(rv), rv);
		return rv;
	};

	// Workaround for (ITS#8393) LMDB - MDB_GET_BOTH broken on non-dup value
	rv = mdb_cursor_get(cur, &key, &data, MDB_GET_CURRENT);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: mdb_cursor_get: %s (%d)", __func__, mdb_strerror(rv), rv);
		return rv;
	};

	/*
	// or simply use this instead of MDB_GET_BOTH + MDB_GET_CURRENT:
	MDB_txn		*txn;
	MDB_dbi		dbi;
	txn = mdb_cursor_txn(cur);
	dbi = mdb_cursor_dbi(cur);
	rv = mdb_get(txn, dbi, &key, &data);
	if (rv != MDB_SUCCESS) {
	        univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR,
	                "%s: mdb_get: %s (%d)",
	                __func__, mdb_strerror(rv), rv);
	        return rv;
	};
	*/

	subdn = (subDN *)data.mv_data;

	*dn = strdup(subdn->data);
	if (*dn == NULL) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: strdup failed", __func__);
		abort();
	}

	return rv;
}

static int next_free_dnid(MDB_cursor *cur, DNID *dnid_out) {
	int rv;
	MDB_val key;

	rv = mdb_cursor_get(cur, &key, NULL, MDB_LAST);
	if (rv == MDB_SUCCESS) {
		*dnid_out = (*(DNID *)key.mv_data) + 1;
		return rv;
	} else if (rv == MDB_NOTFOUND) {
		*dnid_out = 1;
		return MDB_SUCCESS;
	} else {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: mdb_cursor_get: %s (%d)", __func__, mdb_strerror(rv), rv);
		return rv;
	}
}

static int dntree_add_id(MDB_cursor *write_cursor_p, DNID child, LDAPDN dn, DNID parent) {
	int rv;
	MDB_val key, data;
	DNID id;
	char *rdn_str;
	char *dn_str;
	size_t dn_len;
	size_t rdn_len;
	subDN *subdn;

	key.mv_size = sizeof(DNID);
	key.mv_data = &id;
	id = parent;

	rv = ldap_dn2str(dn, &dn_str, LDAP_DN_FORMAT_LDAPV3);
	if (rv != LDAP_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: ldap_dn2str failed: %s (%d)", __func__, ldap_err2string(rv), rv);
		return rv;
	}

	rv = ldap_rdn2str(dn[0], &rdn_str, LDAP_DN_FORMAT_LDAPV3);
	if (rv != LDAP_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: ldap_rdn2str failed: %s (%d)", __func__, ldap_err2string(rv), rv);
		ldap_memfree(dn_str);
		return rv;
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "%s: child=%lu, parent=%lu: \"%s\"", __func__, child, parent, rdn_str);

	dn_len = strlen(dn_str);
	subdn = calloc(1, sizeof(subDN) + dn_len);
	if (subdn == NULL) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: calloc failed", __func__);
		ldap_memfree(dn_str);
		ldap_memfree(rdn_str);
		abort();
	}
	rdn_len = strlen(rdn_str);
	assert(dn_len >= rdn_len);
	data.mv_size = sizeof(subDN) + rdn_len;
	subdn->type = SUBDN_TYPE_LINK;
	subdn->id = child;
	strcpy(subdn->data, rdn_str);
	ldap_memfree(rdn_str);
	data.mv_data = subdn;

	// Store subdn link
	rv = mdb_cursor_put(write_cursor_p, &key, &data, MDB_NODUPDATA);

	// Store subdn node
	if (rv == MDB_SUCCESS) {
		id = child;

		data.mv_size = sizeof(subDN) + dn_len;
		subdn->type = SUBDN_TYPE_NODE;
		subdn->id = parent;  // backlink
		strcpy(subdn->data, dn_str);

		rv = mdb_cursor_put(write_cursor_p, &key, &data, MDB_NODUPDATA);
		if (rv != MDB_SUCCESS) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: mdb_cursor_put failed for child %lu: %s (%d)", __func__, id, mdb_strerror(rv), rv);
			abort();
		}
	} else {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: mdb_cursor_put failed for parent %lu: %s (%d)", __func__, id, mdb_strerror(rv), rv);
		abort();
	}

	ldap_memfree(dn_str);
	free(subdn);

	return rv;
}

static int dntree_has_children(MDB_cursor *local_cursor, DNID dnid) {
	int rv;
	size_t values;
	MDB_val key, data;

	key.mv_size = sizeof(DNID);
	key.mv_data = &dnid;

	rv = mdb_cursor_get(local_cursor, &key, &data, MDB_SET);
	if (rv != MDB_SUCCESS) {
		return rv;
	}

	rv = mdb_cursor_count(local_cursor, &values);
	if (rv == MDB_SUCCESS && values < 2) {
		rv = MDB_NOTFOUND;
	}
	return rv;
}

int dntree_del_id(MDB_cursor *write_cursor_p, DNID dnid) {
	int rv;
	MDB_val key, data;
	MDB_cursor *local_read_cursor_p;
	MDB_txn *txn;
	MDB_dbi dbi;

	txn = mdb_cursor_txn(write_cursor_p);
	dbi = mdb_cursor_dbi(write_cursor_p);
	rv = mdb_cursor_open(txn, dbi, &local_read_cursor_p);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: mdb_cursor_open: %s (%d)", __func__, mdb_strerror(rv), rv);
		abort();
		return rv;
	}

	rv = dntree_has_children(local_read_cursor_p, dnid);
	if (rv == MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: delete failed:"
		                                                    " subordinate objects must be deleted first",
		                 __func__);
		mdb_cursor_close(local_read_cursor_p);
		return -1;
	} else if (rv != MDB_NOTFOUND) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: dntree_has_children failed: %s (%d)", __func__, mdb_strerror(rv), rv);
		abort();
		return -1;
	}
	mdb_cursor_close(local_read_cursor_p);

	// dntree_lookup_id4ldapdn positioned cursor on SUBDN_TYPE_LINK node below parent's key
	rv = mdb_cursor_del(write_cursor_p, 0);

	if (rv == MDB_SUCCESS) {
		key.mv_size = sizeof(DNID);
		key.mv_data = &dnid;
		rv = mdb_cursor_get(write_cursor_p, &key, &data, MDB_SET);
		if (rv == MDB_SUCCESS) {
			rv = mdb_cursor_del(write_cursor_p, 0);
		}
	}

	if (rv == MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "%s: deleted id=%lu", __func__, dnid);
	}

	return rv;
}


static int dntree_get_id4ldapdn(MDB_cursor *write_cursor_p, LDAPDN dn, DNID *dnid_out) {
	int rv, found;
	DNID id, parent = 0;
	LDAPDN pdn;

	if (dn == NULL) {
		*dnid_out = 0;
		return MDB_SUCCESS;
	}

	rv = dntree_lookup_id4ldapdn(write_cursor_p, dn, &id, &found);
	if (rv == MDB_NOTFOUND) {
		pdn = &dn[1];
		if (num_rdns(pdn) != found) {
			rv = dntree_get_id4ldapdn(write_cursor_p, pdn, &parent);
			if (rv != MDB_SUCCESS) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: failed: %s (%d)", __func__, mdb_strerror(rv), rv);
				return rv;
			}
		} else {
			parent = id;
		}
		rv = next_free_dnid(write_cursor_p, &id);
		if (rv != MDB_SUCCESS) {
			return rv;
		}
		rv = dntree_add_id(write_cursor_p, id, dn, parent);
	}

	*dnid_out = id;

	return rv;
}

int dntree_get_id4dn(MDB_cursor *id2dn_cursor_p, char *dn, DNID *dnid, bool create) {
	int rv;
	LDAPDN ldapdn;

	rv = ldap_str2dn(dn, &ldapdn, LDAP_DN_FORMAT_LDAP);
	if (rv != LDAP_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: ldap_str2dn failed: %s (%d)", __func__, ldap_err2string(rv), rv);
		return rv;
	}

	if (ldapdn == NULL) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: ldap_str2dn NULL: %s (%d): %s", __func__, ldap_err2string(rv), rv, dn);
		return 1;
	}

	if (create == true) {
		rv = dntree_get_id4ldapdn(id2dn_cursor_p, ldapdn, dnid);
		if (rv != MDB_SUCCESS) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: failed for %s: %s (%d)", __func__, dn, mdb_strerror(rv), rv);
			abort();
		}
	} else {
		rv = dntree_lookup_id4ldapdn(id2dn_cursor_p, ldapdn, dnid, NULL);
		if (rv == MDB_NOTFOUND) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "%s: DN %s not in id2dn", __func__, dn);
		}
	}

	ldap_dnfree(ldapdn);
	return rv;
}


int dntree_init(MDB_dbi *dbi_p, MDB_txn *cache_init_txn_p, int mdb_flags) {
	int rv;
	MDB_val key, data;
	MDB_cursor *cur;
	int mdb_dbi_flags = MDB_INTEGERKEY | MDB_DUPSORT;
	bool readonly = (mdb_flags & MDB_RDONLY) != 0;

	if (readonly) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "dntree_init: MDB_RDONLY");
	} else {
		mdb_dbi_flags |= MDB_CREATE;
	}

	rv = mdb_dbi_open(cache_init_txn_p, "id2dn", mdb_dbi_flags, dbi_p);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: mdb_dbi_open: %s (%d)", __func__, mdb_strerror(rv), rv);
		abort();
		return rv;
	};
	rv = mdb_set_dupsort(cache_init_txn_p, *dbi_p, mdb_dupsort);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: mdb_set_dupsort: %s (%d)", __func__, mdb_strerror(rv), rv);
		abort();
		return rv;
	};

	if (readonly) {
		return MDB_SUCCESS;
	}

	rv = mdb_cursor_open(cache_init_txn_p, *dbi_p, &cur);
	if (rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: mdb_cursor_open: %s (%d)", __func__, mdb_strerror(rv), rv);
		abort();
		return rv;
	};

	// create root node
	key.mv_size = sizeof(DNID);
	key.mv_data = &(DNID){0};
	data.mv_size = sizeof(subDN);
	data.mv_data = &(subDN){0, SUBDN_TYPE_NODE, ""};
	// ignore exists
	mdb_cursor_put(cur, &key, &data, MDB_NODUPDATA);
	if (rv != MDB_KEYEXIST && rv != MDB_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "%s: mdb_cursor_put: %s (%d)", __func__, mdb_strerror(rv), rv);
		abort();
	}
	// not strictly required, mdb_txn_commit does it for write txn
	mdb_cursor_close(cur);

	return MDB_SUCCESS;
}
