/*
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2022-2024 Univention GmbH
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
#include "config.h"

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <errno.h>
#include <stdarg.h>
#include <stdlib.h>
#include <ctype.h>
#include <syslog.h>
#include <errno.h>
//#include <zlib.h>
#include <sys/stat.h>
#include <sys/queue.h>
#include <time.h>

#include "oauthbearer.h"

#include <rhonabwy.h>

#define AUTOPTR_FUNC_NAME(type) type##AutoPtrFree
#define DEFINE_AUTOPTR_FUNC(type, func) \
  static inline void AUTOPTR_FUNC_NAME(type)(type **_ptr) \
  { \
    if (*_ptr) \
      (func)(*_ptr); \
    *_ptr = NULL; \
  }
#define AUTOPTR(type) \
  __attribute__((cleanup(AUTOPTR_FUNC_NAME(type)))) type *
DEFINE_AUTOPTR_FUNC(char, r_free);
DEFINE_AUTOPTR_FUNC(jwks_t, r_jwks_free);
DEFINE_AUTOPTR_FUNC(jwk_t, r_jwk_free);
DEFINE_AUTOPTR_FUNC(jwt_t, r_jwt_free);


#ifdef HACK
/* Helper functions copied from pam_oauthbearer.c for compiling oauthbearer.c with -DHACK */
void oauth_log(
	const void *utils,
	int pri,
	const char *fmt,
	...
) {
	va_list ap;

	va_start(ap, fmt);
	vsyslog(pri, fmt, ap);
	va_end(ap);
}

void oauth_error(
	const void *utils,
	int pri,
	const char *fmt,
	...
) {
	va_list ap;

	if (pri == 0)
		pri = LOG_ERR;

	va_start(ap, fmt);
	vsyslog(pri, fmt, ap);
	va_end(ap);
}

int oauth_strdup(
	const void *utils,
	const char *src,
	char **dst,
	int *len
) {
	*dst = strdup(src);
	if (*dst == NULL)
		return -1;

	if (len != NULL)
		*len = strlen(*dst);

	return 0;
}
#endif /*HACK*/

const char* oauth_enum_error_string(enum OAuthError code) {
	switch(code) {
		case OK:
			return "";
		case MISSING_UID_CLAIM:
			return "The claim for the username is missing.";
		case PARSE_ERROR:
			return "There was an error parsing the JWT.";
		case INVALID_ISSUER:
			return "The issuer is not given or invalid.";
		case INVALID_AUDIENCE:
			return "The audience is not given or invalid.";
		case MISSING_SCOPE:
			return "A required scope is not given.";
		case INVALID_AUTHORIZED_PARTY:
			return "The authorized party is not given or invalid.";
		case CLAIM_EXPIRED:
			return "The claim is expired (or not yet valid).";
		case INVALID_SIGNATURE:
			return "The signature is wrong.";
		case UNKNOWN_SIGNING_KEY:
			return "The signing key is unknown.";
		case CONFIG_ERROR:
			return "The JWK could not be loaded.";
		default:
			return "";
	}
}

enum OAuthError oauth_check_token_issuer(
	oauth_serv_context_t *ctx,
	const void *utils,
	jwt_t *jwt
) {
	if (r_jwt_validate_claims(jwt, R_JWT_CLAIM_ISS, ctx->glob_context->trusted_iss, R_JWT_CLAIM_NOP) == RHN_OK)
		return OK;
	oauth_error(utils, 0, "invalid or not given issuer: %s", r_jwt_get_claim_str_value(jwt, "iss"));
	return INVALID_ISSUER;
}

enum OAuthError oauth_check_token_audience(
	oauth_serv_context_t *ctx,
	const void *utils,
	jwt_t *jwt
) {
	enum OAuthError ret = OK;
	struct oauth_list *rp;

	SLIST_FOREACH(rp, &ctx->glob_context->trusted_aud, next) {
		if (r_jwt_validate_claims(jwt, R_JWT_CLAIM_AUD, rp->name, R_JWT_CLAIM_NOP) == RHN_OK)
			return OK;
		ret = INVALID_AUDIENCE;
	}

	if (ret != OK) oauth_error(utils, 0, "invalid or not given audience: %s", r_jwt_get_claim_str_value(jwt, "aud"));
	return ret;
}

