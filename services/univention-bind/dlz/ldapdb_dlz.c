/*
 * DLZ/dlopen rewrite of the historical SDB ldapdb.c driver:
 * ldapdb.c version 1.1.1 (beta)
 *
 * Copyright (C) 2002, 2004, 2005 Stig Venaas
 * Copyright (C) 2007 Turbo Fredriksson
 *
 * Permission to use, copy, modify, and distribute this software for any
 * purpose with or without fee is hereby granted, provided that the above
 * copyright notice and this permission notice appear in all copies.
 *
 * Contributors: Jeremy C. McDermond, Turbo Fredriksson
 *
 * $Id: ldapdb.c,v 1.15 2008-12-05 18:09:54 turbo Exp $
 *
 * This is intentionally not a 1:1 SDB port: it removes dependencies on
 * <dns/sdb.h>, <named/globals.h>, <named/log.h>, <isc/thread.h>, and
 * <isc/print.h>.  It is designed as an external DLZ module loaded by named via `/etc/bind/named.conf`:
 *   dlz "ldap" {
 *       database "dlopen /usr/lib/bind9/ucs-ldapdb.so ldap://host/base????x-bindpw=secret 3600";
 *       search yes;
 *   };
 *
 * Needs dlz_minimal.h from ISC's dlz-modules repository.  Do not include
 * BIND internal headers from /usr/include/dns or /usr/include/named.
 */

#define _GNU_SOURCE

#include <ctype.h>
#include <errno.h>
#include <ldap.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <unistd.h>

#include "dlz_minimal.h"

#ifndef LDAPDB_LDAP_VERSION
#define LDAPDB_LDAP_VERSION 3
#endif

#ifndef LDAPDB_MAXNAMELEN
#define LDAPDB_MAXNAMELEN 519
#endif

#define LDAPDB_WILDCARD_EXT "*"
#define LDAPDB_WILDCARD_INT "~"

/*
 * BIND passes the log / putrr / putnamedrr / writeable_zone callbacks into the
 * module via the variadic tail of dlz_create() as (name,fn) pairs terminated
 * by NULL. We stash them in module-scope statics. Avoid the unsuffixed name
 * "log" so we don't collide with libm's log().
 */
static log_t *dlz_log_cb;
static dns_sdlz_putrr_t *dlz_putrr_cb;
static dns_sdlz_putnamedrr_t *dlz_putnamedrr_cb;
static dns_dlz_writeablezone_t *dlz_writeable_zone_cb;

#define LDAPDB_LOG(level, ...)                            \
	do {                                              \
		if (dlz_log_cb != NULL) {                 \
			dlz_log_cb((level), __VA_ARGS__); \
		} else {                                  \
			fprintf(stderr, "ldapdb_dlz: ");  \
			fprintf(stderr, __VA_ARGS__);     \
			fputc('\n', stderr);              \
		}                                         \
	} while (0)
#define LDAPDB_PUTRR(lookup, type, ttl, data) (dlz_putrr_cb != NULL ? dlz_putrr_cb((lookup), (type), (ttl), (data)) : ISC_R_FAILURE)
#define LDAPDB_PUTNAMEDRR(all, name, type, ttl, data) (dlz_putnamedrr_cb != NULL ? dlz_putnamedrr_cb((all), (name), (type), (ttl), (data)) : ISC_R_FAILURE)

typedef struct ldapdb_rrset {
	char *owner;
	char *type;
	unsigned int ttl;
	char *rdata;
	struct ldapdb_rrset *next;
} ldapdb_rrset_t;

typedef struct ldapdb_conn {
	char *url;
	LDAP *ld;
	struct ldapdb_conn *next;
} ldapdb_conn_t;

typedef struct ldapdb_thread_state {
	pthread_t tid;
	ldapdb_conn_t *connections;
	struct ldapdb_thread_state *next;
} ldapdb_thread_state_t;

typedef struct ldapdb_data {
	char *url;
	char *base;
	char **attrs;
	int scope;
	unsigned int defaultttl;
	/* Templates contain the literal "%z" placeholder; set once in parse_url_config. */
	char *filterall_template;
	char *filterone_template;
	/* Substituted per-call by set_zone_filters; freed and rebuilt each invocation. */
	char *filterall;
	size_t filteralllen;
	char *filterone;
	size_t filteronelen;
	char *filtername;
	char *bindname;
	char *bindpw;
	bool tls;
	bool wildcard;
	bool allow_xfr;

	pthread_mutex_t lock;
	ldapdb_thread_state_t *threads;
} ldapdb_data_t;

static const char *scope_str(int scope) {
	switch (scope) {
	case LDAP_SCOPE_BASE:
		return "base";
	case LDAP_SCOPE_ONELEVEL:
		return "one";
	case LDAP_SCOPE_SUBTREE:
		return "sub";
	default:
		return "?";
	}
}

