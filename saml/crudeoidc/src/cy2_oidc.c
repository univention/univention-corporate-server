/* $Id: cy2_saml.c,v 1.12 2017/05/24 22:47:15 manu Exp $ */

/*
 * Copyright (c) 2009,2011 Emmanuel Dreyfus
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
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <syslog.h>
#include <stdarg.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/queue.h>

#include <sasl/sasl.h>
#include <sasl/saslplug.h>
#include <sasl/saslutil.h>

#include "oidc.h"

#include "plugin_common.h"


typedef struct {
	char *out;
	unsigned int len;
} oidc_client_context;

static oidc_glob_context_t server_glob_context;

void oidc_log(
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

void oidc_error(
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

int oidc_strdup(
	const void *utils,
	const char *src,
	char **dst,
	int *len
) {
	sasl_utils_t *sasl_utils;

	sasl_utils = (sasl_utils_t *)utils;
	return _plug_strdup(sasl_utils, src, dst, len);
}

int oidc_retcode(
	int code
) {
	int retcode;

	switch(code) {
	case 0:
		retcode = SASL_OK;
		break;
	case EINVAL:
		retcode = SASL_BADPARAM;
		break;
	case EACCES:
		retcode = SASL_BADAUTH;
		break;
	case ENOMEM:
	default:
		retcode = SASL_FAIL;
		break;
	}

	return retcode;
}

static int oidc_server_mech_new(
	void *glob_context,
	sasl_server_params_t *params,
	const char *challenge,
	unsigned int challen,
	void **conn_context
) {
	oidc_serv_context_t *ctx;

	if (conn_context == NULL) {
		params->utils->seterror(params->utils->conn, 0, "NULL conn_context");
		return SASL_BADPARAM;
	}

	if ((ctx = params->utils->malloc(sizeof(*ctx))) == NULL) {
		params->utils->seterror(params->utils->conn, 0, "out of memory");
		return SASL_NOMEM;
	}

	ctx->glob_context = glob_context;
	ctx->userid = NULL;
	*conn_context = ctx;

	return SASL_OK;
}

static int oidc_server_mech_step(
	void *conn_context,
	sasl_server_params_t *params,
	const char *clientin,
	unsigned int clientinlen,
	const char **serverout,
	unsigned int *serveroutlen,
	sasl_out_params_t *oparams
) {
	oidc_serv_context_t *ctx = (oidc_serv_context_t *)conn_context;
	oidc_glob_context_t *gctx;
	const char *authen;
	const char *userid;
	const char *oidc_msg_ptr;
	char *jwt_msg = NULL;
	unsigned int oidc_len;
	unsigned int lup = 0;
	int flags;
	int error;

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

	gctx = ctx->glob_context;

	/* Limit */
	if (clientinlen > 65536) {
		params->utils->seterror(params->utils->conn, 0, "client data too big (%d)", clientinlen);
		return SASL_BADPROT;
	}

	*serverout = NULL;
	*serveroutlen = 0;

	authen = clientin;
	while ((lup < clientinlen) && (clientin[lup] != 0)) ++lup;
	if (lup >= clientinlen) {
		params->utils->seterror(params->utils->conn, 0, "Found only authen");
		return SASL_BADPROT;
	}

	lup++;
	oidc_msg_ptr = clientin + lup;
	while ((lup < clientinlen) && (clientin[lup] != 0)) ++lup;
	oidc_len = (unsigned int)(clientin + lup - oidc_msg_ptr);
	if (lup != clientinlen) {
		params->utils->seterror(params->utils->conn, 0, "Unexpected data (%d vs %d)", lup, clientinlen);
		return SASL_BADPROT;
	}

	/*
	 * Make sure it is NULL-terminated
	 */
	if ((jwt_msg = params->utils->malloc(oidc_len + 1)) == NULL) {
		params->utils->seterror(params->utils->conn, 0, "Out of memory (%d bytes)", oidc_len + 1);
		return SASL_NOMEM;
	}
	memcpy(jwt_msg, oidc_msg_ptr, oidc_len);
	jwt_msg[oidc_len] = '\0';

	/*
	 * Validate JWT signature, retreive authid
	 */
	flags = 0;  // (gctx->flags & SGC_COMPRESSED_ASSERTION) ? MAYBE_COMPRESS : 0;
	if ((error = oidc_check_jwt(ctx, params->utils, &userid, jwt_msg, flags)) != SASL_OK) {
		params->utils->seterror(params->utils->conn, 0, "oidc_check_jwt (error=%d)", error);
		goto out;
	}
	if (userid == NULL) {
		params->utils->seterror(params->utils->conn, 0, "No userid found");
		error = SASL_NOAUTHZ;
		goto out;
	}

	/* Canonicalize Userid if we have one */
	if ((authen != NULL) && (*authen != '\0')) {
		if ((error = params->canon_user(params->utils->conn, authen, 0, SASL_CU_AUTHZID, oparams)) != SASL_OK) {
			params->utils->seterror(params->utils->conn, 0, "canon_user faild for authen (error=%d)", error);
			goto out;
		}
		if ((error = params->canon_user(params->utils->conn, userid, 0, SASL_CU_AUTHID, oparams)) != SASL_OK) {
			params->utils->seterror(params->utils->conn, 0, "canon_user faild for userid (error=%d)", error);
			goto out;
		}
	} else {
		if ((error = params->canon_user(params->utils->conn, userid, 0, SASL_CU_AUTHID|SASL_CU_AUTHZID, oparams)) != SASL_OK) {
			params->utils->seterror(params->utils->conn, 0, "canon_user faild for userid (both) (error=%d)", error);
			goto out;
		}
	}

	oparams->doneflag = 1;
	oparams->mech_ssf = 0;
	oparams->maxoutbuf = 0;
	oparams->encode_context = NULL;
	oparams->encode = NULL;
	oparams->decode_context = NULL;
	oparams->decode = NULL;
	oparams->param_version = 0;

