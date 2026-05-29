/*
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
 */

/* If you want to use TLS and not OpenLDAP library, uncomment the define below */
/* #define LDAPDB_TLS */
#ifdef LDAP_API_FEATURE_X_OPENLDAP
#define LDAPDB_TLS
#endif

/* If you are using an old LDAP API uncomment the define below. Only do this
 * if you know what you're doing or get compilation errors on ldap_memfree().
 * This also forces LDAPv2.
 */
/* #define LDAPDB_RFC1823API */

/* Using LDAPv3 by default, change this if you want v2 */
#ifndef LDAPDB_LDAP_VERSION
#define LDAPDB_LDAP_VERSION 3
#endif

#include <config.h>

#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>

#include <isc/mem.h>
#include <isc/result.h>
#include <isc/util.h>
#include <isc/thread.h>

#include <dns/sdb.h>

#include <named/globals.h>
#include <named/log.h>

#include <ldap.h>
#include "include/ldapdb.h"

#include <unistd.h>

/*
 * A simple database driver for LDAP
 */

/* enough for name with 8 labels of max length */
#define MAXNAMELEN 519

const char *WILDCARD_EXT = "*"; /* External host wildcard character */
const char *WILDCARD_INT = "~"; /* Internal wildcard, change to taste */

#define LDAPDB_FAILURE(msg)                                                                                                                       \
	{                                                                                                                                         \
		isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_ERROR, "LDAP sdb zone '%s': %s", zone, msg); \
		return (ISC_R_FAILURE);                                                                                                           \
	}

static dns_sdbimplementation_t *ldapdb = NULL;

struct ldapdb_data {
	char *url;
	char *hostname;
	int portno;
	char *base;
	char **attrs;
	int scope;
	int defaultttl;
	char *filterall;
	int filteralllen;
	char *filterone;
	int filteronelen;
	char *filtername;
	char *bindname;
	char *bindpw;
#ifdef LDAPDB_TLS
	int tls;
#endif
	int wildcard;
};

/* used by ldapdb_getconn */

struct ldapdb_entry {
	void *index;
	size_t size;
	void *data;
	struct ldapdb_entry *next;
};

static struct ldapdb_entry *ldapdb_find(struct ldapdb_entry *stack, const void *index, size_t size) {
	while (stack != NULL) {
		if (stack->size == size && !memcmp(stack->index, index, size))
			return stack;
		stack = stack->next;
	}
	return NULL;
}

static void ldapdb_insert(struct ldapdb_entry **stack, struct ldapdb_entry *item) {
	item->next = *stack;
	*stack = item;
}

static void ldapdb_lock(int what) {
	static isc_mutex_t lock;

	switch (what) {
	case 0:
		isc_mutex_init(&lock);
		break;
	case 1:
		LOCK(&lock);
		break;
	case -1:
		UNLOCK(&lock);
		break;
	}
}

/* data == NULL means cleanup */
static LDAP **ldapdb_getconn(struct ldapdb_data *data) {
	static struct ldapdb_entry *allthreadsdata = NULL;
	struct ldapdb_entry *threaddata, *conndata;
	unsigned long threadid;

	if (data == NULL) {
		/* cleanup */
		/* lock out other threads */
		ldapdb_lock(1);
		while (allthreadsdata != NULL) {
			threaddata = allthreadsdata;
			free(threaddata->index);
			while (threaddata->data != NULL) {
				conndata = threaddata->data;
				free(conndata->index);
				if (conndata->data != NULL)
					ldap_unbind_ext((LDAP *)conndata->data, NULL, NULL);
				threaddata->data = conndata->next;
				free(conndata);
			}
			allthreadsdata = threaddata->next;
			free(threaddata);
		}
		ldapdb_lock(-1);
		return (NULL);
	}

	/* look for connection data for current thread */
	threadid = isc_thread_self();
	threaddata = ldapdb_find(allthreadsdata, &threadid, sizeof(threadid));
	if (threaddata == NULL) {
		/* no data for this thread, create empty connection list */
		threaddata = malloc(sizeof(*threaddata));
		if (threaddata == NULL)
			return (NULL);
		threaddata->index = malloc(sizeof(threadid));
		if (threaddata->index == NULL) {
			free(threaddata);
			return (NULL);
		}
		*(unsigned long *)threaddata->index = threadid;
		threaddata->size = sizeof(threadid);
		threaddata->data = NULL;

		/* need to lock out other threads here */
		ldapdb_lock(1);
		ldapdb_insert(&allthreadsdata, threaddata);
		ldapdb_lock(-1);
	}

	/* threaddata points at the connection list for current thread */
	/* look for existing connection to our server */
	conndata = ldapdb_find((struct ldapdb_entry *)threaddata->data, data->url, strlen(data->url));
	if (conndata == NULL) {
		/* no connection data structure for this server, create one */
		conndata = malloc(sizeof(*conndata));
		if (conndata == NULL)
			return (NULL);
		conndata->index = strdup(data->url);
		conndata->size = strlen(data->url);
		conndata->data = NULL;
		ldapdb_insert((struct ldapdb_entry **)&threaddata->data, conndata);
	}

	return (LDAP **)&conndata->data;
}

