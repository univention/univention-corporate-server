/*
 * Univention Policy
 *  C source of the univnetion policy libary
 *
 * Copyright 2003-2011 Univention GmbH
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

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ldap.h>
#include <sasl/sasl.h>
#include <sys/types.h>
#include <pwd.h>
#include <unistd.h>

#include <univention/config.h>
#include <univention/ldap.h>
#include <univention/debug.h>

#include "internal.h"

univention_ldap_parameters_t* univention_ldap_new(void)
{
	univention_ldap_parameters_t* lp;
	if ((lp = calloc(1, sizeof(univention_ldap_parameters_t))) == NULL)
		return NULL;
	return lp;
}

static int __sasl_interaction(unsigned flags, sasl_interact_t *interact, univention_ldap_parameters_t *lp)
{
	const char *dflt = interact->defresult;

	switch (interact->id) {
		case SASL_CB_GETREALM:
			if (lp)
				dflt = lp->sasl_realm;
			break;
		case SASL_CB_AUTHNAME:
			if (lp)
				dflt = lp->sasl_authcid;
			break;
		case SASL_CB_PASS:
			if (lp)
				dflt = lp->bindpw;
			break;
		case SASL_CB_USER:
			if (lp)
				dflt = lp->sasl_authzid;
			break;
		case SASL_CB_NOECHOPROMPT:
			break;
		case SASL_CB_ECHOPROMPT:
			break;
	}

	if (dflt && !*dflt)
		dflt = interact->defresult;

	interact->result = dflt;
	interact->len = strlen(dflt);

	return LDAP_SUCCESS;
}

static int sasl_interact(LDAP *ld, unsigned flags, void *defaults, void *in)
{
	sasl_interact_t *interact;

	for (interact = in; interact->id != SASL_CB_LIST_END; interact++) {
		int rc = __sasl_interaction(flags, interact, defaults);
		if (rc)
			return rc;
	}

	return LDAP_SUCCESS;
}

#define _UNIVENTION_LDAP_SECRET_LEN_MAX 27
int univention_ldap_set_admin_connection( univention_ldap_parameters_t *lp )
{
	FILE *secret;
	char *base = NULL;
	size_t len;

	base = univention_config_get_string("ldap/base");
	if (!base)
		goto err;
	asprintf(&lp->binddn, "cn=admin,%s", base);
	if (!lp->binddn) {
		free(base);
		goto err;
	}

	free(base);

	secret = fopen("/etc/ldap.secret", "r" );
	if (!secret)
		goto err1;

	lp->bindpw = calloc(_UNIVENTION_LDAP_SECRET_LEN_MAX, sizeof(char));
	if (!lp->bindpw) {
		fclose(secret);
		goto err1;
	}

	len = fread(lp->bindpw, _UNIVENTION_LDAP_SECRET_LEN_MAX, sizeof(char), secret);
	if (ferror(secret))
		len = -1;
	fclose(secret);

	for (; len >= 0; len--) {
		switch (lp->bindpw[len]) {
			case '\r':
			case '\n':
				lp->bindpw[len] = '\0';
			case '\0':
				continue;
			default:
				return 0;
		}
	}

	/* password already cleared memory. */
	FREE(lp->bindpw);
err1:
	FREE(lp->binddn);
err:
	return 1;
}