static void format_attrs(char **attrs, char *buf, size_t buflen) {
	if (attrs == NULL || attrs[0] == NULL) {
		snprintf(buf, buflen, "<all>");
		return;
	}
	size_t pos = 0;
	for (int i = 0; attrs[i] != NULL; i++) {
		int n = snprintf(buf + pos, buflen - pos, "%s%s", i == 0 ? "" : ",", attrs[i]);
		if (n < 0 || (size_t)n >= buflen - pos) {
			break;
		}
		pos += (size_t)n;
	}
}

static void ldapdb_log(int level, const char *fmt, ...) {
	char buf[2048];
	va_list ap;

	va_start(ap, fmt);
	vsnprintf(buf, sizeof(buf), fmt, ap);
	va_end(ap);

	LDAPDB_LOG(level, "%s", buf);
}

static char *xstrdup(const char *s) {
	if (s == NULL) {
		return NULL;
	}
	char *copy = strdup(s);
	return copy;
}

static void free_strv(char **v) {
	if (v != NULL) {
		free(v);
	}
}

static void rrset_free(ldapdb_rrset_t *rr) {
	while (rr != NULL) {
		ldapdb_rrset_t *next = rr->next;
		free(rr->owner);
		free(rr->type);
		free(rr->rdata);
		free(rr);
		rr = next;
	}
}

static char *unhex(char *in) {
	static const char hexdigits[] = "0123456789abcdef";
	char *p, *s = in;
	int d1, d2;

	while ((s = strchr(s, '%')) != NULL) {
		if (!(s[1] && s[2])) {
			return NULL;
		}
		p = strchr(hexdigits, tolower((unsigned char)s[1]));
		if (p == NULL) {
			return NULL;
		}
		d1 = (int)(p - hexdigits);
		p = strchr(hexdigits, tolower((unsigned char)s[2]));
		if (p == NULL) {
			return NULL;
		}
		d2 = (int)(p - hexdigits);
		*s++ = (char)((d1 << 4) | d2);
		memmove(s, s + 2, strlen(s + 2) + 1);
	}
	return in;
}

static char **parseattrs(char *a) {
	char **attrs, *s;
	int i;

	for (i = 0, s = a; *s && *s != '?'; s++) {
		if (*s == ',') {
			i++;
		}
	}

	attrs = calloc((size_t)i + 2, sizeof(char *));
	if (attrs == NULL) {
		return NULL;
	}

	for (i = 0, s = a;; i++) {
		attrs[i] = s;
		s = strchr(s, ',');
		if (s == NULL) {
			break;
		}
		*s++ = '\0';
		if (!*attrs[i]) {
			free(attrs);
			return NULL;
		}
	}

	if (!*attrs[i]) {
		free(attrs);
		return NULL;
	}

	attrs[i + 1] = NULL;
	return attrs;
}

static int parsescope(int *scope, char *s) {
	if (s == NULL || strcmp(s, "sub") == 0) {
		*scope = LDAP_SCOPE_SUBTREE;
		return 0;
	}
	if (strcmp(s, "one") == 0) {
		*scope = LDAP_SCOPE_ONELEVEL;
		return 0;
	}
	if (strcmp(s, "base") == 0) {
		*scope = LDAP_SCOPE_BASE;
		return 0;
	}
	return -1;
}

static int parseextensions(char *extensions, ldapdb_data_t *data) {
	char *s, *next, *name, *value;
	int critical;

	while (extensions != NULL) {
		s = strchr(extensions, ',');
		if (s != NULL) {
			*s++ = '\0';
			next = s;
		} else {
			next = NULL;
		}

		if (*extensions != '\0') {
			s = strchr(extensions, '=');
			if (s != NULL) {
				*s++ = '\0';
				value = *s != '\0' ? s : NULL;
			} else {
				value = NULL;
			}
			name = extensions;

			critical = *name == '!';
			if (critical) {
				name++;
			}
			if (*name == '\0') {
				return -1;
			}

			if (strcasecmp(name, "bindname") == 0) {
				data->bindname = xstrdup(value);
				if (value != NULL && data->bindname == NULL) {
					return -3;
				}
			} else if (strcasecmp(name, "x-bindpw") == 0) {
				data->bindpw = xstrdup(value);
				if (value != NULL && data->bindpw == NULL) {
					return -3;
				}
			} else if (strcasecmp(name, "x-wildcard") == 0) {
				data->wildcard = value == NULL || strcasecmp(value, "true") == 0;
			} else if (strcasecmp(name, "x-tls") == 0) {
				data->tls = value == NULL || strcasecmp(value, "true") == 0;
			} else if (strcasecmp(name, "x-allow-xfr") == 0) {
				data->allow_xfr = value == NULL || strcasecmp(value, "true") == 0;
			} else if (critical) {
				return -2;
			}
		}
		extensions = next;
	}
	return 0;
}