static void ldapdb_bind(const char *zone, struct ldapdb_data *data, LDAP **ldp) {
#ifndef LDAPDB_RFC1823API
	const int ver = LDAPDB_LDAP_VERSION;
	const struct timeval timeout = {
	    .tv_sec = 60,
	};
#endif
	int failure = 1, counter = 1, rc;
	struct berval cred;

	if (data->bindpw == NULL) {
		cred.bv_val = NULL;
		cred.bv_len = 0;
	} else {
		cred.bv_val = data->bindpw;
		cred.bv_len = strlen(data->bindpw);
	}

	/* Make sure we try at least three times to connect+bind
	 * to the LDAP server. Sleep five seconds between each
	 * attempt => 25 seconds before timeout! */
	while ((failure == 1) && (counter <= 3)) {
		if (*ldp != NULL)
			ldap_unbind_ext(*ldp, NULL, NULL);

		/* ----------------------------- */
		/* -- Connect to LDAP server. -- */
#ifdef LDAP_API_FEATURE_X_OPENLDAP
		isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_CONTROL, ISC_LOG_DEBUG(2), "LDAP sdb zone '%s': ldap_initialize(%s)", zone, data->url);

		/* Connect to LDAP server using URL */
		rc = ldap_initialize(ldp, data->url);
		if (rc != LDAP_SUCCESS) {
#else
		*ldp = ldap_open(data->hostname, data->portno);
		if (*ldp == NULL) {
#endif

			isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_ERROR,
#ifdef LDAP_API_FEATURE_X_OPENLDAP
			              "LDAP sdb zone '%s': ldapdb_bind(): ldap_initialize() failed. LDAP URL: %s", zone, data->url);
#else
			              "LDAP sdb zone '%s': ldapdb_bind(): ldap_open() failed.", zone);
#endif

			/* Failed - wait five seconds, then try again. */
			goto try_bind_again;
		} else
			isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_CONTROL, ISC_LOG_DEBUG(2),
#ifdef LDAP_API_FEATURE_X_OPENLDAP
			              "LDAP sdb zone '%s': ldapdb_bind(): Connected to ldapserver '%s'", zone, data->url);
#else
			              "LDAP sdb zone '%s': ldapdb_bind(): Connected to ldapserver '%s:%d'", zone, data->hostname, data->portno);
#endif

		/* ----------------- */
		/* -- Set option. -- */
#ifndef LDAPDB_RFC1823API
		ldap_set_option(*ldp, LDAP_OPT_PROTOCOL_VERSION, (const void *)&ver);

		/* Allow referrals */
		ldap_set_option(*ldp, LDAP_OPT_REFERRALS, LDAP_OPT_ON);

		/* Default timeout */
		ldap_set_option(*ldp, LDAP_OPT_TIMEOUT, &timeout);

		isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_CONTROL, ISC_LOG_DEBUG(2), "LDAP sdb zone '%s': ldapdb_bind(): Set option PROTOCOL_VERSION to '%d' and allow referrals.", zone, ver);
#endif

		/* ---------------- */
		/* -- Start TLS. -- */
#ifdef LDAPDB_TLS
		if (data->tls) {
			ldap_start_tls_s(*ldp, NULL, NULL);
			isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_CONTROL, ISC_LOG_DEBUG(2), "LDAP sdb zone '%s': ldapdb_bind(): Started TLS", zone);
		}