int univention_ldap_open(univention_ldap_parameters_t *lp)
{
	int rv = 0;
	struct berval cred;

	if (lp == NULL)
		return 1;
	if (lp->ld != NULL) {
		ldap_unbind_ext(lp->ld, NULL, NULL);
		lp->ld = NULL;
	}

	/* connection defaults */
	if (lp->version == 0) {
		lp->version = LDAP_VERSION3;
	}
	if (lp->host == NULL && lp->uri == NULL) {
		lp->host = univention_config_get_string("ldap/server/name");
		if (lp->host == NULL)
			return 1;
	}
	if (lp->port == 0 && lp->uri == NULL) {
		lp->port = 7389;
	}
	if (lp->base == NULL) {
		lp->base = univention_config_get_string("ldap/base");
		if (lp->base == NULL)
			return 1;
	}
	if (lp->authmethod == 0) {
		lp->authmethod = LDAP_AUTH_SIMPLE;
	}
	if (lp->authmethod == LDAP_AUTH_SASL) {
		if (lp->sasl_authzid == NULL) {
			struct passwd pwd, *result;
			char *buf;
			size_t bufsize;
			int s;

			bufsize = sysconf(_SC_GETPW_R_SIZE_MAX);
			if (bufsize == -1)
				bufsize = 16384;
			buf = malloc(bufsize);
			if (buf == NULL)
				return LDAP_OTHER;
			s = getpwuid_r(getuid(), &pwd, buf, bufsize, &result);
			if (result == NULL) {
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "could not lookup username");
				free(buf);
				return LDAP_OTHER;
			}
			asprintf(&lp->sasl_authzid, "u:%s", pwd.pw_name);
			free(buf);
		}
		if (lp->sasl_mech == NULL) {
			lp->sasl_mech = strdup("GSSAPI");
		}
		if (lp->sasl_realm == NULL && strcmp(lp->sasl_mech, "GSSAPI") == 0) {
			lp->sasl_realm = univention_config_get_string("kerberos/realm");
		}
	}

	/* if uri is given use that */
	if (lp->uri != NULL) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "connecting to %s", lp->uri);
		if ((rv = ldap_initialize(&lp->ld, lp->uri)) != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_initialize: %s", ldap_err2string(rv));
			return rv;
		}
	/* otherwise connect to host:port */
	} else {
		char uri[1024];
		snprintf(uri, sizeof(uri), "ldap://%s:%d", lp->host, lp->port);
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "connecting to ldap://%s:%d/", lp->host, lp->port);
		if ((rv = ldap_initialize(&lp->ld, uri)) != LDAP_SUCCESS) {
			ldap_unbind_ext(lp->ld, NULL, NULL);
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_initialize: %s", ldap_err2string(rv));
			return rv;
		}
	}

	/* set protocol version */
	ldap_set_option(lp->ld, LDAP_OPT_PROTOCOL_VERSION, &lp->version);

	/* TLS */
	if (lp->start_tls) {
		if ((rv = ldap_start_tls_s(lp->ld, NULL, NULL)) != LDAP_SUCCESS && lp->start_tls == 1) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "start_tls: %s", ldap_err2string(rv));
		} else if (rv != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "start_tls: %s", ldap_err2string(rv));
			return rv;
		}
	}

	/* sasl bind */
	if (lp->authmethod == LDAP_AUTH_SASL) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "sasl_bind");
		if ((rv = ldap_sasl_interactive_bind_s(lp->ld, lp->binddn, lp->sasl_mech, NULL, NULL, LDAP_SASL_QUIET, sasl_interact, (void*) lp)) != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_sasl_interactive_bind: %s", ldap_err2string(rv));
			ldap_unbind_ext(lp->ld, NULL, NULL);
			lp->ld = NULL;
			return rv;
		}
	/* simple bind */
	} else {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "simple_bind as %s", lp->binddn);
		if (lp->bindpw == NULL) {
			cred.bv_val = NULL;
			cred.bv_len = 0;
		} else {
			cred.bv_val = lp->bindpw;
			cred.bv_len = strlen(lp->bindpw);
		}

		if ((rv = ldap_sasl_bind_s(lp->ld, lp->binddn, LDAP_SASL_SIMPLE, &cred, NULL, NULL, NULL) != LDAP_SUCCESS)) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_simple_bind: %s", ldap_err2string(rv));
			ldap_unbind_ext(lp->ld, NULL, NULL);
			lp->ld = NULL;
			return rv;
		}
	}

	return LDAP_SUCCESS;
}

void univention_ldap_close(univention_ldap_parameters_t* lp)
{
	char *c;
	if (lp == NULL)
		return;
	if (lp->ld != NULL) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "closing connection");
		ldap_unbind_ext(lp->ld, NULL, NULL);
		lp->ld = NULL;
	}
	FREE(lp->uri);
	FREE(lp->host);
	FREE(lp->base);
	FREE(lp->binddn);
	/* clear password from memory. */
	for (c = lp->bindpw; c && *c; c++)
		*c = '\0';
	FREE(lp->bindpw);
	FREE(lp->sasl_mech);
	FREE(lp->sasl_realm);
	FREE(lp->sasl_authcid);
	FREE(lp->sasl_authzid);
	FREE(lp);
}
