/*
 * Copyright (c) 2022-2024 Univention GmbH
 * Copyright (c) 2009-2015 Emmanuel Dreyfus
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. All advertising materials mentioning features or use of this software
 *    must display the following acknowledgement:
 *        This product includes software developed by Emmanuel Dreyfus
 *
 * THIS SOFTWARE IS PROVIDED ``AS IS'' AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
 * OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#include "config.h"

#include <stdio.h>
#include <stdlib.h>
#include <ctype.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <syslog.h>
#include <stdarg.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/queue.h>

#include <jansson.h>

#include <sasl/sasl.h>
#include <sasl/saslplug.h>
#include <sasl/saslutil.h>

#include "oauthbearer.h"

#include "plugin_common.h"

#define MAX_CLIENTIN_LEN 65536
#define MAX_SERVERIN_LEN 65536

#define BEARER_PREFIX "Bearer "
#define BEARER_LEN strlen(BEARER_PREFIX)

typedef struct {
	char *clientout_buf;
	unsigned int clientout_buf_size;
} oauth_client_context;

static oauth_glob_context_t server_glob_context;

void oauth_log(
	const void *utils,
	int pri,
	const char *fmt,
	...
) {
	sasl_utils_t *sasl_utils;
	char msg[4096];
	va_list ap;

	sasl_utils = (sasl_utils_t *)utils;
	switch (pri) {
	case LOG_DEBUG:
		pri = SASL_LOG_DEBUG;
		break;
	case LOG_NOTICE:
		pri = SASL_LOG_NOTE;
		break;
	default:
		pri = SASL_LOG_ERR;
		break;
	}

	va_start(ap, fmt);
	vsnprintf(msg, sizeof(msg), fmt, ap);
	sasl_utils->log(sasl_utils->conn, pri, "%s", msg);
	va_end(ap);
}

void oauth_error(
	const void *utils,
	int pri,
	const char *fmt,
	...
) {
	sasl_utils_t *sasl_utils;
	char msg[4096];
	va_list ap;

	sasl_utils = (sasl_utils_t *)utils;

	va_start(ap, fmt);
	vsnprintf(msg, sizeof(msg), fmt, ap);
	sasl_utils->seterror(sasl_utils->conn, 0, "%s", msg);
	va_end(ap);
}

int oauth_strdup(
	const void *utils,
	const char *src,
	char **dst,
	int *len
) {
	sasl_utils_t *sasl_utils;

	sasl_utils = (sasl_utils_t *)utils;
	return _plug_strdup(sasl_utils, src, dst, len);
}

int oauth_retcode(
	enum OAuthError code
) {
	switch(code) {
	case OK:
		return SASL_OK;
	case MISSING_UID_CLAIM:
	case PARSE_ERROR:
		return SASL_BADPARAM;
	case INVALID_ISSUER:
	case INVALID_AUDIENCE:
	case INVALID_AUTHORIZED_PARTY:
	case CLAIM_EXPIRED:
	case INVALID_SIGNATURE:
		return SASL_BADAUTH;
	case CONFIG_ERROR:
	default:
		return SASL_FAIL;
	}
}

/* Convert saslname = 1*(value-safe-char / "=2C" / "=3D") in place.
   Returns SASL_FAIL if the encoding is invalid, otherwise SASL_OK */
static int decode_saslname(
	char *buf
) {
	char *inp;
	char *outp;

	inp = outp = buf;

	while (*inp) {
		if (*inp == '=') {
			inp++;
			if (*inp == '\0') {
				return SASL_FAIL;
			}
			if (inp[0] == '2' && inp[1] == 'C') {
				*outp = ',';
				inp += 2;
			} else if (inp[0] == '3' && inp[1] == 'D') {
				*outp = '=';
				inp += 2;
			} else {
				return SASL_FAIL;
			}
		} else {
			*outp = *inp;
			inp++;
		}
		outp++;
	}

	*outp = '\0';

	return SASL_OK;
}

/* Convert a username to saslname = 1*(value-safe-char / "=2C" / "=3D")
   and return an allocated copy.
   "freeme" contains pointer to the allocated output, or NULL,
   if encoded_saslname just points to saslname.
   Returns SASL_NOMEM if can't allocate memory for the output, otherwise SASL_OK */
