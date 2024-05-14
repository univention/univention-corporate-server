/*
 * Univention Policy
 *  C source of the univention policy library
 *
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2003-2024 Univention GmbH
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
#include "internal.h"

#include <fcntl.h>
#include <ldap.h>
#include <pwd.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/types.h>
#include <sasl/sasl.h>
#include <univention/config.h>
#include <univention/debug.h>
#include <univention/ldap.h>

univention_ldap_parameters_t *univention_ldap_new(void) {
	univention_ldap_parameters_t *lp;
	if ((lp = calloc(1, sizeof(univention_ldap_parameters_t))) == NULL)
		return NULL;
	/* connection defaults */
	lp->version = LDAP_VERSION3;
	lp->authmethod = LDAP_AUTH_SIMPLE;
	lp->start_tls = univention_config_get_int("directory/manager/starttls");
	return lp;
}

static int __sasl_interaction(unsigned flags, sasl_interact_t *interact, univention_ldap_parameters_t *lp) {
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

static int sasl_interact(LDAP *ld, unsigned flags, void *defaults, void *in) {
	sasl_interact_t *interact;

	for (interact = in; interact->id != SASL_CB_LIST_END; interact++) {
		int rc = __sasl_interaction(flags, interact, defaults);
		if (rc)
			return rc;
	}

	return LDAP_SUCCESS;
}


#define MAX_SECRET_SIZE 256
char *univention_ldap_read_secret(const char *filename) {
	char buf[MAX_SECRET_SIZE + 1];
	int fd = open(filename, O_RDONLY);
	if (fd < 0) {
		perror("ldap_read_secret: open failed");
		return NULL;
	}
	int count = read(fd, buf, MAX_SECRET_SIZE);
	close(fd);
	if (count < 0 || count > MAX_SECRET_SIZE) {
		perror("ldap_read_secret: read failed");
		return NULL;
	}
	buf[count] = '\0';
	char *c = strstr(buf, "\n");
	if (c)
		*c = '\0';
	return strdup(buf);
}


int univention_ldap_set_admin_connection(univention_ldap_parameters_t *lp) {
	char *base = NULL;
	int s;

	base = univention_config_get_string("ldap/base");
	if (!base) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "UCRV ldap/base unset");
		goto err;
	}
	FREE(lp->binddn);
	s = asprintf(&lp->binddn, "cn=admin,%s", base);
	free(base);
	if (s < 0 || !lp->binddn) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "asprintf(binddn) failed");
		goto err;
	}

	FREE(lp->bindpw);
	lp->bindpw = univention_ldap_read_secret("/etc/ldap.secret");
	if (!lp->bindpw) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_read_secret() failed");
		goto err;
	}
	if (*lp->bindpw)
		return 0;

	/* password already cleared memory. */
err:
	FREE(lp->bindpw);
	FREE(lp->binddn);
	return 1;
}

static int cb_urllist_proc(LDAP *ld, LDAPURLDesc **urllist, LDAPURLDesc **url, void *params) {
	univention_ldap_parameters_t *lp = params;
	return 0;
}

int univention_ldap_open(univention_ldap_parameters_t *lp) {
	int rv = LDAP_OTHER;
	struct berval cred;
	char *uri;

	if (lp == NULL)
		return 1;
	if (lp->ld != NULL) {
		ldap_unbind_ext(lp->ld, NULL, NULL);
		lp->ld = NULL;
	}

	if (lp->base == NULL) {
		lp->base = univention_config_get_string("ldap/base");
		if (lp->base == NULL) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "UCRV ldap/base unset");
			goto out;
		}
	}

	if (lp->uri != NULL) {
		uri = lp->uri;
	} else {
		int s;
		char *schema = "ldap";

		if (lp->host == NULL)
			lp->host = univention_config_get_string("ldap/server/name");
		if (lp->host == NULL) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "UCRV ldap/server/name unset");
			goto out;
		}

		if (lp->port == 0)
			lp->port = univention_config_get_int("ldap/server/port");
		if (lp->port < 0)
			lp->port = 7389;
		if (lp->port == 636 || lp->port == 7636)
			schema = "ldaps";

		s = asprintf(&uri, "%s://%s:%d", schema, lp->host, lp->port);
		if (s < 0 || !uri) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "asprintf(uri) failed");
			goto out;
		}
	}
	univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "connecting to %s", uri);
	rv = ldap_initialize(&lp->ld, uri);
	if (uri != lp->uri)
		free(uri);
	if (rv != LDAP_SUCCESS) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_initialize: %s", ldap_err2string(rv));
		goto error;
	}

	rv = ldap_set_urllist_proc(lp->ld, cb_urllist_proc, lp);

	/* set protocol version */
	ldap_set_option(lp->ld, LDAP_OPT_PROTOCOL_VERSION, &lp->version);

	/* TLS */
	if (lp->start_tls) {
		if ((rv = ldap_start_tls_s(lp->ld, NULL, NULL)) != LDAP_SUCCESS) {
			if (lp->start_tls == 1) {
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "start_tls: %s", ldap_err2string(rv));
			} else {
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "start_tls: %s", ldap_err2string(rv));
				goto error_unbind;
			}
		}
	}

	switch (lp->authmethod) {
	case LDAP_AUTH_SASL:
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "sasl_bind");
		if (lp->sasl_authzid == NULL) {
			struct passwd pwd, *result;
			char *buf;
			size_t bufsize;
			int s;

			rv = LDAP_OTHER;
			bufsize = sysconf(_SC_GETPW_R_SIZE_MAX);
			if (bufsize == -1)
				bufsize = 16384;
			buf = malloc(bufsize);
			if (buf == NULL) {
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "malloc(getpwuid) failed");
				goto error_unbind;
			}
			s = getpwuid_r(getuid(), &pwd, buf, bufsize, &result);
			if (result == NULL) {
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "could not lookup username");
				free(buf);
				goto error_unbind;
			}
			s = asprintf(&lp->sasl_authzid, "u:%s", pwd.pw_name);
			if (s < 0 || !lp->sasl_authzid) {
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "asprintf(sasl_authzid) failed");
				free(buf);
				goto error_unbind;
			}
			free(buf);
		}
		if (lp->sasl_mech == NULL) {
			lp->sasl_mech = strdup("GSSAPI");
		}
		if (lp->sasl_realm == NULL && strcmp(lp->sasl_mech, "GSSAPI") == 0) {
			lp->sasl_realm = univention_config_get_string("kerberos/realm");
		}
		if ((rv = ldap_sasl_interactive_bind_s(lp->ld, lp->binddn, lp->sasl_mech, NULL, NULL, LDAP_SASL_QUIET, sasl_interact, (void *)lp)) == LDAP_SUCCESS)
			goto out;
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_sasl_interactive_bind: %s", ldap_err2string(rv));
		break;

	case LDAP_AUTH_SIMPLE:
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "simple_bind as %s", lp->binddn);
		cred.bv_val = lp->bindpw;
		cred.bv_len = lp->bindpw ? strlen(lp->bindpw) : 0;

		if ((rv = ldap_sasl_bind_s(lp->ld, lp->binddn, LDAP_SASL_SIMPLE, &cred, NULL, NULL, NULL)) == LDAP_SUCCESS)
			goto out;
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
out:
	return rv;
}

void univention_ldap_close(univention_ldap_parameters_t *lp) {
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