static void ldapdb_free_data(ldapdb_data_t *data) {
	if (data == NULL) {
		return;
	}

	pthread_mutex_lock(&data->lock);
	while (data->threads != NULL) {
		ldapdb_thread_state_t *t = data->threads;
		data->threads = t->next;
		while (t->connections != NULL) {
			ldapdb_conn_t *c = t->connections;
			t->connections = c->next;
			if (c->ld != NULL) {
				ldap_unbind_ext(c->ld, NULL, NULL);
			}
			free(c->url);
			free(c);
		}
		free(t);
	}
	pthread_mutex_unlock(&data->lock);
	pthread_mutex_destroy(&data->lock);

	free(data->url);
	free(data->base);
	free_strv(data->attrs);
	free(data->filterall_template);
	free(data->filterone_template);
	free(data->filterall);
	free(data->filterone);
	free(data->bindname);
	free(data->bindpw);
	free(data);
}

static ldapdb_thread_state_t *find_thread_state(ldapdb_data_t *data, pthread_t tid) {
	ldapdb_thread_state_t *t;

	for (t = data->threads; t != NULL; t = t->next) {
		if (pthread_equal(t->tid, tid)) {
			return t;
		}
	}
	return NULL;
}

static LDAP **ldapdb_getconn(ldapdb_data_t *data) {
	pthread_t tid = pthread_self();
	ldapdb_thread_state_t *t;
	ldapdb_conn_t *c;

	pthread_mutex_lock(&data->lock);

	t = find_thread_state(data, tid);
	if (t == NULL) {
		t = calloc(1, sizeof(*t));
		if (t == NULL) {
			pthread_mutex_unlock(&data->lock);
			return NULL;
		}
		t->tid = tid;
		t->next = data->threads;
		data->threads = t;
	}

	for (c = t->connections; c != NULL; c = c->next) {
		if (strcmp(c->url, data->url) == 0) {
			pthread_mutex_unlock(&data->lock);
			return &c->ld;
		}
	}

	c = calloc(1, sizeof(*c));
	if (c == NULL) {
		pthread_mutex_unlock(&data->lock);
		return NULL;
	}
	c->url = xstrdup(data->url);
	if (c->url == NULL) {
		free(c);
		pthread_mutex_unlock(&data->lock);
		return NULL;
	}
	c->next = t->connections;
	t->connections = c;

	pthread_mutex_unlock(&data->lock);
	return &c->ld;
}

static bool ldapdb_bind(ldapdb_data_t *data, LDAP **ldp) {
	const int ver = LDAPDB_LDAP_VERSION;
	const struct timeval timeout = {.tv_sec = 60, .tv_usec = 0};
	struct berval cred;
	int rc;

	cred.bv_val = data->bindpw;
	cred.bv_len = data->bindpw == NULL ? 0 : strlen(data->bindpw);

	for (int attempt = 1; attempt <= 3; attempt++) {
		if (*ldp != NULL) {
			ldap_unbind_ext(*ldp, NULL, NULL);
			*ldp = NULL;
		}

		rc = ldap_initialize(ldp, data->url);
		if (rc != LDAP_SUCCESS) {
			ldapdb_log(ISC_LOG_ERROR, "ldapdb_dlz: ldap_initialize(%s) failed: %s", data->url, ldap_err2string(rc));
			sleep(5);
			continue;
		}

		ldap_set_option(*ldp, LDAP_OPT_PROTOCOL_VERSION, &ver);
		ldap_set_option(*ldp, LDAP_OPT_REFERRALS, LDAP_OPT_ON);
		ldap_set_option(*ldp, LDAP_OPT_TIMEOUT, &timeout);

		if (data->tls) {
			rc = ldap_start_tls_s(*ldp, NULL, NULL);
			if (rc != LDAP_SUCCESS) {
				ldapdb_log(ISC_LOG_ERROR, "ldapdb_dlz: ldap_start_tls_s() failed: %s", ldap_err2string(rc));
				sleep(5);
				continue;
			}
		}

		rc = ldap_sasl_bind_s(*ldp, data->bindname, LDAP_SASL_SIMPLE, &cred, NULL, NULL, NULL);
		if (rc == LDAP_SUCCESS) {
			return true;
		}

		ldapdb_log(ISC_LOG_ERROR, "ldapdb_dlz: bind as '%s' failed: %s", data->bindname != NULL ? data->bindname : "<anonymous>", ldap_err2string(rc));
		sleep(5);
	}

	if (*ldp != NULL) {
		ldap_unbind_ext(*ldp, NULL, NULL);
		*ldp = NULL;
	}
	return false;
}