#endif

		/* ------------------------------ */
		/* -- Bind to the LDAP server. -- */
		if ((rc = ldap_sasl_bind_s(*ldp, data->bindname, LDAP_SASL_SIMPLE, &cred, NULL, NULL, NULL)) != LDAP_SUCCESS) {
			isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_ERROR, "LDAP sdb zone '%s': ldapdb_bind(): ldap_sasl_bind_s(ldp, '%s', '<secret>') failed: %s", zone,
			              data->bindname, ldap_err2string(rc));

			ldap_unbind_ext(*ldp, NULL, NULL);
			*ldp = NULL;

		try_bind_again:
			sleep(5);
			counter++;
		} else {
			isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_CONTROL, ISC_LOG_DEBUG(2), "LDAP sdb zone '%s': ldapdb_bind(): Bound to ldapserver as '%s'", zone, data->bindname);
			failure = 0;
		}
	}
}

static isc_result_t ldapdb_search(const char *zone, const char *name, void *dbdata, void *retdata) {
	struct ldapdb_data *data = dbdata;
	isc_result_t result = ISC_R_NOTFOUND;
	LDAP **ldp;
	LDAPMessage *res, *e;
	char *fltr, *a;
	struct berval **vals = NULL;
	struct berval **names = NULL;
	char type[64];
#ifdef LDAPDB_RFC1823API
	void *ptr;
#else
	BerElement *ptr;
#endif
	int i, j, rc, msgid, search_retry_count = 2;

try_search_again:
	ldp = ldapdb_getconn(data);
	if (ldp == NULL)
		return (ISC_R_NOMEMORY);

	if (*ldp == NULL) {
		ldapdb_bind(zone, data, ldp);
		if (*ldp == NULL)
			LDAPDB_FAILURE("bind failed");
	}

	if (name == NULL)
		fltr = data->filterall;
	else {
		if (strlen(name) > MAXNAMELEN) {
			isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_ERROR, "LDAP sdb zone '%s': name %s too long", zone, name);
			return (ISC_R_FAILURE);
		}

		sprintf(data->filtername, "%s))", name);
		fltr = data->filterone;
	}

	/* debug when starting `named -g -d 1 ...' on console */
	isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_DEBUG(1), "base='%s', zone='%s', name='%s', filter='%s'", (data->base) ? data->base : "<NULL>", (zone) ? zone : "<NULL>",
	              (name) ? name : "<NULL>", (fltr) ? fltr : "<NULL>");

	ldap_search_ext(*ldp, data->base, LDAP_SCOPE_SUBTREE, fltr, NULL, 0, NULL, NULL, NULL /*timeout*/, 0, &msgid);
	if (msgid == -1) {
		ldapdb_bind(zone, data, ldp);
		if (*ldp != NULL)
			ldap_search_ext(*ldp, data->base, LDAP_SCOPE_SUBTREE, fltr, NULL, 0, NULL, NULL, NULL /*timeout*/, 0, &msgid);
	}

	if (*ldp == NULL || msgid == -1) {
		if (name != NULL)
			isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_ERROR, "LDAP sdb zone '%s': search failed, filter %s", zone, fltr);
		return (ISC_R_FAILURE);
	}

	/* Get the records one by one as they arrive and return them to bind */
	while ((rc = ldap_result(*ldp, msgid, 0, NULL, &res)) != LDAP_RES_SEARCH_RESULT) {
		LDAP *ld = *ldp;
		int ttl = data->defaultttl;
		int err;

		ldap_get_option(ld, LDAP_OPT_RESULT_CODE, &err);
		/* not supporting continuation references at present */
		switch (rc) {
		case LDAP_RES_SEARCH_ENTRY:
			break;
		case -1: /* error */
		case 0:  /* timeout */
			switch (err) {
			case LDAP_SERVER_DOWN:
			case LDAP_TIMEOUT:
				if (--search_retry_count)
					goto try_search_again;
			}
			/* fall through */
		default:
			isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_ERROR, "LDAP sdb zone '%s': ldap_result returned %d %s", zone, rc, ldap_err2string(err));
			ldap_msgfree(res);
			return (ISC_R_FAILURE);
		}

		/* only one entry per result message */
		e = ldap_first_entry(ld, res);
		if (e == NULL) {
			ldap_msgfree(res);
			LDAPDB_FAILURE("ldap_first_entry failed");
		}

		if (name == NULL) {
			names = ldap_get_values_len(ld, e, "relativeDomainName");
			if (names == NULL)
				continue;
		}

		vals = ldap_get_values_len(ld, e, "dNSTTL");
		if (vals != NULL && vals[0] != NULL) {
			ttl = atoi(vals[0]->bv_val);
			ldap_value_free_len(vals);
		}

		for (a = ldap_first_attribute(ld, e, &ptr); a != NULL; a = ldap_next_attribute(ld, e, ptr)) {
			char *s;

			for (s = a; *s; s++)
				*s = toupper(*s);
			s = strstr(a, "RECORD");
			if ((s == NULL) || (s == a) || (s - a >= (signed int)sizeof(type))) {
#ifndef LDAPDB_RFC1823API
				ldap_memfree(a);
#endif
				continue;
			}

			strncpy(type, a, s - a);
			type[s - a] = '\0';

			isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_DEBUG(3), "Retreiving values for attribute '%s' with ldap_get_values()", a);

			vals = ldap_get_values_len(ld, e, a);
			if (vals != NULL) {
				for (i = 0; (vals[i] != NULL && vals[i]->bv_val != NULL); i++) {
					isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_DEBUG(3), "vals[%d]: %s", i, vals[i]->bv_val);

					if (name != NULL) {
						isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_DEBUG(3), "name: %s (%s)", name, vals[i]->bv_val);

						result = dns_sdb_putrr(retdata, type, ttl, vals[i]->bv_val);
					} else {
						for (j = 0; (names[j] != NULL && names[j]->bv_val != NULL); j++) {
							isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_DEBUG(3), "names[%d]: %s (%s)", j, names[j]->bv_val, vals[i]->bv_val);

							if (names[j]->bv_val[0] == WILDCARD_INT[0]) {
								names[j]->bv_val[0] = WILDCARD_EXT[0];
							}

							result = dns_sdb_putnamedrr(retdata, names[j]->bv_val, type, ttl, vals[i]->bv_val);
							if (result != ISC_R_SUCCESS)
								break;
						}
					}

					if (result != ISC_R_SUCCESS) {
						isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_ERROR, "LDAP sdb zone '%s': dns_sdb_put... failed for '%s'", zone, vals[i]->bv_val);

						break;
					}
				}
				ldap_value_free_len(vals);
			}