static int encode_saslname(
	const char *saslname,
	const char **encoded_saslname,
	char **freeme
) {
	const char * inp;
	char * outp;
	int special_chars = 0;

	/* Found out if anything needs encoding */
	for (inp = saslname; *inp; inp++) {
		if (*inp == ',' || *inp == '=') {
			special_chars++;
		}
	}

	if (special_chars == 0) {
		*encoded_saslname = saslname;
		*freeme = NULL;
		return SASL_OK;
	}

	outp = malloc(strlen(saslname) + special_chars * 2 + 1);
	*encoded_saslname = outp;
	*freeme = outp;
	if (outp == NULL) {
		return SASL_NOMEM;
	}

	for (inp = saslname; *inp; inp++) {
		switch (*inp) {
			case ',':
				*outp++ = '=';
				*outp++ = '2';
				*outp++ = 'C';
				break;

			case '=':
				*outp++ = '=';
				*outp++ = '3';
				*outp++ = 'D';
				break;

			default:
				*outp++ = *inp;
		}
	}

	*outp = '\0';

	return SASL_OK;
}

char * oauthbearer_error_as_json(
	enum OAuthError code
) {
	/* RFC 7628: 3.2.2 Server Response to Failed Authentication

	status (REQUIRED)
	scope (OPTIONAL)
	openid-configuration (OPTIONAL)
	*/

	// How much do we want to disclose? Let's go with the minimum first
	// otherwise we could send oauth_enum_error_string(code)
	json_t *j_response = json_pack("{ss}", "status", "invalid_token");
	char *tmp = json_dumps(j_response, 0);
	json_decref(j_response);
	return tmp;
}

static int oauth_server_mech_new(
	void *glob_context,
	sasl_server_params_t *params,
	const char *challenge,
	unsigned int challen,
	void **conn_context
) {
	oauth_serv_context_t *ctx;

	if (conn_context == NULL) {
		params->utils->seterror(params->utils->conn, 0, "NULL conn_context");
		return SASL_BADPARAM;
	}

	if ((ctx = params->utils->malloc(sizeof(*ctx))) == NULL) {
		params->utils->seterror(params->utils->conn, 0, "cannot allocate server context");
		return SASL_NOMEM;
	}

	memset(ctx, 0, sizeof(*ctx));
	ctx->glob_context = glob_context;
	*conn_context = ctx;

	return SASL_OK;
}

static int get_client_response_key(
	const sasl_utils_t *utils,
	const char *searchkey,
	const char *client_response,
	char **authzid,
	char **value
) {
	/* GS2 header rule ABNF:

	kvsep          = %x01
	key            = 1*(ALPHA)
	value          = *(VCHAR / SP / HTAB / CR / LF )
	kvpair         = key "=" value kvsep
	;;gs2-header   = See RFC 5801
	client-resp    = (gs2-header kvsep *kvpair kvsep) / kvsep
	*/
	const int kvsep = 0x01; // client_response separator
	const size_t kvsep_length = 1;
	const size_t searchkey_length = strlen(searchkey);
	const char *current_pos = NULL;
	int result;

	// Note: This algorithm is not ensuring that the client_response
	//       ends with two kvsep characters.

	if (authzid) {
		// Try to extract an authzid from the gs2-header
		if (!strncmp(client_response, "n,a=", 4)) {
			current_pos = client_response + 4;
			const char *authzid_end = strstr(current_pos, ",\1");
			if (authzid_end) {
				if (authzid_end > strchr(current_pos, kvsep)) {
					return SASL_BADPROT;
				}
				unsigned int len = authzid_end - current_pos;
				unsigned int authzid_len;
				result = _plug_buf_alloc(utils, authzid, &authzid_len, len + 1);
				if (result != SASL_OK) {
					return result;
				}
				memcpy(*authzid, current_pos, len);
				(*authzid)[len] = '\0';
				decode_saslname(*authzid);
			} else {
				return SASL_BADPROT;
			}
		}
	}

	// Skip the gs2-header
	current_pos = strchr(client_response, kvsep);
	if (!current_pos) {
		return SASL_BADPROT;
	}

	while (current_pos != NULL && *current_pos != '\0') {
		const char *key_start = current_pos + kvsep_length;
		const char *key_end = strchr(current_pos, '=');

		if (!key_end) {
			return SASL_BADPROT;
		}

		size_t key_length = key_end - key_start;
		const char *val_start = key_end + 1;  // skip "="
		const char *next_sep = strchr(val_start, kvsep);
		if (!next_sep) {
			// no terminating kvsep
			return SASL_BADPROT;
		}

		if (key_length == searchkey_length && strncmp(key_start, searchkey, key_length) == 0) {
			size_t val_length = next_sep - val_start;
			*value = (char *)utils->malloc(val_length + 1);
			strncpy(*value, val_start, val_length);
			(*value)[val_length] = '\0';

			return SASL_OK;
		}

		current_pos = next_sep + kvsep_length;
	}

	return SASL_BADPROT;
}


