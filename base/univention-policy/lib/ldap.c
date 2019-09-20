/*
 * Univention Policy
 *  C source of the univention policy library
 *
 * Copyright 2003-2019 Univention GmbH
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
	/* connection defaults */
	lp->version = LDAP_VERSION3;
	lp->authmethod = LDAP_AUTH_SIMPLE;
	lp->start_tls = 2;
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
	if (!base) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "UCRV ldap/base unset");
		goto err;
	}
	FREE(lp->binddn);
	len = asprintf(&lp->binddn, "cn=admin,%s", base);
	free(base);
	if (len < 0 || !lp->binddn) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "asprintf(binddn) failed");
		goto err;
	}

	FREE(lp->bindpw);
	lp->bindpw = calloc(_UNIVENTION_LDAP_SECRET_LEN_MAX, sizeof(char));
	if (!lp->bindpw) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "calloc(bindpw) failed");
		goto err;
	}

	secret = fopen("/etc/ldap.secret", "r" );
	if (!secret) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "open(/etc/ldap.secret) failed");
		goto err;
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
err:
	FREE(lp->bindpw);
	FREE(lp->binddn);
	return 1;
}

int univention_ldap_open(univention_ldap_parameters_t *lp)
{
	int rv = LDAP_OTHER;
	struct berval cred;

	if (lp == NULL)
		return 1;
	if (lp->ld != NULL) {
		ldap_unbind_ext(lp->ld, NULL, NULL);
		lp->ld = NULL;
	}

	if (lp->host == NULL && lp->uri == NULL) {
		lp->host = univention_config_get_string("ldap/server/name");
		if (lp->host == NULL) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "UCRV ldap/server/name unset");
			goto error;
		}
	}
	if (lp->port == 0 && lp->uri == NULL) {
		lp->port = 7389;
	}
	if (lp->base == NULL) {
		lp->base = univention_config_get_string("ldap/base");
		if (lp->base == NULL) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "UCRV ldap/base unset");
			goto error;
		}
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
			if (buf == NULL) {
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "malloc(getpwuid) failed");
				goto error;
			}
			s = getpwuid_r(getuid(), &pwd, buf, bufsize, &result);
			if (result == NULL) {
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "could not lookup username");
				free(buf);
				goto error;
			}
			s = asprintf(&lp->sasl_authzid, "u:%s", pwd.pw_name);
			if (s < 0) {
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "asprintf(sasl_authzid) failed");
				free(buf);
				goto error;
			}
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
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_PROCESS, "connecting to %s", lp->uri);
		if ((rv = ldap_initialize(&lp->ld, lp->uri)) != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_initialize: %s", ldap_err2string(rv));
			goto error;
		}
	/* otherwise connect to host:port */
	} else {
		char uri[1024];
		snprintf(uri, sizeof(uri), "ldap://%s:%d", lp->host, lp->port);
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_PROCESS, "connecting to %s", uri);
		if ((rv = ldap_initialize(&lp->ld, uri)) != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_initialize: %s", ldap_err2string(rv));
			goto error;
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
			goto error_unbind;
		}
	}

	switch (lp->authmethod) {
	case LDAP_AUTH_SASL:
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "sasl_bind");
		if ((rv = ldap_sasl_interactive_bind_s(lp->ld, lp->binddn, lp->sasl_mech, NULL, NULL, LDAP_SASL_QUIET, sasl_interact, (void*) lp)) == LDAP_SUCCESS)
			goto success;
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_sasl_interactive_bind: %s", ldap_err2string(rv));
		break;

	case LDAP_AUTH_SIMPLE:
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "simple_bind as %s", lp->binddn);
		if (lp->bindpw == NULL) {
			cred.bv_val = NULL;
			cred.bv_len = 0;
		} else {
			cred.bv_val = lp->bindpw;
			cred.bv_len = strlen(lp->bindpw);
		}

		if ((rv = ldap_sasl_bind_s(lp->ld, lp->binddn, LDAP_SASL_SIMPLE, &cred, NULL, NULL, NULL)) == LDAP_SUCCESS)
			goto success;
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_simple_bind: %s", ldap_err2string(rv));
		break;

	default:
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "unsupported auth method %d", lp->authmethod);
		rv = LDAP_OTHER;
	}
error_unbind:
	ldap_unbind_ext(lp->ld, NULL, NULL);
error:
	lp->ld = NULL;
success:
	return rv;
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
