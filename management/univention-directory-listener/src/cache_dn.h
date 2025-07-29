/*
 * Univention Directory Listener
 *  header information for cache_dn.c
 *
 * SPDX-FileCopyrightText: 2016-2025 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#ifndef _DNTREE_H_
#define _DNTREE_H_

#include <stdbool.h>
#include <lmdb.h>
#include <ldap.h>

#define SUBDN_TYPE_NODE 0
#define SUBDN_TYPE_LINK 1

typedef unsigned char SUBDNTYPE;
typedef unsigned long DNID;
typedef struct subDN {
	DNID id;
	SUBDNTYPE type;
	char data[1];
} subDN;

int dntree_init(MDB_dbi *dbi_ptr, MDB_txn *write_txn_p, int mdb_flags);
int dntree_get_id4dn(MDB_cursor *cursor, char *dn, DNID *dnid, bool create);
int dntree_lookup_dn4id(MDB_cursor *cur, DNID dnid, char **dn);
int dntree_del_id(MDB_cursor *cursor, DNID dnid);

#endif /* _DNTREE_H_ */