enum OAuthError oidc_check_token_authorized_party(
	oauth_serv_context_t *ctx,
	const void *utils,
	jwt_t *jwt
) {
	enum OAuthError ret = OK;
	struct oauth_list *rp;

	if (r_jwt_validate_claims(jwt, R_JWT_CLAIM_STR, "azp", NULL, R_JWT_CLAIM_NOP) != RHN_OK)
		return OK;

	SLIST_FOREACH(rp, &ctx->glob_context->trusted_azp, next) {
		if (r_jwt_validate_claims(jwt, R_JWT_CLAIM_STR, "azp", rp->name, R_JWT_CLAIM_NOP) == RHN_OK)
			return OK;
		ret = INVALID_AUTHORIZED_PARTY;
	}
	if (ret != OK) oauth_error(utils, 0, "token contains no or invalid azp: %s", r_jwt_get_claim_str_value(jwt, "azp"));
	return ret;
}

enum OAuthError oauth_check_token_validity_dates(
	oauth_serv_context_t *ctx,
	const void *utils,
	jwt_t *jwt
) {
	time_t now = time(NULL);
	time_t grace = ctx->glob_context->grace;

	if (r_jwt_validate_claims(jwt, R_JWT_CLAIM_NBF, R_JWT_CLAIM_PRESENT, R_JWT_CLAIM_NOP) == RHN_OK && r_jwt_validate_claims(jwt, R_JWT_CLAIM_NBF, (int)now + grace, R_JWT_CLAIM_NOP) != RHN_OK)
		goto err;
	if (r_jwt_validate_claims(jwt, R_JWT_CLAIM_IAT, R_JWT_CLAIM_PRESENT, R_JWT_CLAIM_NOP) == RHN_OK && r_jwt_validate_claims(jwt, R_JWT_CLAIM_IAT, (int)now + grace, R_JWT_CLAIM_NOP) != RHN_OK)
		goto err;
	if (r_jwt_validate_claims(jwt, R_JWT_CLAIM_EXP, R_JWT_CLAIM_PRESENT, R_JWT_CLAIM_NOP) == RHN_OK && r_jwt_validate_claims(jwt, R_JWT_CLAIM_EXP, (int)now - grace, R_JWT_CLAIM_NOP) != RHN_OK)
		goto err;

	return OK;

err:
	oauth_error(utils, 0, "claim expired or not yet valid: now=%d exp=%d nbf=%d iat=%d", (int)now, r_jwt_get_claim_int_value(jwt, "exp"), r_jwt_get_claim_int_value(jwt, "nbf"), r_jwt_get_claim_int_value(jwt, "iat"));
	return CLAIM_EXPIRED;
}

enum OAuthError oauth_check_required_scopes(
	oauth_serv_context_t *ctx,
	const void *utils,
	jwt_t *jwt
) {
	struct oauth_list *scope;

	SLIST_FOREACH(scope, &ctx->glob_context->required_scope, next) {
		if (r_jwt_validate_claims(jwt, R_JWT_CLAIM_STR, "scope", scope->name, R_JWT_CLAIM_NOP) != RHN_OK)
			return MISSING_SCOPE;
	}
	return OK;
}

enum OAuthError oauth_check_token_uid(
	oauth_serv_context_t *ctx,
	const void *utils,
	jwt_t *jwt
) {
	const char *preferred_username = r_jwt_get_claim_str_value(jwt, ctx->glob_context->uid_attr);
	if ((preferred_username != NULL) && (*preferred_username != '\0')) {
		if (oauth_strdup(utils, preferred_username, &ctx->authcid, NULL) != 0) {
			return CONFIG_ERROR;
		}
		return OK;
	}
	oauth_error(utils, 0, "token contains no %s", ctx->glob_context->uid_attr);
	return MISSING_UID_CLAIM;
}


jwk_t * oauth_get_jwk_for_jwt(
	oauth_glob_context_t *gctx,
	const void *utils,
	jwt_t *jwt
) {
	const char *kid;
	jwk_t *jwk;

	if ((kid = r_jwt_get_sig_kid(jwt)) == NULL) {
		oauth_error(utils, 0, "Error in r_jwt_get_sig_kid");
		goto out;
	}

	jwk = r_jwks_get_by_kid(gctx->jwks, kid);
	if (!jwk) {
		oauth_error(utils, 0, "Could not get kid %s from JWKS", kid);
		goto out;
	}

	return jwk;

out:
	return NULL;
}


enum OAuthError oauth_check_jwt_signature(
	oauth_serv_context_t *ctx,
	const void *utils,
	jwt_t *jwt
) {
	AUTOPTR(char) claims = NULL;
	AUTOPTR(jwk_t) jwk = NULL;

	jwk = oauth_get_jwk_for_jwt(ctx->glob_context, utils, jwt);
	if (!jwk) {
		return UNKNOWN_SIGNING_KEY;
	}

	if (r_jwt_verify_signature(jwt, jwk, 0) != RHN_OK) {
		oauth_error(utils, 0, "Error in r_jwt_verify_signature");
		return INVALID_SIGNATURE;
	}

	claims = r_jwt_get_full_claims_str(jwt);
	oauth_log(utils, LOG_DEBUG, "Verified payload:\n%s\n", claims);
	return OK;
}


