/*
 * OpenLDAP overlay implementing Active Directory compatible
 * LDAP_MATCHING_RULE_IN_CHAIN / LDAP_MATCHING_RULE_TRANSITIVE_EVAL
 * OID: 1.2.840.113556.1.4.1941
 *
 * This overlay rewrites filters like
 *   (member:1.2.840.113556.1.4.1941:=uid=user,dc=example,dc=com)
 * to an OR filter containing the original DN and all recursively discovered
 * parent DNs for the asserted DN within the current backend suffix.
 *
 * Default behaviour is ACL respecting: internal recursive searches use the
 * original operation identity. With inchain-ignore-acls TRUE, internal searches
 * are evaluated as the database rootdn and therefore bypass OpenLDAP ACLs.
 */

// FIXME: assign a OID for the config schema from OpenLDAP: 1.3.6.1.4.1.4203.666.11.*

#include "portable.h"

#include <stdio.h>
#include <ac/string.h>
#include <ac/stdlib.h>

#include "slap.h"
#include "slap-config.h"

#define INCHAIN_OID "1.2.840.113556.1.4.1941"
#define LDAP_SYNTAX_DN_OID "1.3.6.1.4.1.1466.115.121.1.12"

/* Safety defaults. Keep these deliberately conservative: every expanded
 * frontier node requires one internal equality lookup, and a missing equality
 * index on the chosen DN-valued attribute would otherwise amplify into many
 * sequential subtree scans.
 */
#define INCHAIN_DEFAULT_MAX_DEPTH 16
#define INCHAIN_DEFAULT_MAX_NODES 1024
#define INCHAIN_DEFAULT_MAX_SEARCHES 256
#define INCHAIN_DNSET_BUCKETS 2048
#define INCHAIN_MAX_FILTER_DEPTH 64

typedef struct inchain_attr {
	AttributeDescription *ad;
	struct inchain_attr *next;
} inchain_attr;

typedef struct inchain_info {
	/* Optional allowlist. Empty means: allow all DN-syntax attributes. */
	inchain_attr *attrs;
	int max_depth;
	int max_nodes;
	int max_searches;
	int ignore_acls;
} inchain_info;

typedef struct dn_node {
	BerValue ndn;
	struct dn_node *next;
	struct dn_node *bucket_next;
} dn_node;

typedef struct dn_set {
	dn_node *head;
	dn_node **buckets;
	unsigned bucket_count;
	int count;
} dn_set;

enum {
	IC_ATTR = 1,
	IC_MAX_DEPTH,
	IC_MAX_NODES,
	IC_MAX_SEARCHES,
	IC_IGNORE_ACLS
};

static ConfigDriver inchain_cf;