static isc_result_t append_rr(ldapdb_rrset_t **head, const char *owner, const char *type, unsigned int ttl, const char *rdata) {
	ldapdb_rrset_t *rr = calloc(1, sizeof(*rr));
	if (rr == NULL) {
		return ISC_R_NOMEMORY;
	}

	rr->owner = xstrdup(owner);
	rr->type = xstrdup(type);
	rr->rdata = xstrdup(rdata);
	rr->ttl = ttl;
	if (rr->owner == NULL || rr->type == NULL || rr->rdata == NULL) {
		rrset_free(rr);
		return ISC_R_NOMEMORY;
	}

	rr->next = *head;
	*head = rr;
	return ISC_R_SUCCESS;
}

static isc_result_t ldapdb_collect(const char *zone, const char *name, ldapdb_data_t *data, ldapdb_rrset_t **out) {
	isc_result_t result = ISC_R_NOTFOUND;
	LDAP **ldp;
	LDAPMessage *res = NULL, *e;
	struct berval **vals = NULL, **names = NULL;
	BerElement *ptr = NULL;
	char *fltr;
	char type[64];
	int rc;

	*out = NULL;

	ldp = ldapdb_getconn(data);
	if (ldp == NULL) {
		return ISC_R_NOMEMORY;
	}

	if (*ldp == NULL && !ldapdb_bind(data, ldp)) {
		return ISC_R_FAILURE;
	}

	if (name == NULL) {
		fltr = data->filterall;
	} else {
		if (strlen(name) > LDAPDB_MAXNAMELEN) {
			return ISC_R_FAILURE;
		}
		snprintf(data->filtername, data->filteronelen - (size_t)(data->filtername - data->filterone), "%s))", name);
		fltr = data->filterone;
	}

	{
		char attrs_buf[512];
		format_attrs(data->attrs, attrs_buf, sizeof(attrs_buf));
		ldapdb_log(ISC_LOG_INFO, "ldapdb_dlz: ldap_search base='%s' scope=%s filter='%s' attrs=%s", data->base != NULL ? data->base : "", scope_str(data->scope), fltr, attrs_buf);
	}

	for (int retry = 0; retry < 2; retry++) {
		rc = ldap_search_ext_s(*ldp, data->base, data->scope, fltr, data->attrs, 0, NULL, NULL, NULL, 0, &res);
		if (rc == LDAP_SUCCESS) {
			break;
		}
		if (rc == LDAP_SERVER_DOWN || rc == LDAP_TIMEOUT) {
			ldapdb_bind(data, ldp);
			continue;
		}
		ldapdb_log(ISC_LOG_ERROR, "ldapdb_dlz: ldap_search_ext_s zone=%s name=%s filter=%s failed: %s", zone, name != NULL ? name : "<allnodes>", fltr, ldap_err2string(rc));
		return ISC_R_FAILURE;
	}

	if (res == NULL) {
		return ISC_R_FAILURE;
	}

	ldapdb_log(ISC_LOG_INFO, "ldapdb_dlz: ldap_search filter='%s' -> %d entries", fltr, ldap_count_entries(*ldp, res));

	for (e = ldap_first_entry(*ldp, res); e != NULL; e = ldap_next_entry(*ldp, e)) {
		unsigned int ttl = data->defaultttl;

		if (name == NULL) {
			names = ldap_get_values_len(*ldp, e, "relativeDomainName");
			if (names == NULL) {
				continue;
			}
		}

		vals = ldap_get_values_len(*ldp, e, "dNSTTL");
		if (vals != NULL && vals[0] != NULL && vals[0]->bv_val != NULL) {
			ttl = (unsigned int)strtoul(vals[0]->bv_val, NULL, 10);
			ldap_value_free_len(vals);
			vals = NULL;
		}

		for (char *a = ldap_first_attribute(*ldp, e, &ptr); a != NULL; a = ldap_next_attribute(*ldp, e, ptr)) {
			char *record_suffix;
			size_t typelen;

			for (char *s = a; *s != '\0'; s++) {
				*s = (char)toupper((unsigned char)*s);
			}

			record_suffix = strstr(a, "RECORD");
			if (record_suffix == NULL || record_suffix == a) {
				ldap_memfree(a);
				continue;
			}

			typelen = (size_t)(record_suffix - a);
			if (typelen >= sizeof(type)) {
				ldap_memfree(a);
				continue;
			}
			memcpy(type, a, typelen);
			type[typelen] = '\0';

			vals = ldap_get_values_len(*ldp, e, a);
			if (vals != NULL) {
				for (int i = 0; vals[i] != NULL && vals[i]->bv_val != NULL; i++) {
					if (name != NULL) {
						result = append_rr(out, name, type, ttl, vals[i]->bv_val);
					} else {
						for (int j = 0; names[j] != NULL && names[j]->bv_val != NULL; j++) {
							char ownerbuf[LDAPDB_MAXNAMELEN + 2];
							const char *owner = names[j]->bv_val;

							if (owner[0] == LDAPDB_WILDCARD_INT[0]) {
								snprintf(ownerbuf, sizeof(ownerbuf), "%s%s", LDAPDB_WILDCARD_EXT, owner + 1);
								owner = ownerbuf;
							}
							result = append_rr(out, owner, type, ttl, vals[i]->bv_val);
							if (result != ISC_R_SUCCESS) {
								break;
							}
						}
					}
					if (result != ISC_R_SUCCESS) {
						break;
					}
				}
				ldap_value_free_len(vals);
				vals = NULL;
			}
			ldap_memfree(a);
			if (result != ISC_R_SUCCESS && result != ISC_R_NOTFOUND) {
				break;
			}
		}

		if (ptr != NULL) {
			ber_free(ptr, 0);
			ptr = NULL;
		}
		if (names != NULL) {
			ldap_value_free_len(names);
			names = NULL;
		}
	}

	ldap_msgfree(res);
	return result;
}