static int oauth_server_mech_step(
	void *conn_context,
	sasl_server_params_t *params,
	const char *clientin,
	unsigned int clientinlen,
	const char **serverout,
	unsigned int *serveroutlen,
	sasl_out_params_t *oparams
) {
	oauth_serv_context_t *ctx = (oauth_serv_context_t *)conn_context;
	// oauth_glob_context_t *gctx;
	char *authzid = NULL;
	const char *authcid = NULL;
	char *auth_msg = NULL;
	const sasl_ssf_t *ssfp = NULL;
	int error = SASL_OK;
	enum OAuthError oauth_errno;

	/* Sanity checks */
	if ((ctx == NULL) ||
		(params == NULL) ||
		(params->utils == NULL) ||
		(params->utils->conn == NULL) ||
		(params->utils->getcallback == NULL) ||
		(serverout == NULL) ||
		(serveroutlen == NULL) ||
		(oparams == NULL)) {
		params->utils->seterror(params->utils->conn, 0, "Bad parameters");
		return SASL_BADPARAM;
	}

	/* Check if the connection is over TLS */
	if (sasl_getprop(params->utils->conn, SASL_SSF_EXTERNAL, (const void **)&ssfp) != SASL_OK) {
		params->utils->seterror(params->utils->conn, 0, "could not get SASL_SSF_EXTERNAL");
		return SASL_BADPARAM;
	}
	if (!((ssfp ? *ssfp : 0) >= 256)) {
		params->utils->seterror(params->utils->conn, 0, "TLS required!");
		return SASL_ENCRYPT;
	}

	/* Limit */
	if (clientinlen > MAX_CLIENTIN_LEN) {
		params->utils->seterror(params->utils->conn, 0, "client data too big (%d)", clientinlen);
		return SASL_BADPROT;
	}

	*serverout = NULL;
	*serveroutlen = 0;

	if (clientinlen == 1 && !strcmp(clientin, "\1")) {
		// TODO: RFC 7628: 3.2.3 Completing an Error Message Sequence
		error = SASL_BADAUTH;
		goto doneout;
	}

	unsigned int rfc7628_msg_len = strlen(clientin);
	if (rfc7628_msg_len != clientinlen) {
		params->utils->seterror(params->utils->conn, 0, "Unexpected data (%d vs %d)", rfc7628_msg_len, clientinlen);
		return SASL_BADPROT;
	}

	error = get_client_response_key(params->utils, "auth", clientin, &authzid, &auth_msg);
	if (error != SASL_OK) {
		params->utils->seterror(params->utils->conn, 0, "No auth found in client response (error=%d)", error);
		goto out;
	}

	if (strncasecmp(auth_msg, BEARER_PREFIX, BEARER_LEN) != 0) {
		params->utils->seterror(params->utils->conn, 0, "No bearer token given.");
		error = SASL_BADPARAM;
		goto out;
	}

	char *jwt_msg = auth_msg + BEARER_LEN;

	/*
	 * Validate JWT signature, retreive authcid
	 */
	if ((oauth_errno = oauth_check_jwt(ctx, params->utils, &authcid, jwt_msg)) != OK) {
		ctx->serverout_buf = oauthbearer_error_as_json(oauth_errno);
		*serverout = ctx->serverout_buf;
		*serveroutlen = (unsigned int) strlen(*serverout);
		error = SASL_CONTINUE;  // RFC 7628
		goto out;
	}
	if (authcid == NULL) {
		params->utils->seterror(params->utils->conn, 0, "No authcid found");
		error = SASL_NOUSER;
		goto out;
	}

	/* Canonicalize Userid if we have one */
	if ((authzid != NULL) && (*authzid != '\0')) {
		if ((error = params->canon_user(params->utils->conn, authzid, 0, SASL_CU_AUTHZID, oparams)) != SASL_OK) {
			params->utils->seterror(params->utils->conn, 0, "canon_user failed for authzid (error=%d)", error);
			goto out;
		}
		if ((error = params->canon_user(params->utils->conn, authcid, 0, SASL_CU_AUTHID, oparams)) != SASL_OK) {
			params->utils->seterror(params->utils->conn, 0, "canon_user failed for authcid (error=%d)", error);
			goto out;
		}
	} else {
		if ((error = params->canon_user(params->utils->conn, authcid, 0, SASL_CU_AUTHID|SASL_CU_AUTHZID, oparams)) != SASL_OK) {
			params->utils->seterror(params->utils->conn, 0, "canon_user failed for userid (both) (error=%d)", error);
			goto out;
		}
	}

doneout:
	oparams->doneflag = 1;
	oparams->mech_ssf = 0;
	oparams->maxoutbuf = 0;
	oparams->encode_context = NULL;
	oparams->encode = NULL;
	oparams->decode_context = NULL;
	oparams->decode = NULL;
	oparams->param_version = 0;

out:
	if (auth_msg != NULL) {
		params->utils->erasebuffer(auth_msg, strlen(auth_msg));
		params->utils->free(auth_msg);
	}
	if (authzid != NULL) {
		params->utils->erasebuffer(authzid, strlen(authzid));
		params->utils->free(authzid);
	}

	return error;
}