#ifndef LDAPDB_RFC1823API
			ldap_memfree(a);
#endif
		}

#ifndef LDAPDB_RFC1823API
		if (ptr != NULL)
			ber_free(ptr, 0);
#endif

		if (name == NULL)
			ldap_value_free_len(names);

		/* free this result */
		ldap_msgfree(res);
	}

	/* free final result */
	if ((rc = ldap_parse_result(*ldp, res, &msgid, NULL, NULL, NULL, NULL, 1)) != LDAP_SUCCESS) {
		isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_ERROR, "LDAP sdb zone '%s': ldap_parse_result failed: %s", zone, ldap_err2string(rc));
	} else if (msgid != LDAP_SUCCESS) {
		isc_log_write(named_g_lctx, DNS_LOGCATEGORY_GENERAL, NAMED_LOGMODULE_SERVER, ISC_LOG_ERROR, "LDAP sdb zone '%s': ldap_search_ex failed: %s", zone, ldap_err2string(msgid));
		if (msgid == LDAP_SERVER_DOWN && --search_retry_count)
			goto try_search_again;
	}

	return (result);
}


/* callback routines */
static isc_result_t ldapdb_lookup(const char *zone, const char *name, void *dbdata, dns_sdblookup_t *lookup, dns_clientinfomethods_t *methods, dns_clientinfo_t *clientinfo) {
	struct ldapdb_data *data = dbdata;
	isc_result_t result;                                               /* Result for bind */
	const char *np = name;                                             /* Point at parts of name */
	char *srch_name = malloc(strlen(name) + strlen(WILDCARD_INT) + 1); /* Name for searching */
	if (srch_name == NULL)
		return ISC_R_NOMEMORY;

	UNUSED(methods);
	UNUSED(clientinfo);

	/* search for original name */
	if ((result = ldapdb_search(zone, name, dbdata, lookup)) == ISC_R_NOTFOUND && strcmp(name, "@") && data->wildcard) {
		/* if full name not found,  and wildcard searches enabled,
		 * break name into labels and search for WILDCARD.label from the left */
		while ((result == ISC_R_NOTFOUND) && ((np = strpbrk(np + 1, ".")) != NULL)) {
			sprintf(srch_name, "%s%s", WILDCARD_INT, np);
			result = ldapdb_search(zone, srch_name, dbdata, lookup);
		}
		/* the above loop won't search for the wildcard on it's own as
		 * the relativeDomainName, so we should check that too... */
		if (result == ISC_R_NOTFOUND)
			result = ldapdb_search(zone, WILDCARD_INT, dbdata, lookup);
	}
	free(srch_name);
	return (result);
}