static ConfigTable inchaincfg[] = {
	{
		"inchain-attr", "attribute", 2, 2, 0,
		ARG_MAGIC | IC_ATTR, inchain_cf,
		"( 1.3.6.1.4.1.64020.142857.369.1.1 "
			"NAME 'olcInChainAttr' "
			"DESC 'Optional DN-valued attribute allowlist for LDAP_MATCHING_RULE_IN_CHAIN' "
			"EQUALITY caseIgnoreMatch "
			"SYNTAX 1.3.6.1.4.1.1466.115.121.1.15 )",
		NULL, NULL
	},
	{
		"inchain-max-depth", "integer", 2, 2, 0,
		ARG_INT | ARG_MAGIC | IC_MAX_DEPTH, inchain_cf,
		"( 1.3.6.1.4.1.64020.142857.369.1.2 "
			"NAME 'olcInChainMaxDepth' "
			"DESC 'Maximum recursive depth for LDAP_MATCHING_RULE_IN_CHAIN' "
			"EQUALITY integerMatch "
			"SYNTAX 1.3.6.1.4.1.1466.115.121.1.27 SINGLE-VALUE )",
		NULL, NULL
	},
	{
		"inchain-max-nodes", "integer", 2, 2, 0,
		ARG_INT | ARG_MAGIC | IC_MAX_NODES, inchain_cf,
		"( 1.3.6.1.4.1.64020.142857.369.1.3 "
			"NAME 'olcInChainMaxNodes' "
			"DESC 'Maximum number of expanded DNs for LDAP_MATCHING_RULE_IN_CHAIN' "
			"EQUALITY integerMatch "
			"SYNTAX 1.3.6.1.4.1.1466.115.121.1.27 SINGLE-VALUE )",
		NULL, NULL
	},
	{
		"inchain-max-searches", "integer", 2, 2, 0,
		ARG_INT | ARG_MAGIC | IC_MAX_SEARCHES, inchain_cf,
		"( 1.3.6.1.4.1.64020.142857.369.1.4 "
			"NAME 'olcInChainMaxSearches' "
			"DESC 'Maximum number of internal recursive searches for LDAP_MATCHING_RULE_IN_CHAIN' "
			"EQUALITY integerMatch "
			"SYNTAX 1.3.6.1.4.1.1466.115.121.1.27 SINGLE-VALUE )",
		NULL, NULL
	},
	{
		"inchain-ignore-acls", "TRUE|FALSE", 2, 2, 0,
		ARG_ON_OFF | ARG_MAGIC | IC_IGNORE_ACLS, inchain_cf,
		"( 1.3.6.1.4.1.64020.142857.369.1.5 "
			"NAME 'olcInChainIgnoreACLs' "
			"DESC 'Evaluate LDAP_MATCHING_RULE_IN_CHAIN as rootdn and bypass ACL checks' "
			"EQUALITY booleanMatch "
			"SYNTAX 1.3.6.1.4.1.1466.115.121.1.7 SINGLE-VALUE )",
		NULL, NULL
	},
	{ NULL, NULL, 0, 0, 0, ARG_IGNORED }
};

static ConfigOCs inchainocs[] = {
	{
		"( 1.3.6.1.4.1.64020.142857.369.1.6 "
		"NAME 'olcInChainConfig' "
		"DESC 'LDAP_MATCHING_RULE_IN_CHAIN overlay configuration' "
		"SUP olcOverlayConfig "
		"MAY ( olcInChainAttr $ olcInChainMaxDepth $ olcInChainMaxNodes $ "
		"olcInChainMaxSearches $ olcInChainIgnoreACLs ) )",
		Cft_Overlay, inchaincfg
	},
	{ NULL, 0, NULL }
};

static int
inchain_attr_is_dn_syntax(AttributeDescription *ad)
{
	AttributeType *at;

	if (ad == NULL || ad->ad_type == NULL) {
		return 0;
	}

	for (at = ad->ad_type; at != NULL; at = at->sat_sup) {
		if (at->sat_syntax != NULL && at->sat_syntax->ssyn_oid != NULL && strcmp(at->sat_syntax->ssyn_oid, LDAP_SYNTAX_DN_OID) == 0) {
			return 1;
		}
	}

	return 0;
}

static int inchain_attr_allowed(inchain_info *ii, AttributeDescription *ad) {
	inchain_attr *ia;

	if (!inchain_attr_is_dn_syntax(ad)) {
		return 0;
	}

	if (ii->attrs == NULL) {
		return 1;
	}

	for (ia = ii->attrs; ia != NULL; ia = ia->next) {
		if (ia->ad == ad || ia->ad->ad_type == ad->ad_type) {
			return 1;
		}
	}

	return 0;
}

static unsigned inchain_dn_hash(BerValue *ndn) {
	unsigned hash = 5381;
	ber_len_t i;

	for (i = 0; i < ndn->bv_len; i++) {
		hash = ((hash << 5) + hash) ^ (unsigned char)ndn->bv_val[i];
	}

	return hash;
}

static void dn_set_ensure_buckets(Operation *op, dn_set *set) {
	if (set->buckets != NULL) {
		return;
	}

	set->bucket_count = INCHAIN_DNSET_BUCKETS;
	set->buckets = op->o_tmpcalloc(set->bucket_count, sizeof(*set->buckets), op->o_tmpmemctx);
}