static isc_result_t ldapdb_lookup_name(const char *zone, const char *name, ldapdb_data_t *data, dns_sdlzlookup_t *lookup) {
	ldapdb_rrset_t *rrs = NULL, *rr;
	isc_result_t result = ldapdb_collect(zone, name, data, &rrs);

	if (result != ISC_R_SUCCESS) {
		rrset_free(rrs);
		return result;
	}

	for (rr = rrs; rr != NULL; rr = rr->next) {
		result = LDAPDB_PUTRR(lookup, rr->type, rr->ttl, rr->rdata);
		if (result != ISC_R_SUCCESS) {
			break;
		}
	}
	rrset_free(rrs);
	return result;
}

static isc_result_t ldapdb_allnodes_emit(const char *zone, ldapdb_data_t *data, dns_sdlzallnodes_t *allnodes) {
	ldapdb_rrset_t *rrs = NULL, *rr;
	isc_result_t result = ldapdb_collect(zone, NULL, data, &rrs);

	if (result != ISC_R_SUCCESS) {
		rrset_free(rrs);
		return result;
	}

	for (rr = rrs; rr != NULL; rr = rr->next) {
		result = LDAPDB_PUTNAMEDRR(allnodes, rr->owner, rr->type, rr->ttl, rr->rdata);
		if (result != ISC_R_SUCCESS) {
			break;
		}
	}
	rrset_free(rrs);
	return result;
}

/*
 * BIND's SDLZ layer resolves a multi-label name by walking labels from the
 * zone apex downward, asking the driver at each intermediate label. If we
 * answer NOTFOUND for a label that has no LDAP entry of its own but does have
 * descendants (e.g. "_tcp" when "_ldap._tcp" exists), BIND stops walking and
 * the leaf becomes unreachable. The SDLZ contract for that case is to return
 * ISC_R_SUCCESS without calling putrr -- "this node exists, walk deeper".
 *
 * has_descendants() runs a sizelimit-1 LDAP probe for any entry whose
 * relativeDomainName ends in ".<name>" inside the current zone. Caller must
 * have already invoked set_zone_filters() for the zone so data->filterone
 * holds the "(&(zoneName=<zone>)(relativeDomainName=" prefix and
 * data->filtername points at the slot after it.
 */
static bool has_descendants(ldapdb_data_t *data, const char *name) {
	LDAP **ldp;
	LDAPMessage *res = NULL;
	char namebuf[LDAPDB_MAXNAMELEN + 3];
	char *no_attrs[] = {(char *)"1.1", NULL};
	int rc, count = 0;
	size_t name_len = strlen(name);

	if (name_len == 0 || name_len + 2 > LDAPDB_MAXNAMELEN) {
		return false;
	}
	if (snprintf(namebuf, sizeof(namebuf), "*.%s", name) >= (int)sizeof(namebuf)) {
		return false;
	}
	snprintf(data->filtername, data->filteronelen - (size_t)(data->filtername - data->filterone), "%s))", namebuf);

	ldp = ldapdb_getconn(data);
	if (ldp == NULL) {
		return false;
	}
	if (*ldp == NULL && !ldapdb_bind(data, ldp)) {
		return false;
	}

	ldapdb_log(ISC_LOG_INFO, "ldapdb_dlz: ldap_search base='%s' scope=%s filter='%s' attrs=1.1 sizelimit=1 (descendant-probe)", data->base != NULL ? data->base : "", scope_str(data->scope), data->filterone);

	rc = ldap_search_ext_s(*ldp, data->base, data->scope, data->filterone, no_attrs, 1, NULL, NULL, NULL, 1 /* sizelimit */, &res);
	if (rc == LDAP_SUCCESS || rc == LDAP_SIZELIMIT_EXCEEDED) {
		count = ldap_count_entries(*ldp, res);
	} else {
		ldapdb_log(ISC_LOG_INFO, "ldapdb_dlz: descendant-probe filter='%s' failed: %s", data->filterone, ldap_err2string(rc));
	}
	if (res != NULL) {
		ldap_msgfree(res);
	}
	ldapdb_log(ISC_LOG_INFO, "ldapdb_dlz: ldap_search filter='%s' -> %d match (descendant-probe)", data->filterone, count);
	return count > 0;
}