static isc_result_t ldapdb_allnodes(const char *zone, void *dbdata, dns_sdballnodes_t *allnodes) {
	return ldapdb_search(zone, NULL, dbdata, allnodes);
}

static char *unhex(char *in) {
	static const char hexdigits[] = "0123456789abcdef";
	char *p, *s = in;
	int d1, d2;

	while ((s = strchr(s, '%'))) {
		if (!(s[1] && s[2]))
			return NULL;
		if ((p = strchr(hexdigits, tolower(s[1]))) == NULL)
			return NULL;
		d1 = p - hexdigits;
		if ((p = strchr(hexdigits, tolower(s[2]))) == NULL)
			return NULL;
		d2 = p - hexdigits;
		*s++ = d1 << 4 | d2;
		memmove(s, s + 2, strlen(s) - 1);
	}
	return in;
}

static char **parseattrs(char *a) {
	char **attrs, *s;
	int i;

	/* find number of commas */
	for (i = 0, s = a; *s && *s != '?'; s++)
		if (*s == ',')
			i++;

	/* two more than # of commas, need room for NULL terminator */
	attrs = malloc(sizeof(char *) * (i + 2));
	if (!attrs)
		return NULL;

	for (i = 0, s = a;; i++) {
		attrs[i] = s;
		if (!(s = strchr(s, ',')))
			break;
		*s++ = '\0';
		if (!*attrs[i])
			break;
	}
	if (!*attrs[i]) {
		free(attrs);
		return NULL;
	}
	attrs[i + 1] = NULL;
	return attrs;
}

/* returns 0 for ok, -1 for bad syntax */
static int parsescope(int *scope, char *s) {
	if (!s || !strcmp(s, "sub")) {
		*scope = LDAP_SCOPE_SUBTREE;
		return 0;
	}
	if (!strcmp(s, "one")) {
		*scope = LDAP_SCOPE_ONELEVEL;
		return 0;
	}
	if (!strcmp(s, "base")) {
		*scope = LDAP_SCOPE_BASE;
		return 0;
	}

	return -1;
}

/* returns 0 for ok, -1 for bad syntax, -2 for unknown critical extension */
static int parseextensions(char *extensions, struct ldapdb_data *data) {
	char *s, *next, *name, *value;
	int critical;

	while (extensions != NULL) {
		s = strchr(extensions, ',');
		if (s != NULL) {
			*s++ = '\0';
			next = s;
		} else
			next = NULL;

		if (*extensions != '\0') {
			s = strchr(extensions, '=');
			if (s != NULL) {
				*s++ = '\0';
				value = *s != '\0' ? s : NULL;
			} else
				value = NULL;
			name = extensions;

			critical = *name == '!';
			if (critical)
				name++;

			if (*name == '\0')
				return -1;

			if (!strcasecmp(name, "bindname")) {
				data->bindname = isc_mem_strdup(named_g_mctx, value);
				if (data->bindname == NULL)
					return (ISC_R_NOMEMORY);
			} else if (!strcasecmp(name, "x-bindpw")) {
				data->bindpw = isc_mem_strdup(named_g_mctx, value);
				if (data->bindpw == NULL)
					return (ISC_R_NOMEMORY);
			} else if (!strcasecmp(name, "x-wildcard"))
				data->wildcard = value == NULL || !strcasecmp(value, "true");
#ifdef LDAPDB_TLS
			else if (!strcasecmp(name, "x-tls"))
				data->tls = value == NULL || !strcasecmp(value, "true");
#endif
			else if (critical)
				return -2;
		}
		extensions = next;
	}
	return 0;
}