out:
	if (jwt_msg != NULL) {
		params->utils->erasebuffer(jwt_msg, strlen(jwt_msg));
		params->utils->free(jwt_msg);
		return error;
	}

	return SASL_OK;
}

static void oidc_server_mech_dispose(
	void *conn_context,
	const sasl_utils_t *utils
) {
	oidc_serv_context_t *ctx = (oidc_serv_context_t *)conn_context;

	if (ctx != NULL) {
		if (ctx->userid != NULL)
			utils->free(ctx->userid);

		utils->free(ctx);
	}

	return;
}

static void oidc_server_mech_free(
	void *glob_context,
	const sasl_utils_t *utils
) {
	struct oidc_trusted_rp *item;
	oidc_glob_context_t *gctx;

	gctx = (oidc_glob_context_t *)glob_context;

	/*
	 * Do not free gctx->uid_attr, it is static
	 */

	while ((item = SLIST_FIRST(&gctx->trusted_rp)) != NULL) {
		SLIST_REMOVE_HEAD(&gctx->trusted_rp, next);
		free(item);
	}

	/* TODO: shutdown jwt lib?  */

	/*
	 * Do not free (oidc_glob_context_t *)glob_context, it is static!
	 */
}


static sasl_server_plug_t oidc_server_plugin = {
	"OIDC",  /* mech_name */
	0,  /* max_ssf */
	SASL_SEC_NOANONYMOUS,  /* security_flags */
	SASL_FEAT_WANT_CLIENT_FIRST | SASL_FEAT_ALLOWS_PROXY, /* features */
	&server_glob_context,  /* glob_context */
	&oidc_server_mech_new,  /* mech_new */
	&oidc_server_mech_step,  /* mech_step */
	&oidc_server_mech_dispose,  /* mech_dispose */
	&oidc_server_mech_free,  /* mech_free */
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
	oidc_glob_context_t *gctx;
	const char *grace;
	char propname[1024];
	int propnum = 0;
	FILE *jwks_fp;

	if (maxvers < SASL_SERVER_PLUG_VERSION) {
		utils->seterror(utils->conn, 0, "OIDC version mismatch");
		return SASL_BADVERS;
	}

	*outvers = SASL_SERVER_PLUG_VERSION;
	*pluglist = &oidc_server_plugin;
	*plugcount = 1;

	/* TODO: init jwt library? */

	gctx = (oidc_glob_context_t *)oidc_server_plugin.glob_context;

	gctx->flags = 0;

	/*
	 * Attribute to be used for userid
	if (((utils->getopt(utils->getopt_context, "OIDC", "oidc_userid", &gctx->uid_attr, NULL)) != 0) || (gctx->uid_attr == NULL) || (*gctx->uid_attr == '\0'))
		gctx->uid_attr = "uid";
	 */

	/*
	 * Grace delay for clock skews
	 */
	if (((utils->getopt(utils->getopt_context, "OIDC", "oidc_grace", &grace, NULL)) != 0) || (grace == NULL) || (*grace == '\0'))
		gctx->grace = (time_t)600;
	else
		gctx->grace = atoi(grace);

	/*
	 * Load the trusted rp names
	 */
	propnum = 0;
	SLIST_INIT(&gctx->trusted_rp);
	do {
		const char *trusted_rp;
		struct oidc_trusted_rp *item;

		(void)snprintf(propname, sizeof(propname), "oidc_trusted_rp%d", propnum);
		propnum++;

		if (utils->getopt(utils->getopt_context, "OIDC", propname, &trusted_rp, NULL) != 0)
			break;

		if ((item = utils->malloc(sizeof(*item))) == NULL) {
			utils->seterror(utils->conn, 0, "cannot allocate memory");
			return SASL_NOMEM;
		}

		item->name = trusted_rp;
		SLIST_INSERT_HEAD(&gctx->trusted_rp, item, next);
	} while (1 /*CONSTCOND*/);

	/* 
	 * Load the trusted iss names
	 */
	propnum = 0;
	do {
		if (propnum > 0)  // TODO: support multiple issuers
			break;

		(void)snprintf(propname, sizeof(propname), 
			       "oidc_trusted_iss%d", propnum);
		propnum++;
	
		if (utils->getopt(utils->getopt_context, "OIDC", 
				  propname, &gctx->trusted_iss, NULL) != 0) 
			break;
		
		if ((gctx->trusted_iss == NULL) || (*gctx->trusted_iss == '\0')) {
			utils->log(NULL, SASL_LOG_ERR,
				   "Unable to get issuer from \"%s\"",
				   propname); 
			continue;
		}
	} while (1 /*CONSTCOND*/);

	/* 
	 * Load the JWKS file
	 */
	propnum = 0;
	do {
		const char *jwks_filename;

		if (propnum > 0)  // TODO: support multiple issuers
			break;

		(void)snprintf(propname, sizeof(propname), 
			       "oidc_trusted_jwks%d", propnum);
		propnum++;
	
		if (utils->getopt(utils->getopt_context, "OIDC", 
				  propname, &jwks_filename, NULL) != 0) 
			break;
		
		if ((jwks_filename == NULL) || (*jwks_filename == '\0'))
			continue;

		if (access(jwks_filename, R_OK) != 0) {
			utils->log(NULL, SASL_LOG_ERR,
				   "Unable to read Issuer JWKS file \"%s\"",
				   jwks_filename); 
			continue;
		}

		if ((gctx->trusted_jwks_str = utils->malloc(JWKS_BUFFSIZE)) == NULL) {
			utils->seterror(utils->conn, 0, "cannot allocate memory");
			return SASL_NOMEM;
		}

		jwks_fp = fopen(jwks_filename, "r");
		fgets(gctx->trusted_jwks_str, JWKS_BUFFSIZE, jwks_fp); //TODO: Error handling
		fclose(jwks_fp);

		if (!gctx->trusted_jwks_str) {
			utils->log(NULL, SASL_LOG_ERR,
				   "Failed to load JWKS from \"%s\"", jwks_filename);
			continue;
		}

		utils->log(NULL, SASL_LOG_NOTE, 
			   "Loaded JWKS from \"%s\"", jwks_filename);
	} while (1 /*CONSTCOND*/);

	return SASL_OK;
}