static int dn_set_contains(dn_set *set, BerValue *ndn) {
	dn_node *node;

	if (set->buckets != NULL && set->bucket_count != 0) {
		unsigned bucket = inchain_dn_hash(ndn) % set->bucket_count;
		for (node = set->buckets[bucket]; node != NULL; node = node->bucket_next) {
			if (bvmatch(&node->ndn, ndn)) {
				return 1;
			}
		}
		return 0;
	}

	for (node = set->head; node != NULL; node = node->next) {
		if (bvmatch(&node->ndn, ndn)) {
			return 1;
		}
	}

	return 0;
}

static int dn_set_add(Operation *op, dn_set *set, BerValue *ndn) {
	dn_node *node;
	unsigned bucket;

	dn_set_ensure_buckets(op, set);

	if (dn_set_contains(set, ndn)) {
		return 0;
	}

	node = op->o_tmpcalloc(1, sizeof(*node), op->o_tmpmemctx);
	ber_dupbv_x(&node->ndn, ndn, op->o_tmpmemctx);
	node->next = set->head;
	set->head = node;

	bucket = inchain_dn_hash(ndn) % set->bucket_count;
	node->bucket_next = set->buckets[bucket];
	set->buckets[bucket] = node;
	set->count++;

	return 1;
}

typedef struct collect_cb {
	slap_callback cb;
	Operation *outer_op;
	dn_set *result;
	int limit;
	int rc;
} collect_cb;

static int inchain_collect_response(Operation *op, SlapReply *rs) {
	collect_cb *ccb = op->o_callback->sc_private;

	if (rs->sr_type == REP_SEARCH && rs->sr_entry != NULL) {
		// Debug(LDAP_DEBUG_TRACE, "inchain: collect parent entry=%s\n", rs->sr_entry->e_nname.bv_val);
		if (ccb->result->count >= ccb->limit) {
			ccb->rc = LDAP_ADMINLIMIT_EXCEEDED;
			return LDAP_ADMINLIMIT_EXCEEDED;
		}

		dn_set_add(ccb->outer_op, ccb->result, &rs->sr_entry->e_nname);
	}

	if (rs->sr_type == REP_RESULT && rs->sr_err != LDAP_SUCCESS) {
		ccb->rc = rs->sr_err;
	}

	return LDAP_SUCCESS;
}

static Filter *inchain_make_parent_filter(Operation *op, AttributeDescription *ad, BerValue *child_ndn) {
	Filter *f;

	f = op->o_tmpcalloc(1, sizeof(*f), op->o_tmpmemctx);
	f->f_choice = LDAP_FILTER_EQUALITY;
	f->f_ava = op->o_tmpcalloc(1, sizeof(AttributeAssertion), op->o_tmpmemctx);
	f->f_ava->aa_desc = ad;
	ber_dupbv_x(&f->f_ava->aa_value, child_ndn, op->o_tmpmemctx);

	return f;
}