static void free_data(struct ldapdb_data *data) {
	if (data->hostname)
		isc_mem_free(named_g_mctx, data->hostname);
	if (data->url)
		isc_mem_free(named_g_mctx, data->url);
	if (data->attrs)
		free(data->attrs);
	if (data->filterall)
		isc_mem_put(named_g_mctx, data->filterall, data->filteralllen);
	if (data->filterone)
		isc_mem_put(named_g_mctx, data->filterone, data->filteronelen);
	if (data->bindname)
		isc_mem_free(named_g_mctx, data->bindname);
	if (data->bindpw)
		isc_mem_free(named_g_mctx, data->bindpw);
	isc_mem_put(named_g_mctx, data, sizeof(struct ldapdb_data));
}


static isc_result_t ldapdb_create(const char *zone, int argc, char **argv, void *driverdata, void **dbdata) {
	struct ldapdb_data *data;
	char *s, *hostport, *filter = NULL, *attrs = NULL, *scope = NULL, *extensions = NULL;
	int defaultttl;

	UNUSED(driverdata);

	/* we assume that only one thread will call create at a time */
	/* want to do this only once for all instances */

	if (argc < 2)
		LDAPDB_FAILURE("ldapdb_create(): Both URL and TTL value must be specified");

	if ((argv[0] == strstr(argv[0], "ldaps://")) || (argv[0] == strstr(argv[0], "ldapi://"))) {
#ifndef LDAP_API_FEATURE_X_OPENLDAP
		LDAPDB_FAILURE("ldapdb_create(): ldapi and ldaps schemes are only supported with OpenLDAP library for now");
#endif
	} else if (argv[0] != strstr(argv[0], "ldap://"))
		LDAPDB_FAILURE("ldapdb_create(): First argument must be an LDAP URL");

	if ((defaultttl = atoi(argv[1])) < 1)
		LDAPDB_FAILURE("ldapdb_create(): Default TTL must be a positive integer");

	data = isc_mem_get(named_g_mctx, sizeof(struct ldapdb_data));
	if (data == NULL)
		return (ISC_R_NOMEMORY);
	memset(data, 0, sizeof(struct ldapdb_data));

	/* Save data so it doesn't get overwritten - fix reload/restart problems. */
	data->url = isc_mem_strdup(named_g_mctx, argv[0]);
	if (data->url == NULL) {
		free_data(data);
		return (ISC_R_NOMEMORY);
	}

	data->defaultttl = defaultttl;

	/* we know data->url starts with "ldap://", "ldaps://" or "ldapi://" */
	hostport = data->url + strlen(strstr(data->url, "ldap://") ? "ldap://" : "ldap.://");

	s = strchr(hostport, '/');
	if (s) {
		*s++ = '\0';
		data->base = s;
		/* attrs, scope, filter etc? */
		s = strchr(s, '?');
		if (s) {
			*s++ = '\0';
			attrs = s;
			s = strchr(s, '?');
			if (s) {
				*s++ = '\0';
				/* scope */
				scope = s;
				s = strchr(s, '?');
				if (s) {
					*s++ = '\0';
					/* filter */
					filter = s;
					s = strchr(s, '?');
					if (s) {
						*s++ = '\0';
						/* extensions */
						extensions = s;
						s = strchr(s, '?');
						if (s)
							*s++ = '\0';
						if (!*extensions)
							extensions = NULL;
					}
					if (!*filter)
						filter = NULL;
				}
				if (!*scope)
					scope = NULL;
			}
			if (!*attrs)
				attrs = NULL;
		}
		if (!*data->base)
			data->base = NULL;
	}

	if (attrs && !(data->attrs = parseattrs(attrs)))
		LDAPDB_FAILURE("URL: Error parsing attributes");

	if (parsescope(&data->scope, scope))
		LDAPDB_FAILURE("URL: Scope must be base, one or sub");

	/* parse extensions */
	if (extensions) {
		int err;

		err = parseextensions(extensions, data);
		if (err < 0) {
			/* err should be -1 or -2 */
			free_data(data);
			if (err == -1)
				LDAPDB_FAILURE("URL: extension syntax error")
			else if (err == -2)
				LDAPDB_FAILURE("URL: unknown critical extension");
		}
	}

	if ((data->base != NULL && unhex(data->base) == NULL) || (filter != NULL && unhex(filter) == NULL) || (data->bindname != NULL && unhex(data->bindname) == NULL) ||
	    (data->bindpw != NULL && unhex(data->bindpw) == NULL)) {
		free_data(data);
		LDAPDB_FAILURE("URL: bad hex values");
	}

	/* compute filterall and filterone once and for all */
	if (filter == NULL) {
		data->filteralllen = strlen(zone) + strlen("(zoneName=)") + 1;
		data->filteronelen = strlen(zone) + strlen("(&(zoneName=)(relativeDomainName=))") + MAXNAMELEN + 1;
	} else {
		data->filteralllen = strlen(filter) + strlen(zone) + strlen("(&(zoneName=))") + 1;
		data->filteronelen = strlen(filter) + strlen(zone) + strlen("(&(zoneName=)(relativeDomainName=))") + MAXNAMELEN + 1;
	}

	data->filterall = isc_mem_get(named_g_mctx, data->filteralllen);
	if (data->filterall == NULL) {
		free_data(data);
		return (ISC_R_NOMEMORY);
	}
	data->filterone = isc_mem_get(named_g_mctx, data->filteronelen);
	if (data->filterone == NULL) {
		free_data(data);
		return (ISC_R_NOMEMORY);
	}

	if (filter == NULL) {
		sprintf(data->filterall, "(zoneName=%s)", zone);
		sprintf(data->filterone, "(&(zoneName=%s)(relativeDomainName=", zone);
	} else {
		sprintf(data->filterall, "(&%s(zoneName=%s))", filter, zone);
		sprintf(data->filterone, "(&%s(zoneName=%s)(relativeDomainName=", filter, zone);
	}
	data->filtername = data->filterone + strlen(data->filterone);

#ifndef LDAP_API_FEATURE_X_OPENLDAP
	/* support URLs with literal IPv6 addresses */
	data->hostname = isc_mem_strdup(named_g_mctx, hostport + (*hostport == '[' ? 1 : 0));
	if (data->hostname == NULL) {
		free_data(data);
		return (ISC_R_NOMEMORY);
	}

	if (*hostport == '[' && (s = strchr(data->hostname, ']')) != NULL)
		*s++ = '\0';
	else
		s = data->hostname;
	s = strchr(s, ':');
	if (s != NULL) {
		*s++ = '\0';
		data->portno = atoi(s);
	} else
		data->portno = LDAP_PORT;
#endif

	*dbdata = data;
	return (ISC_R_SUCCESS);
}

static void ldapdb_destroy(const char *zone, void *driverdata, void **dbdata) {
	struct ldapdb_data *data = *dbdata;

	UNUSED(zone);
	UNUSED(driverdata);

	free_data(data);
}

static dns_sdbmethods_t ldapdb_methods = {
    .lookup = ldapdb_lookup,
    .allnodes = ldapdb_allnodes,
    .create = ldapdb_create,
    .destroy = ldapdb_destroy,
};

/* Wrapper around dns_sdb_register() */
isc_result_t ldapdb_init(void) {
	unsigned int flags = DNS_SDBFLAG_RELATIVEOWNER | DNS_SDBFLAG_RELATIVERDATA | DNS_SDBFLAG_THREADSAFE;

	ldapdb_lock(0);
	return (dns_sdb_register("ldap", &ldapdb_methods, NULL, flags, named_g_mctx, &ldapdb));
}

/* Wrapper around dns_sdb_unregister() */
void ldapdb_clear(void) {
	if (ldapdb != NULL) {
		/* clean up thread data */
		ldapdb_getconn(NULL);
		dns_sdb_unregister(&ldapdb);
	}
}

/*
 * Local variables:
 * mode: c
 * tab-width: 4
 * End:
 */
