/* 
 * Samba LDB module univention_ldb_log
 *	LDB Module for monitoring LDB operations
 *
 * Copyright 2011-2019 Univention GmbH
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

/* univention_ldb_log was derived from the tests/sample_module

   Unix SMB/CIFS implementation.
   Samba utility functions
   Copyright (C) Jelmer Vernooij <jelmer@samba.org> 2007

     ** NOTE! The following LGPL license applies to the ldb
     ** library. This does NOT imply that all of Samba is released
     ** under the LGPL
   
   This library is free software; you can redistribute it and/or
   modify it under the terms of the GNU Lesser General Public
   License as published by the Free Software Foundation; either
   version 3 of the License, or (at your option) any later version.

   This library is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
   Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public
   License along with this library; if not, see <https://www.gnu.org/licenses/>.
*/

#include "ldb_module.h"
#include <univention/config.h>

static char *LOGFILENAME = "/tmp/univention_ldb_log_module.log";

static int univention_ldb_log(struct ldb_module *module, struct ldb_request *req)
{
	struct ldb_context *ldb;
	ldb = ldb_module_get_ctx(module);
	int i, j;

	FILE *fp;
	fp=fopen(LOGFILENAME, "a");

	// code copied from ldb.c
	TALLOC_CTX *tmp_ctx = talloc_new(req);
	switch (req->operation) {
	case LDB_SEARCH:
		fprintf(fp, "ldb_trace_request: SEARCH\n");
		fprintf(fp, " dn: %s\n",
			      ldb_dn_is_null(req->op.search.base)?"<rootDSE>":
			      ldb_dn_get_linearized(req->op.search.base));
		fprintf(fp, " scope: %s\n", 
			  req->op.search.scope==LDB_SCOPE_BASE?"base":
			  req->op.search.scope==LDB_SCOPE_ONELEVEL?"one":
			  req->op.search.scope==LDB_SCOPE_SUBTREE?"sub":"UNKNOWN");
		fprintf(fp, " expr: %s\n", 
			  ldb_filter_from_tree(tmp_ctx, req->op.search.tree));
		if (req->op.search.attrs == NULL) {
			fprintf(fp, " attr: <ALL>\n");
		} else {
			for (i=0; req->op.search.attrs[i]; i++) {
				fprintf(fp, " attr: %s\n", req->op.search.attrs[i]);
			}
		}
		break;
	case LDB_DELETE:
		fprintf(fp, "ldb_trace_request: DELETE\n");
		fprintf(fp, " dn: %s\n", 
			      ldb_dn_get_linearized(req->op.del.dn));
		break;
	case LDB_RENAME:
		fprintf(fp, "ldb_trace_request: RENAME\n");
		fprintf(fp, " olddn: %s\n", 
			      ldb_dn_get_linearized(req->op.rename.olddn));
		fprintf(fp, " newdn: %s\n", 
			      ldb_dn_get_linearized(req->op.rename.newdn));
		break;
	case LDB_EXTENDED:
		fprintf(fp, "ldb_trace_request: EXTENDED\n");
		fprintf(fp, " oid: %s\n", req->op.extended.oid);
		fprintf(fp, " data: %s\n", req->op.extended.data?"yes":"no");
		break;
	case LDB_ADD:
		fprintf(fp, "ldb_trace_request: ADD\n");
		fprintf(fp, "%s\n", 
			      ldb_ldif_message_string(ldb, tmp_ctx, 
						      LDB_CHANGETYPE_ADD, 
						      req->op.add.message));
		break;
	case LDB_MODIFY:
		fprintf(fp, "ldb_trace_request: MODIFY\n");
		fprintf(fp, "%s\n", 
			      ldb_ldif_message_string(ldb, tmp_ctx, 
						      LDB_CHANGETYPE_ADD, 
						      req->op.mod.message));
		break;
	case LDB_REQ_REGISTER_CONTROL:
		fprintf(fp, "ldb_trace_request: REGISTER_CONTROL\n");
		fprintf(fp, "%s\n", 
			      req->op.reg_control.oid);
		break;
	case LDB_REQ_REGISTER_PARTITION:
		fprintf(fp, "ldb_trace_request: REGISTER_PARTITION\n");
		fprintf(fp, "%s\n", 
			      ldb_dn_get_linearized(req->op.reg_partition.dn));
		break;
	default:
		fprintf(fp, "ldb_trace_request: UNKNOWN(%u)\n", 
			      req->operation);
		break;
	}

	fclose(fp);
	talloc_free(tmp_ctx);

	return ldb_next_request(module, req);
}

static int univention_ldb_log_add(struct ldb_module *module, struct ldb_request *req)
{
	return univention_ldb_log(module, req);
}

static int univention_ldb_log_modify(struct ldb_module *module, struct ldb_request *req)
{
	return univention_ldb_log(module, req);
}

static int univention_ldb_log_delete(struct ldb_module *module, struct ldb_request *req)
{
	return univention_ldb_log(module, req);
}

static int univention_ldb_log_init_context(struct ldb_module *module)
{
	return ldb_next_init(module);
}

static struct ldb_module_ops ldb_univention_ldb_log_module_ops = {
	.name	= "univention_ldb_log",
	.add	= univention_ldb_log_add,
	.modify	= univention_ldb_log_modify,
	.del	= univention_ldb_log_delete,
	.init_context	= univention_ldb_log_init_context,
};

int ldb_univention_ldb_log_init(const char *version)
{
	if (strcmp(version, LDB_VERSION) != 0) {
		fprintf(stderr, "ldb: WARNING: module version mismatch in %s : ldb_version=%s module_version=%s\n", __FILE__, version, LDB_VERSION);
	}
	return ldb_register_module(&ldb_univention_ldb_log_module_ops);
}