static isc_result_t parse_url_config(char *url, ldapdb_data_t *data) {
	char *s, *attrs = NULL, *scope = NULL, *filter = NULL, *extensions = NULL;

	data->url = xstrdup(url);
	if (data->url == NULL) {
		return ISC_R_NOMEMORY;
	}

	s = strstr(data->url, "://");
	if (s == NULL) {
		ldapdb_log(ISC_LOG_ERROR, "ldapdb_dlz: first argument must be an LDAP URL");
		return ISC_R_FAILURE;
	}

	s = strchr(s + 3, '/');
	if (s == NULL) {
		data->base = NULL;
		return ISC_R_SUCCESS;
	}

	*s++ = '\0';
	data->base = xstrdup(s);
	if (data->base == NULL && *s != '\0') {
		return ISC_R_NOMEMORY;
	}

	s = strchr(data->base, '?');
	if (s != NULL) {
		*s++ = '\0';
		attrs = s;
		s = strchr(s, '?');
		if (s != NULL) {
			*s++ = '\0';
			scope = s;
			s = strchr(s, '?');
			if (s != NULL) {
				*s++ = '\0';
				filter = s;
				s = strchr(s, '?');
				if (s != NULL) {
					*s++ = '\0';
					extensions = s;
					s = strchr(s, '?');
					if (s != NULL) {
						*s = '\0';
					}
				}
			}
		}
	}

	if (data->base != NULL && *data->base == '\0') {
		free(data->base);
		data->base = NULL;
	}
	if (attrs != NULL && *attrs == '\0') {
		attrs = NULL;
	}
	if (scope != NULL && *scope == '\0') {
		scope = NULL;
	}
	if (filter != NULL && *filter == '\0') {
		filter = NULL;
	}
	if (extensions != NULL && *extensions == '\0') {
		extensions = NULL;
	}

	if (attrs != NULL) {
		data->attrs = parseattrs(attrs);
		if (data->attrs == NULL) {
			ldapdb_log(ISC_LOG_ERROR, "ldapdb_dlz: URL attribute parse error");
			return ISC_R_FAILURE;
		}
	}

	if (parsescope(&data->scope, scope) != 0) {
		ldapdb_log(ISC_LOG_ERROR, "ldapdb_dlz: URL scope must be base, one, or sub");
		return ISC_R_FAILURE;
	}

	if (extensions != NULL) {
		int err = parseextensions(extensions, data);
		if (err == -3) {
			return ISC_R_NOMEMORY;
		}
		if (err < 0) {
			ldapdb_log(ISC_LOG_ERROR, "ldapdb_dlz: URL extension parse error %d", err);
			return ISC_R_FAILURE;
		}
	}

	if ((data->base != NULL && unhex(data->base) == NULL) || (filter != NULL && unhex(filter) == NULL) || (data->bindname != NULL && unhex(data->bindname) == NULL) ||
	    (data->bindpw != NULL && unhex(data->bindpw) == NULL)) {
		ldapdb_log(ISC_LOG_ERROR, "ldapdb_dlz: URL contains bad hex escapes");
		return ISC_R_FAILURE;
	}

	/*
	 * Save the filter as a template with "%z" as a placeholder for the zone
	 * name. set_zone_filters() rebuilds data->filterall / filterone on every
	 * lookup by substituting the zone into the template, so the original
	 * template is preserved for re-use.
	 */
	if (filter == NULL) {
		data->filterall_template = xstrdup("(zoneName=%z)");
		data->filterone_template = xstrdup("(&(zoneName=%z)(relativeDomainName=");
	} else {
		if (asprintf(&data->filterall_template, "(&%s(zoneName=%%z))", filter) < 0) {
			data->filterall_template = NULL;
		}
		if (asprintf(&data->filterone_template, "(&%s(zoneName=%%z)(relativeDomainName=", filter) < 0) {
			data->filterone_template = NULL;
		}
	}
	if (data->filterall_template == NULL || data->filterone_template == NULL) {
		return ISC_R_NOMEMORY;
	}

	return ISC_R_SUCCESS;
}

