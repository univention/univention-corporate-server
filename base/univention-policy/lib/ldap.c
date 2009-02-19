/*
 * Univention Policy
 *  C source of the univnetion policy libary
 *
 * Copyright (C) 2003-2009 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Binary versions of this file provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ldap.h>
#include <sasl/sasl.h>
#include <sys/types.h>
#include <pwd.h>

#include <univention/config.h>
#include <univention/ldap.h>
#include <univention/debug.h>

univention_ldap_parameters_t* univention_ldap_new(void)
{
	univention_ldap_parameters_t* lp;
	if ((lp=malloc(sizeof(univention_ldap_parameters_t))) == NULL)
		return NULL;
	lp->ld=NULL;
	lp->version=0;
	lp->host=NULL;
	lp->port=0;
	lp->uri=NULL;
	lp->start_tls=0;
	lp->base=NULL;
	lp->binddn=NULL;
	lp->bindpw=NULL;
	lp->authmethod=0;
	lp->sasl_mech=NULL;
	lp->sasl_realm=NULL;
	lp->sasl_authcid=NULL;
	lp->sasl_authzid=NULL;
	return lp;
}

static int __sasl_interaction(unsigned flags, sasl_interact_t *interact, univention_ldap_parameters_t *lp)
{
	const char *dflt = interact->defresult;

	switch (interact->id) {
	case SASL_CB_GETREALM:
		if (lp) dflt = lp->sasl_realm;
		break;
	case SASL_CB_AUTHNAME:
		if (lp) dflt = lp->sasl_authcid;
		break;
	case SASL_CB_PASS:
		if (lp) dflt = lp->bindpw;
		break;
	case SASL_CB_USER:
		if (lp) dflt = lp->sasl_authzid;
		break;
	case SASL_CB_NOECHOPROMPT:
		break;
	case SASL_CB_ECHOPROMPT:
		break;
        }

	if (dflt && !*dflt) dflt = interact->defresult;

	interact->result = dflt;
	interact->len = strlen(dflt);

	return LDAP_SUCCESS;
}

static int sasl_interact(LDAP *ld, unsigned flags, void *defaults, void *in)
{
	sasl_interact_t *interact;

	for (interact = in; interact->id != SASL_CB_LIST_END; interact++) {
		int rc = __sasl_interaction(flags, interact, defaults);
		if (rc) return rc;
	}

	return LDAP_SUCCESS;
}

int univention_ldap_set_admin_connection( univention_ldap_parameters_t *lp )
{
	FILE *secret;
	char *base    = NULL;

	base = univention_config_get_string("ldap/base");
	if ( !base ) {
		return 1;
	}
	lp->binddn=malloc( ( strlen(base)+strlen("cn=admin,")+1) * sizeof (char) );
	if ( !lp->binddn ) {
		free(base);
		return 1;
	}
	sprintf(lp->binddn, "cn=admin,%s", base );

	free(base);

	secret=fopen("/etc/ldap.secret", "r" );

	if ( !secret ) {
		return 1;
	}

	lp->bindpw=malloc(25*sizeof(char));

	if ( !lp->bindpw ) {
		return 1;
	}

	memset(lp->bindpw, 0, 25);

	fread(lp->bindpw,24,1,secret);

	if ( lp->bindpw[strlen(lp->bindpw)-1] == '\r' ) {
		lp->bindpw[strlen(lp->bindpw)-1]='\0';
	}
	if ( lp->bindpw[strlen(lp->bindpw)-1] == '\n' ) {
		lp->bindpw[strlen(lp->bindpw)-1]='\0';
	}

	fclose(secret);

	return 0;

}

int univention_ldap_open(univention_ldap_parameters_t *lp)
{
	int rv;

	if (lp == NULL)
		return 1;
	if (lp->ld != NULL) {
		ldap_unbind(lp->ld);
		lp->ld=NULL;
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
		lp->port = 389;
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
			struct passwd *pwd;
			pwd = getpwuid(getuid());
			if (pwd == NULL) {
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "could not lookup username\n");
				return LDAP_OTHER;
			}
			asprintf(&lp->sasl_authzid, "u:%s", (pwd->pw_name));
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
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "connecting to %s\n", lp->uri);
		if ((rv = ldap_initialize(&lp->ld, lp->uri)) != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_initialize: %s", ldap_err2string(rv));
			return rv;
		}
	/* otherwise connect to host:port */
	} else {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "connecting to ldap://%s:%d/", lp->host, lp->port);
		if ((lp->ld=ldap_init(lp->host, lp->port)) == NULL) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_init: %s", ldap_err2string(rv));
			return LDAP_OTHER;
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
			ldap_unbind(lp->ld);
			lp->ld = NULL;
			return rv;
		}
	/* simple bind */
	} else {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "simple_bind as %s", lp->binddn);
		if ((rv = ldap_simple_bind_s(lp->ld, lp->binddn, lp->bindpw)) != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "ldap_simple_bind: %s", ldap_err2string(rv));
			ldap_unbind(lp->ld);
			lp->ld = NULL;
			return rv;
		}
	}

	return LDAP_SUCCESS;
}

void univention_ldap_close(univention_ldap_parameters_t* lp)
{
	if (lp == NULL)
		return;
	if (lp->ld != NULL) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "closing connection");
		ldap_unbind(lp->ld);
		lp->ld = NULL;
	}
	if (lp->uri != NULL) {
		free(lp->uri);
		lp->uri = NULL;
	}
	if (lp->host != NULL) {
		free(lp->host);
		lp->host = NULL;
	}
	if (lp->base != NULL) {
		free(lp->base);
		lp->base = NULL;
	}
	if (lp->binddn != NULL) {
		free(lp->binddn);
		lp->binddn = NULL;
	}
	if (lp->bindpw != NULL) {
		free(lp->bindpw);
		lp->bindpw = NULL;
	}
	if (lp->sasl_mech != NULL) {
		free(lp->sasl_mech);
		lp->sasl_mech = NULL;
	}
	if (lp->sasl_realm != NULL) {
		free(lp->sasl_realm);
		lp->sasl_realm = NULL;
	}
	if (lp->sasl_authcid != NULL) {
		free(lp->sasl_authcid);
		lp->sasl_authcid = NULL;
	}
	if (lp->sasl_authzid != NULL) {
		free(lp->sasl_authzid);
		lp->sasl_authzid = NULL;
	}
	if (lp != NULL) {
		free(lp);
		lp = NULL;
	}
}