static void oauth_server_mech_dispose(
	void *conn_context,
	const sasl_utils_t *utils
) {
	oauth_serv_context_t *ctx = (oauth_serv_context_t *)conn_context;

	if (ctx != NULL) {
		if (ctx->authcid != NULL)
			utils->free(ctx->authcid);

		if (ctx->serverout_buf != NULL)
			utils->free(ctx->serverout_buf);

		utils->free(ctx);
	}

	return;
}

static void oauth_server_mech_free(
	void *glob_context,
	const sasl_utils_t *utils
) {
	struct oauth_list *item;
	oauth_glob_context_t *gctx;

	gctx = (oauth_glob_context_t *)glob_context;

	if (gctx->uid_attr != NULL) {
		free((void *)gctx->uid_attr);
		gctx->uid_attr = NULL;
	}

	if (gctx->jwks != NULL) {
		r_jwks_free(gctx->jwks);
		gctx->jwks = NULL;
	}

	if (gctx->trusted_jwks_str != NULL) {
		free(gctx->trusted_jwks_str);
		gctx->trusted_jwks_str = NULL;
	}

	while ((item = SLIST_FIRST(&gctx->trusted_aud)) != NULL) {
		SLIST_REMOVE_HEAD(&gctx->trusted_aud, next);
		free(item);
	}

	while ((item = SLIST_FIRST(&gctx->trusted_azp)) != NULL) {
		SLIST_REMOVE_HEAD(&gctx->trusted_azp, next);
		free(item);
	}

	while ((item = SLIST_FIRST(&gctx->required_scope)) != NULL) {
		SLIST_REMOVE_HEAD(&gctx->required_scope, next);
		free(item);
	}

	r_global_close();

	/*
	 * Do not free (oauth_glob_context_t *)glob_context, it is static!
	 */
}


static sasl_server_plug_t oauth_server_plugin = {
	"OAUTHBEARER",  /* mech_name */
	0,  /* max_ssf */
	SASL_SEC_NOANONYMOUS,  /* security_flags */
	SASL_FEAT_WANT_CLIENT_FIRST | SASL_FEAT_ALLOWS_PROXY, /* features */
	&server_glob_context,  /* glob_context */
	&oauth_server_mech_new,  /* mech_new */
	&oauth_server_mech_step,  /* mech_step */
	&oauth_server_mech_dispose,  /* mech_dispose */
	&oauth_server_mech_free,  /* mech_free */
	NULL,  /* setpass */
	NULL,  /* user_query */
	NULL,  /* idle */
	NULL,  /* mech_avail */
	NULL  /* spare */
};