static isc_result_t set_zone_filters(ldapdb_data_t *data, const char *zone) {
	char *new_all = NULL, *new_one_prefix = NULL, *new_one = NULL;
	char *p;
	size_t one_buflen;

	/* Rebuild filterall from filterall_template by substituting %z -> zone. */
	p = strstr(data->filterall_template, "%z");
	if (p == NULL) {
		return ISC_R_FAILURE;
	}
	if (asprintf(&new_all, "%.*s%s%s", (int)(p - data->filterall_template), data->filterall_template, zone, p + 2) < 0) {
		return ISC_R_NOMEMORY;
	}

	/* Rebuild filterone the same way, then leave room for the relativeDomainName
	 * tail that ldapdb_collect snprintf's in just before searching. */
	p = strstr(data->filterone_template, "%z");
	if (p == NULL) {
		free(new_all);
		return ISC_R_FAILURE;
	}
	if (asprintf(&new_one_prefix, "%.*s%s%s", (int)(p - data->filterone_template), data->filterone_template, zone, p + 2) < 0) {
		free(new_all);
		return ISC_R_NOMEMORY;
	}
	one_buflen = strlen(new_one_prefix) + LDAPDB_MAXNAMELEN + 4;
	new_one = calloc(1, one_buflen);
	if (new_one == NULL) {
		free(new_all);
		free(new_one_prefix);
		return ISC_R_NOMEMORY;
	}
	memcpy(new_one, new_one_prefix, strlen(new_one_prefix));
	free(new_one_prefix);

	free(data->filterall);
	free(data->filterone);
	data->filterall = new_all;
	data->filteralllen = strlen(new_all) + 1;
	data->filterone = new_one;
	data->filteronelen = one_buflen;
	data->filtername = data->filterone + strlen(data->filterone);
	return ISC_R_SUCCESS;
}

/* Required by DLZ dlopen. */
int dlz_version(unsigned int *flags) {
	if (flags != NULL) {
		*flags |= DNS_SDLZFLAG_THREADSAFE;
	}
	return DLZ_DLOPEN_VERSION;
}

/*
 * Required by DLZ dlopen.
 * argv[0] is the LDAP URL.
 * argv[1] is the default TTL.
 */
isc_result_t dlz_create(const char *dlzname, unsigned int argc, char *argv[], void **dbdata, ...) {
	ldapdb_data_t *data;
	isc_result_t result;
	va_list ap;
	const char *helper_name;

	(void)dlzname;

	/*
	 * Extract the (name, fn-pointer) helper pairs BIND passes after dbdata,
	 * terminated by a NULL name. Must happen before any ldapdb_log() call
	 * that should actually reach BIND's log.
	 */
	va_start(ap, dbdata);
	while ((helper_name = va_arg(ap, const char *)) != NULL) {
		if (strcmp(helper_name, "log") == 0) {
			dlz_log_cb = va_arg(ap, log_t *);
		} else if (strcmp(helper_name, "putrr") == 0) {
			dlz_putrr_cb = va_arg(ap, dns_sdlz_putrr_t *);
		} else if (strcmp(helper_name, "putnamedrr") == 0) {
			dlz_putnamedrr_cb = va_arg(ap, dns_sdlz_putnamedrr_t *);
		} else if (strcmp(helper_name, "writeable_zone") == 0) {
			dlz_writeable_zone_cb = va_arg(ap, dns_dlz_writeablezone_t *);
		} else {
			(void)va_arg(ap, void *);
		}
	}
	va_end(ap);

	/*
	 * BIND's dlopen driver passes argv[0]=driver path, argv[1..N]=user args
	 * from the database "dlopen <path> <arg1> <arg2> ..." string.
	 */
	if (argc < 3) {
		ldapdb_log(ISC_LOG_ERROR, "ldapdb_dlz: expected LDAP URL and default TTL after driver path (argc=%u)", argc);
		return ISC_R_FAILURE;
	}

	data = calloc(1, sizeof(*data));
	if (data == NULL) {
		return ISC_R_NOMEMORY;
	}

	pthread_mutex_init(&data->lock, NULL);
	data->defaultttl = (unsigned int)strtoul(argv[2], NULL, 10);
	if (data->defaultttl == 0) {
		ldapdb_log(ISC_LOG_ERROR, "ldapdb_dlz: invalid default TTL '%s'", argv[2]);
		ldapdb_free_data(data);
		return ISC_R_FAILURE;
	}

	result = parse_url_config(argv[1], data);
	if (result != ISC_R_SUCCESS) {
		ldapdb_free_data(data);
		return result;
	}

	*dbdata = data;
	return ISC_R_SUCCESS;
}