jwks_t * oauth_get_jwks(
	oauth_glob_context_t *gctx,
	const void *utils
) {
	jwks_t *jwks;

	if (r_jwks_init(&jwks) != RHN_OK) {
		oauth_error(utils, 0, "Error in r_jwks_init");
		goto out;
	}

	if (r_jwks_import_from_json_str(jwks, gctx->trusted_jwks_str) != RHN_OK) {
		oauth_error(utils, 0, "Error in r_jwks_import_from_str");
		goto out;
	}

	for (int i=0; i<r_jwks_size(jwks); i++) {
		jwk_t *jwk = r_jwks_get_at(jwks, i);
		if(r_jwk_is_valid(jwk) != RHN_OK) {
			oauth_error(utils, 0, "Error: JWK is not valid");
			r_jwk_free(jwk);
			goto out;
		}

		/*
		int rc;
		unsigned char *output;
		size_t output_len = JWKS_BUFFSIZE;

		output = malloc(output_len);
		rc = r_jwk_export_to_pem_der(jwk, R_FORMAT_PEM, output, &output_len, 0);
		if (rc == RHN_ERROR_PARAM) {
			output = realloc(output, output_len);
			rc = r_jwk_export_to_pem_der(jwk, R_FORMAT_PEM, output, &output_len, 0);
		}

		if (rc != RHN_OK) {
			oauth_error(utils, 0, "Error in r_jwk_export_to_pem_der");
			free(output);
			goto out;
		}
		oauth_log(utils, LOG_DEBUG, "Exported key:\n%.*s\n", (int)output_len, output);
		free(output);
		*/
		r_jwk_free(jwk);
	}

	return jwks;

out:
	return NULL;
}


enum OAuthError oauth_check_jwt(
	oauth_serv_context_t *ctx,
	const void *utils,
	const char **oauth_user,
	char *msg
) {
	unsigned int msg_len;
	enum OAuthError error = PARSE_ERROR;
	AUTOPTR(jwt_t) jwt = NULL;

	if (msg == NULL) {
		oauth_error(utils, 0, "No token");
		return PARSE_ERROR;
	}

	/*
	 * The message must be long enough to hold an JWT
	 */
	msg_len = strlen(msg);
	if (msg_len < JWT_MINLEN) {
		oauth_error(utils, 0, "Token too short");
		return PARSE_ERROR;
	}

	// parse the token
	if (r_jwt_init(&jwt) != RHN_OK) {
		oauth_error(utils, 0, "Error in r_jwt_init");
		return CONFIG_ERROR;
	}

	if (r_jwt_parse(jwt, msg, 0) != RHN_OK) {
		oauth_error(utils, 0, "Error in r_jwt_parse");
		return PARSE_ERROR;
	}

	if ((error = oauth_check_jwt_signature(ctx, utils, jwt)) != OK)
		return error;
	if ((error = oauth_check_token_issuer(ctx, utils, jwt)) != OK)
		return error;
	if ((error = oauth_check_token_audience(ctx, utils, jwt)) != OK)
		return error;
	if ((error = oidc_check_token_authorized_party(ctx, utils, jwt)) != OK)
		return error;
	if ((error = oauth_check_token_validity_dates(ctx, utils, jwt)) != OK)
		return error;
	if ((error = oauth_check_required_scopes(ctx, utils, jwt)) != OK)
		return error;
	if ((error = oauth_check_token_uid(ctx, utils, jwt)) != OK)
		return error;

	*oauth_user = ctx->authcid;
	return error;
}

#ifdef HACK
/* To compile with gcc oauthbearer.c -lrhonabwy -lsasl2 -lorcania -lyder -ljansson -DHACK */

// curl https://ucs-sso-ng.$(hostname -d)/realms/master/protocol/openid-connect/certs | python -c 'import json, sys; print(json.dumps(json.load(sys.stdin)["keys"][0]))'
// static const char jwk_str[] = ...;