static int inchain_search_parents(Operation *op, SlapReply *rs, inchain_info *ii, AttributeDescription *ad, BerValue *child_ndn, dn_set *parents, int remaining_nodes) {
	Operation op2 = *op;
	SlapReply rs2;
	collect_cb ccb;
	BackendDB *be = op->o_bd;
	Filter *filter;
	int rc;
	slap_overinst *on;
	BackendInfo *bi_orig;

	if (be == NULL || BER_BVISNULL(&be->be_nsuffix[0])) {
		rs->sr_text = "inchain overlay cannot determine current database suffix";
		return LDAP_OTHER;
	}

	filter = inchain_make_parent_filter(op, ad, child_ndn);
	memset(&ccb, 0, sizeof(ccb));

	op2.o_tag = LDAP_REQ_SEARCH;
	op2.o_protocol = LDAP_VERSION3;
	op2.o_managedsait = SLAP_CONTROL_NONCRITICAL;
	op2.o_bd = be;
	op2.o_callback = &ccb.cb;
	op2.o_req_dn = be->be_suffix[0];
	op2.o_req_ndn = be->be_nsuffix[0];
	op2.ors_scope = LDAP_SCOPE_SUBTREE;
	op2.ors_deref = LDAP_DEREF_NEVER;
	op2.ors_slimit = SLAP_NO_LIMIT;
	op2.ors_tlimit = SLAP_NO_LIMIT;
	op2.ors_filter = filter;
	op2.ors_filterstr.bv_val = NULL;
	op2.ors_filterstr.bv_len = 0;
	op2.ors_attrs = slap_anlist_no_attrs;
	op2.ors_attrsonly = 1;

	if (ii->ignore_acls) {
		if (BER_BVISNULL(&be->be_rootndn)) {
			rs->sr_text = "inchain-ignore-acls requires database rootdn";
			return LDAP_UNWILLING_TO_PERFORM;
		}
		op2.o_dn = be->be_rootdn;
		op2.o_ndn = be->be_rootndn;
	}

	ccb.cb.sc_response = inchain_collect_response;
	ccb.cb.sc_private = &ccb;
	ccb.outer_op = op;
	ccb.result = parents;
	ccb.limit = remaining_nodes;
	ccb.rc = LDAP_SUCCESS;

	memset(&rs2, 0, sizeof(rs2));
	rs2.sr_type = REP_RESULT;
	// Debug(LDAP_DEBUG_TRACE, "inchain: internal parent search base=%s filter=(%s=%s)\n", op2.o_req_ndn.bv_val, ad->ad_cname.bv_val, child_ndn->bv_val);

	on = (slap_overinst *)be->bd_info;
	if (on->on_info == NULL || on->on_info->oi_orig == NULL) {
		rs->sr_text = "inchain overlay cannot determine underlying backend";
		return LDAP_OTHER;
	}

	bi_orig = be->bd_info;
	be->bd_info = on->on_info->oi_orig;
	op2.o_bd = be;
	rc = op2.o_bd->be_search(&op2, &rs2);
	be->bd_info = bi_orig;

	if (rc == SLAP_CB_CONTINUE) {
		rc = LDAP_SUCCESS;
	}

	if (rc != LDAP_SUCCESS) {
		return rc;
	}

	if (ccb.rc != LDAP_SUCCESS) {
		return ccb.rc;
	}

	if (rs2.sr_err == SLAP_CB_CONTINUE) {
		rs2.sr_err = LDAP_SUCCESS;
	}

	if (rs2.sr_err != LDAP_SUCCESS) {
		return rs2.sr_err;
	}

	return rc;
}

static int inchain_expand_dn(Operation *op, SlapReply *rs, inchain_info *ii, AttributeDescription *ad, BerValue *start_ndn, dn_set *expanded) {
	dn_set frontier = {0};
	int depth;
	int searches = 0;

	dn_set_add(op, expanded, start_ndn);
	// Debug(LDAP_DEBUG_TRACE, "inchain: expand start dn=%s\n", start_ndn->bv_val);
	dn_set_add(op, &frontier, start_ndn);

	for (depth = 0; depth < ii->max_depth && frontier.head != NULL; depth++) {
		dn_set next = {0};
		dn_node *node;

		for (node = frontier.head; node != NULL; node = node->next) {
			dn_set parents = {0};
			dn_node *parent;
			int rc;

			searches++;
			if (searches > ii->max_searches) {
				rs->sr_text = "LDAP_MATCHING_RULE_IN_CHAIN internal search limit exceeded";
				return LDAP_ADMINLIMIT_EXCEEDED;
			}

			// Debug(LDAP_DEBUG_TRACE, "inchain: expand depth=%d frontier dn=%s\n", depth, node->ndn.bv_val);
			rc = inchain_search_parents(op, rs, ii, ad, &node->ndn, &parents, ii->max_nodes - expanded->count);
			// Debug(LDAP_DEBUG_TRACE, "inchain: parent search rc=%d parents=%d for child=%s\n", rc, parents.count, node->ndn.bv_val);
			if (rc != LDAP_SUCCESS) {
				return rc;
			}

			for (parent = parents.head; parent != NULL; parent = parent->next) {
				if (expanded->count >= ii->max_nodes) {
					rs->sr_text = "LDAP_MATCHING_RULE_IN_CHAIN node limit exceeded";
					return LDAP_ADMINLIMIT_EXCEEDED;
				}
				if (dn_set_add(op, expanded, &parent->ndn)) {
					// Debug(LDAP_DEBUG_TRACE, "inchain: parent candidate=%s\n", parent->ndn.bv_val);
					dn_set_add(op, &next, &parent->ndn);
				}
				// else {
				// 	Debug(LDAP_DEBUG_TRACE, "inchain: already seen dn=%s\n", parent->ndn.bv_val);
				// }
			}
		}

		frontier = next;
	}

	if (frontier.head != NULL) {
		rs->sr_text = "LDAP_MATCHING_RULE_IN_CHAIN depth limit exceeded";
		return LDAP_ADMINLIMIT_EXCEEDED;
	}

	return LDAP_SUCCESS;
}