static int oidc_client_mech_new(
	void *glob_context,
	sasl_client_params_t *params,
	void **conn_context
) {
	oidc_client_context *text;

	if ((text = params->utils->malloc(sizeof(*text))) == NULL) {
		params->utils->seterror(params->utils->conn, 0, "cannot allocate client context");
		return SASL_NOMEM;
	}

	memset(text, 0, sizeof(*text));
	*conn_context = text;

	return SASL_OK;
}

static int oidc_client_mech_step(
	void *conn_context,
	sasl_client_params_t *params,
	const char *serverin,
	unsigned serverinlen,
	sasl_interact_t **prompt_need,
	const char **clientout,
	unsigned *clientoutlen,
	sasl_out_params_t *oparams
) {
	oidc_client_context *text = (oidc_client_context *)conn_context;
	const char *user = NULL;
	sasl_secret_t *jwt_msg = NULL;
	unsigned int free_jwt_msg = 0;
	int user_result = SASL_OK;
	int pass_result = SASL_OK;
	int result;
	char *cp;

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

	if (serverinlen != 0) {
		params->utils->seterror(params->utils->conn, 0, "Bad protocol");
		return SASL_BADPROT;
	}

	*clientout = NULL;
	*clientoutlen = 0;

	if (params->props.min_ssf > params->external_ssf) {
		params->utils->seterror(params->utils->conn, 0, "SSF too weak for OIDC plugin");
		return SASL_TOOWEAK;
	}

	/* Try to get user */
	user_result = _plug_get_simple(params->utils, SASL_CB_USER, 0, &user, prompt_need);
	if ((user_result != SASL_OK) && (user_result != SASL_INTERACT))
		return user_result;

	/* Try to get JWT */
	pass_result = _plug_get_password(params->utils, &jwt_msg, &free_jwt_msg, prompt_need);
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
			user_result == SASL_INTERACT ?  "Please enter your authorization name" : NULL,
			NULL, NULL, NULL,
			pass_result == SASL_INTERACT ?  "Please enter JWT" : NULL,
			NULL, NULL, NULL, NULL, NULL, NULL, NULL);

		if (result != SASL_OK)
			goto out;

		return SASL_INTERACT;
	}

	if (jwt_msg == NULL) {
		params->utils->seterror(params->utils->conn, 0, "Bad parameter (no JWT)");
		return SASL_BADPARAM;
	}

	/* Placeholder for later */
	if ((result = params->canon_user(params->utils->conn, "anonymous", 0, SASL_CU_AUTHID, oparams)) != SASL_OK)
		goto out;

	if (user != NULL && *user != '\0') {
		result = params->canon_user(params->utils->conn, user, 0, SASL_CU_AUTHZID, oparams);
	} else {
		result = params->canon_user(params->utils->conn, "anonymous", 0, SASL_CU_AUTHZID, oparams);
	}

	if (result != SASL_OK)
		goto out;

	/* send authorized id NUL password */
	*clientoutlen = ((user && *user ? strlen(user) : 0) + 1 + jwt_msg->len);

	/* remember the extra NUL on the end for stupid clients */
	result = _plug_buf_alloc(params->utils, &(text->out), &(text->len), *clientoutlen + 1);
	if (result != SASL_OK)
		goto out;

	memset(text->out, 0, *clientoutlen + 1);
	cp = text->out;
	if (user != NULL && *user != '\0') {
		size_t len;

		len = strlen(user);
		memcpy(cp, user, len);
		cp += len;
	}
	memcpy(++cp, jwt_msg->data, jwt_msg->len);

	*clientout = text->out;

	/* set oparams */
	oparams->doneflag = 1;
	oparams->mech_ssf = 0;
	oparams->maxoutbuf = 0;
	oparams->encode_context = NULL;
	oparams->encode = NULL;
	oparams->decode_context = NULL;
	oparams->decode = NULL;
	oparams->param_version = 0;

	result = SASL_OK;
out:
	if (free_jwt_msg)
		_plug_free_secret(params->utils, &jwt_msg);

	return result;
}

static void oidc_client_mech_dispose(
	void *conn_context,
	const sasl_utils_t *utils
) {
	oidc_client_context *text = (oidc_client_context *)conn_context;

	if (text == NULL)
		return;

	if (text->out != NULL)
		utils->free(text->out);
	utils->free(text);
}

static sasl_client_plug_t oidc_client_plugin = {
	"OIDC", /* mech_name */
	0, /* max_ssf */
	SASL_SEC_NOANONYMOUS, /* security_flags */
	SASL_FEAT_WANT_CLIENT_FIRST | SASL_FEAT_ALLOWS_PROXY, /* features */
	NULL, /* required_prompts */
	NULL, /* glob_context */
	&oidc_client_mech_new, /* mech_new */
	&oidc_client_mech_step, /* mech_step */
	&oidc_client_mech_dispose,/* mech_dispose */
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
		utils->seterror(utils->conn, 0, "OIDC version mismatch");
		return SASL_BADVERS;
	}

	*outvers = SASL_CLIENT_PLUG_VERSION;
	*pluglist = &oidc_client_plugin;
	*plugcount = 1;

	return SASL_OK;
}