int sasl_server_plug_init(
	const sasl_utils_t *utils,
	int maxvers,
	int *outvers,
	sasl_server_plug_t **pluglist,
	int *plugcount
) {
	oauth_glob_context_t *gctx;
	int r;
	const char *val;
	const char *grace;
	char propname[1024];
	int propnum = 0;
	FILE *jwks_fp;

	if (maxvers < SASL_SERVER_PLUG_VERSION) {
		utils->log(NULL, SASL_LOG_ERR, "OAUTHBEARER version mismatch");
		return SASL_BADVERS;
	}

	*outvers = SASL_SERVER_PLUG_VERSION;
	*pluglist = &oauth_server_plugin;
	*plugcount = 1;

	gctx = (oauth_glob_context_t *)oauth_server_plugin.glob_context;
	memset(gctx, 0, sizeof(*gctx));

	if (r_global_init() != RHN_OK) {
		utils->log(NULL, SASL_LOG_ERR, "OAUTHBEARER r_global_init failed");
		return SASL_FAIL;
	}

	/*
	 * Attribute to be used for authcid
	 */
	r = utils->getopt(utils->getopt_context, "OAUTHBEARER", "oauthbearer_userid", &val, NULL);
	if ((r != 0) || (val == NULL) || (*val == '\0')) {
		if((gctx->uid_attr = strdup("preferred_username")) == NULL) {
			utils->log(NULL, SASL_LOG_ERR, "cannot allocate memory");
			return SASL_NOMEM;
		}
	} else if((gctx->uid_attr = strdup(val)) == NULL) {
		utils->log(NULL, SASL_LOG_ERR, "cannot allocate memory");
		return SASL_NOMEM;
	}

	/*
	 * Grace delay for clock skews
	 */
	r = utils->getopt(utils->getopt_context, "OAUTHBEARER", "oauthbearer_grace", &grace, NULL);
	if ((r != 0) || (grace == NULL) || (*grace == '\0'))
		gctx->grace = (time_t)3;
	else
		gctx->grace = atoi(grace);

	/*
	 * Load the trusted audiences
	 */
	propnum = 0;
	SLIST_INIT(&gctx->trusted_aud);
	do {
		const char *trusted_aud;
		struct oauth_list *item;

		(void)snprintf(propname, sizeof(propname), "oauthbearer_trusted_aud%d", propnum);
		propnum++;

		if (utils->getopt(utils->getopt_context, "OAUTHBEARER", propname, &trusted_aud, NULL) != 0)
			break;

		if ((item = utils->malloc(sizeof(*item))) == NULL) {
			utils->log(NULL, SASL_LOG_ERR, "cannot allocate memory");
			return SASL_NOMEM;
		}

		item->name = trusted_aud;  // just points to the getopt string
		SLIST_INSERT_HEAD(&gctx->trusted_aud, item, next);
	} while (1 /*CONSTCOND*/);

	if (SLIST_EMPTY(&gctx->trusted_aud)) {
		utils->log(NULL, SASL_LOG_ERR, "No trusted audiences configured");
		return SASL_CONFIGERR;
	}

	/*
	 * Load the trusted authorized parties
	 */
	propnum = 0;
	SLIST_INIT(&gctx->trusted_azp);
	do {
		const char *trusted_azp;
		struct oauth_list *item;

		(void)snprintf(propname, sizeof(propname), "oauthbearer_trusted_azp%d", propnum);
		propnum++;

		if (utils->getopt(utils->getopt_context, "OAUTHBEARER", propname, &trusted_azp, NULL) != 0)
			break;

		if ((item = utils->malloc(sizeof(*item))) == NULL) {
			utils->log(NULL, SASL_LOG_ERR, "cannot allocate memory");
			return SASL_NOMEM;
		}

		item->name = trusted_azp;  // just points to the getopt string
		SLIST_INSERT_HEAD(&gctx->trusted_azp, item, next);
	} while (1 /*CONSTCOND*/);

	/*
	 * Load the required scopes
	 */
	propnum = 0;
	SLIST_INIT(&gctx->required_scope);
	do {
		const char *required_scope;
		struct oauth_list *item;

		(void)snprintf(propname, sizeof(propname), "oauthbearer_required_scope%d", propnum);
		propnum++;

		if (utils->getopt(utils->getopt_context, "OAUTHBEARER", propname, &required_scope, NULL) != 0)
			break;

		if ((item = utils->malloc(sizeof(*item))) == NULL) {
			utils->log(NULL, SASL_LOG_ERR, "cannot allocate memory");
			return SASL_NOMEM;
		}

		item->name = required_scope;  // just points to the getopt string
		SLIST_INSERT_HEAD(&gctx->required_scope, item, next);
	} while (1 /*CONSTCOND*/);

	/*
	 * Load the trusted iss names
	 */
	propnum = 0;
	do {
		if (propnum > 0)  // TODO: support multiple issuers
			break;

		(void)snprintf(propname, sizeof(propname), "oauthbearer_trusted_iss%d", propnum);
		propnum++;

		if (utils->getopt(utils->getopt_context, "OAUTHBEARER", propname, &gctx->trusted_iss, NULL) != 0)
			break;

		if ((gctx->trusted_iss == NULL) || (*gctx->trusted_iss == '\0')) {
			utils->log(NULL, SASL_LOG_ERR, "Unable to get issuer from \"%s\"", propname);
			continue;
		}
	} while (1 /*CONSTCOND*/);

	if (gctx->trusted_iss == NULL) {
		utils->log(NULL, SASL_LOG_ERR, "No trusted issuer configured");
		return SASL_CONFIGERR;
	}

	/*
	 * Load the JWKS file
	 */
	propnum = 0;
	do {
		const char *jwks_filename;

		if (propnum > 0)  // TODO: support multiple JWKS
			break;

		(void)snprintf(propname, sizeof(propname), "oauthbearer_trusted_jwks%d", propnum);
		propnum++;

		if (utils->getopt(utils->getopt_context, "OAUTHBEARER", propname, &jwks_filename, NULL) != 0)
			break;

		if ((jwks_filename == NULL) || (*jwks_filename == '\0'))
			continue;

		if (access(jwks_filename, R_OK) != 0) {
			utils->log(NULL, SASL_LOG_ERR, "Unable to read Issuer JWKS file \"%s\" (%s)", jwks_filename, strerror(errno));
			continue;
		}

		if ((gctx->trusted_jwks_str = utils->malloc(JWKS_BUFFSIZE)) == NULL) {
			utils->log(NULL, SASL_LOG_ERR, "cannot allocate memory");
			return SASL_NOMEM;
		}

		jwks_fp = fopen(jwks_filename, "r");
		if (jwks_fp == NULL) {
			utils->log(NULL, SASL_LOG_ERR, "Failed to open JWKS file \"%s\" (%s)", jwks_filename, strerror(errno));
			return SASL_CONFIGERR;
		}
		if (NULL == fgets(gctx->trusted_jwks_str, JWKS_BUFFSIZE, jwks_fp)) {
			fclose(jwks_fp);
			utils->log(NULL, SASL_LOG_ERR, "Failed to load JWKS from \"%s\"", jwks_filename);
			return SASL_CONFIGERR;
		}
		fclose(jwks_fp);

		if (!gctx->trusted_jwks_str) {
			utils->log(NULL, SASL_LOG_ERR, "Failed to load JWKS from \"%s\"", jwks_filename);
			continue;
		}

		utils->log(NULL, SASL_LOG_NOTE, "Loaded JWKS from \"%s\"", jwks_filename);
	} while (1 /*CONSTCOND*/);

	if (gctx->trusted_jwks_str == NULL) {
		utils->log(NULL, SASL_LOG_ERR, "No JWKS configured");
		return SASL_CONFIGERR;
	}

	gctx->jwks = oauth_get_jwks(gctx, NULL);
	if (!gctx->jwks) {
		utils->log(NULL, SASL_LOG_ERR, "Error in oauth_get_jwks");
		return SASL_CONFIGERR;
	}

	return SASL_OK;
}