static Filter *inchain_make_or_filter(Operation *op, AttributeDescription *ad, dn_set *dns) {
	Filter *or_filter;
	Filter **tail;
	dn_node *node;

	or_filter = op->o_tmpcalloc(1, sizeof(*or_filter), op->o_tmpmemctx);
	or_filter->f_choice = LDAP_FILTER_OR;
	tail = &or_filter->f_or;

	for (node = dns->head; node != NULL; node = node->next) {
		Filter *eq;

		eq = op->o_tmpcalloc(1, sizeof(*eq), op->o_tmpmemctx);
		eq->f_choice = LDAP_FILTER_EQUALITY;
		eq->f_ava = op->o_tmpcalloc(1, sizeof(AttributeAssertion), op->o_tmpmemctx);
		eq->f_ava->aa_desc = ad;
		ber_dupbv_x(&eq->f_ava->aa_value, &node->ndn, op->o_tmpmemctx);

		*tail = eq;
		tail = &eq->f_next;
	}

	return or_filter;
}

static int inchain_rewrite_filter(Operation *op, SlapReply *rs, inchain_info *ii, Filter **fp, int below_not, int depth) {
	Filter *f = *fp;
	int rc;

	if (depth > INCHAIN_MAX_FILTER_DEPTH) {
		rs->sr_text = "LDAP_MATCHING_RULE_IN_CHAIN filter nesting limit exceeded";
		return LDAP_ADMINLIMIT_EXCEEDED;
	}

	if (f == NULL) {
		return LDAP_SUCCESS;
	}

	switch (f->f_choice) {
	case LDAP_FILTER_AND:
	case LDAP_FILTER_OR: {
		Filter **child;
		for (child = &f->f_list; *child != NULL; child = &(*child)->f_next) {
			rc = inchain_rewrite_filter(op, rs, ii, child, below_not, depth + 1);
			if (rc != LDAP_SUCCESS) {
				return rc;
			}
		}
		return LDAP_SUCCESS;
	}
	case LDAP_FILTER_NOT:
		/* Reject the rule anywhere below NOT to avoid surprising authorization
		 * semantics. This must be recursive, not only a direct-child check.
		 */
		return inchain_rewrite_filter(op, rs, ii, &f->f_not, 1, depth + 1);
	case LDAP_FILTER_EXT:
		break;
	default:
		return LDAP_SUCCESS;
	}

	if (f->f_mra == NULL || f->f_mra->ma_rule == NULL || strcmp(f->f_mra->ma_rule->smr_oid, INCHAIN_OID) != 0) {
		return LDAP_SUCCESS;
	}

	if (below_not) {
		rs->sr_text = "LDAP_MATCHING_RULE_IN_CHAIN below NOT is not supported";
		return LDAP_UNWILLING_TO_PERFORM;
	}

	if (f->f_mra->ma_desc == NULL) {
		rs->sr_text = "LDAP_MATCHING_RULE_IN_CHAIN requires an attribute description";
		return LDAP_INAPPROPRIATE_MATCHING;
	}

	if (f->f_mra->ma_dnattrs) {
		rs->sr_text = "LDAP_MATCHING_RULE_IN_CHAIN does not support dnAttributes";
		return LDAP_INAPPROPRIATE_MATCHING;
	}

	if (!inchain_attr_allowed(ii, f->f_mra->ma_desc)) {
		rs->sr_text = "LDAP_MATCHING_RULE_IN_CHAIN is only supported for configured or DN-syntax attributes";
		return LDAP_INAPPROPRIATE_MATCHING;
	}

	BerValue normalized = BER_BVNULL;
	rc = dnNormalize(0, NULL, NULL, &f->f_mra->ma_value, &normalized, op->o_tmpmemctx);
	if (rc != LDAP_SUCCESS) {
		rs->sr_text = "LDAP_MATCHING_RULE_IN_CHAIN assertion value is not a valid DN";
		return LDAP_INVALID_DN_SYNTAX;
	}

	dn_set expanded = {0};
	rc = inchain_expand_dn(op, rs, ii, f->f_mra->ma_desc, &normalized, &expanded);
	if (rc != LDAP_SUCCESS) {
		return rc;
	}

	// Debug(LDAP_DEBUG_TRACE, "inchain: final expanded count=%d\n", expanded.count);

	// for (dn_node *n = expanded.head; n != NULL; n = n->next) {
	// 	Debug(LDAP_DEBUG_TRACE, "inchain: final expanded dn=%s\n", n->ndn.bv_val);
	// }

	*fp = inchain_make_or_filter(op, f->f_mra->ma_desc, &expanded);
	return LDAP_SUCCESS;
}