static const char test_jwks_str[] =
"{\"keys\":[{\"x5t\": \"3KS_qYX91eZwWSvaZXC_xnEhFpA\", \"x5t#S256\": \"sBb9vJ-tMYVbx1Xjk3Mb_6FCfHHPCy1Jeq3b-VYVuKs\", \"use\": \"enc\", \"e\": \"AQAB\", \"kty\": \"RSA\", \"alg\": \"RSA-OAEP\", \"n\": \"ttCYcHQrVpQg-PPSdCOnFAsxjDFsR3NLlexuuKdbHDAT2vRrgCmn6PJpC9UDwSW38HOzwyYGBb7yy1sfZl8a3XnHEmwCTkGTf80VfgRbM6dn-ZVNL-4_XlXznz1Z9yp5ZhGKBq2jFVCIE_x9VhpeVbUft3bDjcw_D5xtZdFpPTBT7fSbATC8IsxwClLkg-_S41bFMRRpgQ1dJM5OZeSN3Rnj40aj-yrk7QYLDlGYtnMOAITThY0qZmf90Lnp5CInMmVoKw0RqPPMZuHitboNShvUTN_1NoMQO4CTCtANuh14HsD1l37tnf50Uva5-bH9_FX7m91duNgAm7DLuPAiDQ\", \"x5c\": [\"MIICmzCCAYMCBgGLuLRGTjANBgkqhkiG9w0BAQsFADARMQ8wDQYDVQQDDAZtYXN0ZXIwHhcNMjMxMTEwMTAwNjQ0WhcNMzMxMTEwMTAwODI0WjARMQ8wDQYDVQQDDAZtYXN0ZXIwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC20JhwdCtWlCD489J0I6cUCzGMMWxHc0uV7G64p1scMBPa9GuAKafo8mkL1QPBJbfwc7PDJgYFvvLLWx9mXxrdeccSbAJOQZN/zRV+BFszp2f5lU0v7j9eVfOfPVn3KnlmEYoGraMVUIgT/H1WGl5VtR+3dsONzD8PnG1l0Wk9MFPt9JsBMLwizHAKUuSD79LjVsUxFGmBDV0kzk5l5I3dGePjRqP7KuTtBgsOUZi2cw4AhNOFjSpmZ/3QuenkIicyZWgrDRGo88xm4eK1ug1KG9RM3/U2gxA7gJMK0A26HXgewPWXfu2d/nRS9rn5sf38Vfub3V242ACbsMu48CINAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAD2DwCHe811jV+RstZb5E3C5HDFcH136KMORaa/3ixBxAKoh7PWIxV6KVtUn2QY9GS6sk8dajx3D9/xpAixodggTF5yM4L9gd0IVIax4Rcc5EdOJwR1FMQitKw5x6U2j31cTgTzlKB6tZB0QtbQcDTbXjyHvyX9p9e/v4/T1ZbxYLBS4GRNUf8CrMaiIfJ/ODaO93kQw/D5j17RgxE+INeKanTrNfww/NSV+28i81Tf6U1S1K6vijS3XkU5AFd/ki1ccExZAWJgE4tetWxcOHEew1lo1kJi36NlVMP1RSnawNcLmP0g9rpORiP6PHmiStqYx01OHyq85iYusH5mXyjw=\"], \"kid\": \"1HTqWpPbr73gG5YquJMOjwd5M34qrCfb9S9rN46SzOk\"}]}"
;