static int oauth_client_mech_new(
	void *glob_context,
	sasl_client_params_t *params,
	void **conn_context
) {
	oauth_client_context *text;

	if ((text = params->utils->malloc(sizeof(*text))) == NULL) {
		params->utils->seterror(params->utils->conn, 0, "cannot allocate client context");
		return SASL_NOMEM;
	}

	memset(text, 0, sizeof(*text));
	*conn_context = text;

	return SASL_OK;
}

static int oauth_client_mech_step(
	void *conn_context,
	sasl_client_params_t *params,
	const char *serverin,
	unsigned serverinlen,
	sasl_interact_t **prompt_need,
	const char **clientout,
	unsigned *clientoutlen,
	sasl_out_params_t *oparams
) {
	oauth_client_context *text = (oauth_client_context *)conn_context;
	sasl_secret_t *pass = NULL;
	unsigned int free_pass = 0;
	int user_result = SASL_OK;
	int pass_result = SASL_OK;
	int result;
	const char *authzid = NULL;
	char *freeme = NULL;
	char *encoded_authorization_id = NULL;

	/* Sanity checks */
	if ((params == NULL) ||
		(params->utils == NULL) ||
		(params->utils->conn == NULL) ||
		(params->utils->getcallback == NULL) ||
		(clientout == NULL) ||
		(clientoutlen == NULL) ||
		(oparams == NULL)) {
		params->utils->seterror(params->utils->conn, 0, "Bad parameters");
		return SASL_BADPARAM;
	}

	/* Limit */
	if (serverinlen > MAX_SERVERIN_LEN) {
		params->utils->seterror(params->utils->conn, 0, "server data too big (%d)", serverinlen);
		return SASL_BADPROT;
	}

	if (serverinlen != 0) {
		// client step 2
		// RFC 7628: 3.2.2 Server Response to Failed Authentication

		/*
		json_error_t json_error;
		json_t *j_response = json_loads(serverin, 0, &json_error);
		if (!j_response) {
			params->utils->seterror(params->utils->conn, 0, "Failed parsing json error message (%s)", json_error.text);
			return SASL_BADPROT;
		}

		char *status = NULL;
		char *scope = NULL;
		char *openid_configuration = NULL;
		if(json_unpack_ex(j_response, &json_error, 0, "{ss s?s s?s!}", "status", &status, "scope", &scope, "openid-configuration", &openid_configuration)) {
			params->utils->seterror(params->utils->conn, 0, "Failed unpacking json error message (%s)", json_error.text);
			return SASL_BADPROT;
		}
		json_decref(j_response);
		*/

		params->utils->seterror(params->utils->conn, 0, "Authentication failed (%s)", serverin);
		// return SASL_BADPROT;

		// RFC 7628: 3.2.3 Completing an Error Message Sequence
		*clientoutlen = 1;
		result = _plug_buf_alloc(params->utils, &(text->clientout_buf), &(text->clientout_buf_size), *clientoutlen + 1);
		// params->utils->encode64
		strcpy(text->clientout_buf, "\1");
		*clientout = text->clientout_buf;

		result = SASL_OK;
		goto doneout;
	}

	*clientout = NULL;
	*clientoutlen = 0;

	if (params->props.min_ssf > params->external_ssf) {
		params->utils->seterror(params->utils->conn, 0, "SSF too weak for sasl_oauthbearer plugin");
		return SASL_TOOWEAK;
	}

	/* Try to get authzid -- currently not used, as RFC 7628 communicates this via gs2-header
	 * Note: The authzid format should be either "dn:<userdn>" or "u:uid",
	 *       where the latter will be mapped by slapd using authz-regexp
	 */
	user_result = _plug_get_simple(params->utils, SASL_CB_USER, 0, &authzid, prompt_need);
	if ((user_result != SASL_OK) && (user_result != SASL_INTERACT))
		return user_result;

	/* Try to get oauthbearer message containing JWT */
	pass_result = _plug_get_password(params->utils, &pass, &free_pass, prompt_need);
	if ((pass_result != SASL_OK) && (pass_result != SASL_INTERACT))
		return user_result;

	/* free prompts we got */
	if (prompt_need && *prompt_need) {
		params->utils->free(*prompt_need);
		*prompt_need = NULL;
	}

	if ((user_result == SASL_INTERACT) || (pass_result == SASL_INTERACT)) {
		/* make the prompt list */
		result = _plug_make_prompts(params->utils, prompt_need,
			user_result == SASL_INTERACT ?  "Please enter an authorization name" : NULL,
			NULL, NULL, NULL,
			pass_result == SASL_INTERACT ?  "Please enter Access Token (as JWT)" : NULL,
			NULL, NULL, NULL, NULL, NULL, NULL, NULL);

		if (result != SASL_OK)
			goto out;

		return SASL_INTERACT;
	}

	/* Placeholder for later */
	if ((result = params->canon_user(params->utils->conn, "anonymous", 0, SASL_CU_AUTHID, oparams)) != SASL_OK)
		goto out;

	if (authzid != NULL && *authzid != '\0') {
		result = params->canon_user(params->utils->conn, authzid, 0, SASL_CU_AUTHZID, oparams);
	} else {
		result = params->canon_user(params->utils->conn, "anonymous", 0, SASL_CU_AUTHZID, oparams);
	}

	if (result != SASL_OK)
		goto out;

	if (pass == NULL) {
		params->utils->seterror(params->utils->conn, 0, "Bad parameter (no Access Token)");
		return SASL_BADPARAM;
	}

	if (authzid != NULL && *authzid != '\0') {
		result = encode_saslname(oparams->user, (const char **) &encoded_authorization_id, &freeme);
		if (result != SASL_OK) {
			goto out;
		}
	}

	unsigned int rfc7628_msg_len = 18 + ((encoded_authorization_id != NULL) ? 2 + strlen(encoded_authorization_id) : 0) + pass->len;

	// result = _plug_buf_alloc(params->utils, &rfc7628_msg, &rfc7628_msg_size, rfc7628_msg_len + 1);
	result = _plug_buf_alloc(params->utils, &(text->clientout_buf), &(text->clientout_buf_size), rfc7628_msg_len + 1);
	if (result != SASL_OK) {
		goto out;
	}
	if (authzid != NULL && *authzid != '\0') {
		snprintf(text->clientout_buf, text->clientout_buf_size, "n,a=%s,\1auth=Bearer %s\1\1", encoded_authorization_id, pass->data);
	} else {
		snprintf(text->clientout_buf, text->clientout_buf_size, "n,,\1auth=Bearer %s\1\1", pass->data);
	}

	*clientout = text->clientout_buf;
	*clientoutlen = text->clientout_buf_size - 1;

	result = SASL_CONTINUE;
	goto out;

doneout:
	/* set oparams */
	oparams->doneflag = 1;
	oparams->mech_ssf = 0;
	oparams->maxoutbuf = 0;
	oparams->encode_context = NULL;
	oparams->encode = NULL;
	oparams->decode_context = NULL;
	oparams->decode = NULL;
	oparams->param_version = 0;
out:
	if (free_pass)
		_plug_free_secret(params->utils, &pass);
	if (freeme != NULL)
		_plug_free_string(params->utils, &freeme);

	return result;
}