static int inchain_search(Operation *op, SlapReply *rs) {
	slap_overinst *on;
	inchain_info *ii;
	int rc;

	// Debug(LDAP_DEBUG_TRACE, "inchain: search hook called filter=%s\n", op->ors_filterstr.bv_val ? op->ors_filterstr.bv_val : "<null>");
	on = (slap_overinst *)op->o_bd->bd_info;
	ii = on->on_bi.bi_private;

	if (op->ors_filter == NULL) {
		return SLAP_CB_CONTINUE;
	}

	rc = inchain_rewrite_filter(op, rs, ii, &op->ors_filter, 0, 0);
	if (rc != LDAP_SUCCESS) {
		rs->sr_err = rc;
		send_ldap_result(op, rs);
		return rc;
	}

	return SLAP_CB_CONTINUE;
}

static int inchain_cf(ConfigArgs *c) {
	slap_overinst *on = (slap_overinst *)c->bi;
	inchain_info *ii = on->on_bi.bi_private;
	int rc = 0;

	if (c->op == SLAP_CONFIG_EMIT) {
		switch (c->type) {
		case IC_ATTR: {
			inchain_attr *ia;
			for (ia = ii->attrs; ia != NULL; ia = ia->next) {
				value_add_one(&c->rvalue_vals, &ia->ad->ad_cname);
			}
			break;
		}
		case IC_MAX_DEPTH:
			c->value_int = ii->max_depth;
			break;
		case IC_MAX_NODES:
			c->value_int = ii->max_nodes;
			break;
		case IC_MAX_SEARCHES:
			c->value_int = ii->max_searches;
			break;
		case IC_IGNORE_ACLS:
			c->value_int = ii->ignore_acls;
			break;
		default:
			rc = 1;
		}
		return rc;
	}

	if (c->op == LDAP_MOD_DELETE) {
		if (c->type == IC_ATTR) {
			ii->attrs = NULL;
			return 0;
		}
		return 1;
	}

	switch (c->type) {
	case IC_ATTR: {
		AttributeDescription *ad = NULL;
		const char *text = NULL;
		inchain_attr *ia;

		rc = slap_str2ad(c->argv[1], &ad, &text);
		if (rc != LDAP_SUCCESS) {
			snprintf(c->cr_msg, sizeof(c->cr_msg), "unknown attribute '%s': %s", c->argv[1], text ? text : "");
			return 1;
		}
		if (!inchain_attr_is_dn_syntax(ad)) {
			snprintf(c->cr_msg, sizeof(c->cr_msg), "attribute '%s' does not use Distinguished Name syntax", c->argv[1]);
			return 1;
		}
		ia = ch_calloc(1, sizeof(*ia));
		ia->ad = ad;
		ia->next = ii->attrs;
		ii->attrs = ia;
		break;
	}
	case IC_MAX_DEPTH:
		if (c->value_int <= 0) {
			snprintf(c->cr_msg, sizeof(c->cr_msg), "inchain-max-depth must be greater than zero");
			return 1;
		}
		ii->max_depth = c->value_int;
		break;
	case IC_MAX_NODES:
		if (c->value_int <= 0) {
			snprintf(c->cr_msg, sizeof(c->cr_msg), "inchain-max-nodes must be greater than zero");
			return 1;
		}
		ii->max_nodes = c->value_int;
		break;
	case IC_MAX_SEARCHES:
		if (c->value_int <= 0) {
			snprintf(c->cr_msg, sizeof(c->cr_msg), "inchain-max-searches must be greater than zero");
			return 1;
		}
		ii->max_searches = c->value_int;
		break;
	case IC_IGNORE_ACLS:
		ii->ignore_acls = c->value_int;
		break;
	default:
		return 1;
	}

	return 0;
}