static const char test_token_str[] =
"eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICItaUZsOU14U09sb0dFM1ZOQnZLMnJDYVl5RmZ5dHZMWTFBQWZsel9Vc3ZBIn0.eyJleHAiOjE2OTk2NTYwODYsImlhdCI6MTY5OTY1NTc4NiwiYXV0aF90aW1lIjoxNjk5NjU1Nzg2LCJqdGkiOiJmNjJlYmVhZS03ZjVkLTRkYTktYWZlNC01ZDllM2MxMDM4YzYiLCJpc3MiOiJodHRwczovL3Vjcy1zc28tbmcuc2Nob29sLmRldi9yZWFsbXMvdWNzIiwiYXVkIjoibGRhcHM6Ly9zY2hvb2wuZGV2LyIsInN1YiI6ImY6Y2MxY2E0ZjMtMzA1ZC00YWY4LWE5OWEtY2U0M2YxMzYxMWU3OkFkbWluaXN0cmF0b3IiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJodHRwczovL21hc3RlcjMuc2Nob29sLmRldi91bml2ZW50aW9uL29hdXRoLyIsIm5vbmNlIjoiYmJiODI1ZWU3ZWUwNGRlZGE1YmFiMjMwZDhiM2RjYmEiLCJzZXNzaW9uX3N0YXRlIjoiMjhkZTFhZjAtMWIxOS00NzA3LTkwMjItZThmZTcxNzYyYTJjIiwiYWNyIjoiMSIsImFsbG93ZWQtb3JpZ2lucyI6WyJodHRwczovL21hc3RlcjMuc2Nob29sLmRldi91bml2ZW50aW9uL29hdXRoLyIsImh0dHBzOi8vbWFzdGVyMy5zY2hvb2wuZGV2L3VuaXZlbnRpb24vb2F1dGgvKiIsImh0dHBzOi8vbWFzdGVyMy5zY2hvb2wuZGV2IiwiaHR0cDovL21hc3RlcjMuc2Nob29sLmRldi91bml2ZW50aW9uL29hdXRoLyoiLCJodHRwOi8vMTAuMjAwLjI3LjMvdW5pdmVudGlvbi9vYXV0aC8qIiwiaHR0cHM6Ly8xMC4yMDAuMjcuMy91bml2ZW50aW9uL29hdXRoLyoiXSwicmVhbG1fYWNjZXNzIjp7InJvbGVzIjpbImRlZmF1bHQtcm9sZXMtdWNzIiwib2ZmbGluZV9hY2Nlc3MiLCJ1bWFfYXV0aG9yaXphdGlvbiJdfSwic2NvcGUiOiJvcGVuaWQgcHJvZmlsZSBlbWFpbCIsInNpZCI6IjI4ZGUxYWYwLTFiMTktNDcwNy05MDIyLWU4ZmU3MTc2MmEyYyIsInVpZCI6IkFkbWluaXN0cmF0b3IiLCJlbWFpbF92ZXJpZmllZCI6ZmFsc2UsIm5hbWUiOiJBZG1pbmlzdHJhdG9yIiwicHJlZmVycmVkX3VzZXJuYW1lIjoiYWRtaW5pc3RyYXRvciIsImZhbWlseV9uYW1lIjoiQWRtaW5pc3RyYXRvciJ9.N5enVnKQ7-BsZS7hCLNUiwbzg-yQtXq111RVo4WhOMavbSo-QCPQpPyw82wBHJvlEQ8LTOSSxnTlFdfPbe9wqY7fAFU-ru23zKMpNSjMQy3pWaG1j3C8IFbA99Hg0B0W_VOGpxCgXWFn1A1xn0HXDLVIBJ_Xav-eurEMicv0U_WMEj15Gpiyo1UX3gbajZGlDLnHOwAgQqAiKSXRjP1HxKERtWquth7OG-T-P8TaKr_FFOV4EErsH7JVfxyQDUSzE7bTExKaXou4tO-6sV6eNxDWnyzzntgavRvc1NC-TSWrtCFJ_Sy5Q_uII7ZJV6d80nSnoibHGPUf6Q03hc1iYA"
;

#include <yder.h>
static struct oauth_list trusted_aud;
static struct oauth_list trusted_azp;
static struct oauth_list required_scope;
static oauth_glob_context_t server_glob_context;

int main() {
	enum OAuthError rc;
	oauth_glob_context_t *gctx = &server_glob_context;
	gctx->grace = (time_t)6000000000000;
	gctx->uid_attr = "uid";
	gctx->trusted_iss = "https://ucs-sso-ng.school.dev/realms/ucs";
	gctx->trusted_jwks_str = (char *)test_jwks_str;

	trusted_aud.name = "ldaps://school.dev/";
	SLIST_INIT(&gctx->trusted_aud);
	SLIST_INSERT_HEAD(&gctx->trusted_aud, &trusted_aud, next);

	trusted_azp.name = "https://master3.school.dev/univention/oidc/";
	SLIST_INIT(&gctx->trusted_azp);
	SLIST_INSERT_HEAD(&gctx->trusted_azp, &trusted_azp, next);

	required_scope.name = "openid";
	SLIST_INIT(&gctx->required_scope);
	SLIST_INSERT_HEAD(&gctx->required_scope, &required_scope, next);

	oauth_serv_context_t ctx;
	ctx.glob_context = gctx;

	const void *utils = NULL;
	const char *oauth_user[256];

	y_init_logs("Rhonabwy", Y_LOG_MODE_CONSOLE, Y_LOG_LEVEL_DEBUG, NULL, "Starting Rhonabwy JWS tests");

	rc = oauth_check_jwt(&ctx, utils, oauth_user, test_token_str);
	if (rc != OK) {
		printf("Got user: %s\n", ctx.authcid);
	} else {
		fprintf(stderr, "oauth_check_jwt failed (%d), see syslog for details\n", rc);
	}

	y_close_logs();
}
#endif /*HACK*/