void dlz_destroy(void *dbdata) {
	ldapdb_free_data((ldapdb_data_t *)dbdata);
}

/*
 * DLZ asks whether this driver can serve the zone containing 'name'.  This
 * implementation probes LDAP for zoneName=<name> and lets named walk upward.
 */
isc_result_t dlz_findzonedb(void *dbdata, const char *name, dns_clientinfomethods_t *methods, dns_clientinfo_t *clientinfo) {
	ldapdb_data_t *data = (ldapdb_data_t *)dbdata;
	ldapdb_rrset_t *rrs = NULL;
	isc_result_t result;

	(void)methods;
	(void)clientinfo;

	result = set_zone_filters(data, name);
	if (result != ISC_R_SUCCESS) {
		ldapdb_log(ISC_LOG_INFO, "ldapdb_dlz: findzonedb(%s): set_zone_filters failed (%u)", name, result);
		return result;
	}

	result = ldapdb_collect(name, NULL, data, &rrs);
	rrset_free(rrs);
	ldapdb_log(ISC_LOG_INFO, "ldapdb_dlz: findzonedb(%s) filter=%s -> %s", name, data->filterall, result == ISC_R_SUCCESS ? "FOUND" : "NOTFOUND");
	return result == ISC_R_SUCCESS ? ISC_R_SUCCESS : ISC_R_NOTFOUND;
}

isc_result_t dlz_lookup(const char *zone, const char *name, void *dbdata, dns_sdlzlookup_t *lookup, dns_clientinfomethods_t *methods, dns_clientinfo_t *clientinfo) {
	ldapdb_data_t *data = (ldapdb_data_t *)dbdata;
	isc_result_t result;

	(void)methods;
	(void)clientinfo;

	/*
	 * BIND's SDLZ layer calls us with the name already relative to the zone:
	 *   "@"    for the apex
	 *   "*"    for a wildcard probe
	 *   "host" for a leaf inside the zone
	 * That happens to be exactly the value of relativeDomainName in UCS LDAP,
	 * so we pass it through directly to the search filter.
	 */
	ldapdb_log(ISC_LOG_INFO, "ldapdb_dlz: lookup(zone=%s relativeDomainName=%s)", zone, name);

	result = set_zone_filters(data, zone);
	if (result != ISC_R_SUCCESS) {
		return result;
	}

	result = ldapdb_lookup_name(zone, name, data, lookup);

	/*
	 * Intermediate-node stub: when the exact lookup fails, ask LDAP whether
	 * any deeper relativeDomainName ends in ".<name>". If so, return SUCCESS
	 * with no records so BIND descends the tree to the leaf.
	 */
	if (result == ISC_R_NOTFOUND && strcmp(name, "@") != 0 && strcmp(name, "*") != 0 && has_descendants(data, name)) {
		ldapdb_log(ISC_LOG_INFO, "ldapdb_dlz: lookup(zone=%s name=%s) intermediate node, descending", zone, name);
		return ISC_R_SUCCESS;
	}

	if (result == ISC_R_NOTFOUND && strcmp(name, "@") != 0 && data->wildcard) {
		const char *np = name;
		char *srch_name = malloc(strlen(name) + strlen(LDAPDB_WILDCARD_INT) + 1);
		if (srch_name == NULL) {
			return ISC_R_NOMEMORY;
		}

		while (result == ISC_R_NOTFOUND && (np = strchr(np + 1, '.')) != NULL) {
			snprintf(srch_name, strlen(name) + strlen(LDAPDB_WILDCARD_INT) + 1, "%s%s", LDAPDB_WILDCARD_INT, np);
			result = ldapdb_lookup_name(zone, srch_name, data, lookup);
		}
		if (result == ISC_R_NOTFOUND) {
			result = ldapdb_lookup_name(zone, LDAPDB_WILDCARD_INT, data, lookup);
		}
		free(srch_name);
	}

	return result;
}

isc_result_t dlz_allowzonexfr(void *dbdata, const char *name, const char *client) {
	ldapdb_data_t *data = (ldapdb_data_t *)dbdata;

	(void)client;
	(void)name;

	return data->allow_xfr ? ISC_R_SUCCESS : ISC_R_NOPERM;
}

isc_result_t dlz_allnodes(const char *zone, void *dbdata, dns_sdlzallnodes_t *allnodes) {
	ldapdb_data_t *data = (ldapdb_data_t *)dbdata;
	isc_result_t result;

	result = set_zone_filters(data, zone);
	if (result != ISC_R_SUCCESS) {
		return result;
	}
	return ldapdb_allnodes_emit(zone, data, allnodes);
}