static void oauth_client_mech_dispose(
	void *conn_context,
	const sasl_utils_t *utils
) {
	oauth_client_context *text = (oauth_client_context *)conn_context;

	if (text == NULL)
		return;

	if (text->clientout_buf != NULL)
		utils->free(text->clientout_buf);
	utils->free(text);
}

static sasl_client_plug_t oauth_client_plugin = {
	"OAUTHBEARER", /* mech_name */
	0, /* max_ssf */
	SASL_SEC_NOANONYMOUS, /* security_flags */
	SASL_FEAT_WANT_CLIENT_FIRST | SASL_FEAT_ALLOWS_PROXY, /* features */
	NULL, /* required_prompts */
	NULL, /* glob_context */
	&oauth_client_mech_new, /* mech_new */
	&oauth_client_mech_step, /* mech_step */
	&oauth_client_mech_dispose,/* mech_dispose */
	NULL, /* mech_free */
	NULL, /* idle */
	NULL, /* spare */
	NULL /* spare */
};

int sasl_client_plug_init(
	const sasl_utils_t *utils,
	int maxvers,
	int *outvers,
	sasl_client_plug_t **pluglist,
	int *plugcount
) {
	if (maxvers < SASL_CLIENT_PLUG_VERSION) {
		utils->log(NULL, SASL_LOG_ERR, "OAUTHBEARER version mismatch");
		return SASL_BADVERS;
	}

	*outvers = SASL_CLIENT_PLUG_VERSION;
	*pluglist = &oauth_client_plugin;
	*plugcount = 1;

	return SASL_OK;
}