static int inchain_db_init(BackendDB *be, ConfigReply *cr) {
	slap_overinst *on = (slap_overinst *)be->bd_info;
	inchain_info *ii;

	ii = ch_calloc(1, sizeof(*ii));
	ii->max_depth = INCHAIN_DEFAULT_MAX_DEPTH;
	ii->max_nodes = INCHAIN_DEFAULT_MAX_NODES;
	ii->max_searches = INCHAIN_DEFAULT_MAX_SEARCHES;
	ii->ignore_acls = 0;
	on->on_bi.bi_private = ii;

	return 0;
}

static int inchain_db_destroy(BackendDB *be, ConfigReply *cr) {
	slap_overinst *on = (slap_overinst *)be->bd_info;
	inchain_info *ii = on->on_bi.bi_private;
	inchain_attr *ia, *next;

	if (ii != NULL) {
		for (ia = ii->attrs; ia != NULL; ia = next) {
			next = ia->next;
			ch_free(ia);
		}
		ch_free(ii);
	}

	return 0;
}

/*
 * Dummy match function.
 *
 * It should normally never be used, because the overlay rewrites the
 * extensibleMatch filter before the backend evaluates it.
 */
static int
inchain_dummy_match(
	int *matchp,
	slap_mask_t flags,
	Syntax *syntax,
	MatchingRule *mr,
	struct berval *value,
	void *assertedValue
) {
	*matchp = 1; /* no match */
	return LDAP_SUCCESS;
}

static slap_mrule_defs_rec inchain_mrule_defs[] = {
	{
		"( 1.2.840.113556.1.4.1941 "
			"NAME 'inChainMatch' "
			"DESC 'LDAP_MATCHING_RULE_IN_CHAIN' "
			"SYNTAX 1.3.6.1.4.1.1466.115.121.1.12 )",
		SLAP_MR_EXT,
		NULL,
		NULL,
		dnNormalize,
		inchain_dummy_match,
		NULL,
		NULL,
		NULL
	},
	{ NULL, 0, NULL, NULL, NULL, NULL, NULL, NULL, NULL }
};

static int inchain_register_matching_rule(void) {
	int rc;

	rc = register_matching_rule(&inchain_mrule_defs[0]);
	if (rc != LDAP_SUCCESS) {
		Debug(LDAP_DEBUG_CONFIG, "inchain: register_matching_rule failed rc=%d\n", rc);
		return rc;
	}

	return LDAP_SUCCESS;
}

static slap_overinst inchain;

int inchain_initialize(void) {
	int rc;

	memset(&inchain, 0, sizeof(inchain));

	rc = inchain_register_matching_rule();
	if (rc != LDAP_SUCCESS) {
		return rc;
	}

	inchain.on_bi.bi_type = "inchain";
	inchain.on_bi.bi_flags = SLAPO_BFLAG_SINGLE;
	inchain.on_bi.bi_db_init = inchain_db_init;
	inchain.on_bi.bi_db_destroy = inchain_db_destroy;
	inchain.on_bi.bi_op_search = inchain_search;
	inchain.on_bi.bi_cf_ocs = inchainocs;

	rc = config_register_schema(inchaincfg, inchainocs);
	if (rc != 0) {
		return rc;
	}

	return overlay_register(&inchain);
}

#if SLAPD_OVER_INCHAIN == SLAPD_MOD_DYNAMIC
int init_module(int argc, char *argv[]) {
	return inchain_initialize();
}
#endif
