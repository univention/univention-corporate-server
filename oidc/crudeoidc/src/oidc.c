#include "config.h"

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <fcntl.h>
#include <errno.h>
#include <stdarg.h>
#include <ctype.h>
#include <syslog.h>
#include <errno.h>
//#include <zlib.h>
#include <sys/stat.h>
#include <sys/queue.h>
#include <time.h>

#include <sasl/saslutil.h> /* XXX for sasl_decode64 */

#include "oidc.h"

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
// wget https://login.$(hostname -f)/realms/master/protocol/openid-connect/certs -O - | python -c 'import json, sys; print(json.dumps(json.load(sys.stdin)["keys"][0]))'
// static const char jwk_str[] = ...;

static const char test_jwks_str[] =
"{\"keys\":[{\"kid\":\"ldN7fMGxGayNmTk9CL_I_or-GN7TN8r30DJh8B50CAg\",\"kty\":\"RSA\",\"alg\":\"RS256\",\"use\":\"sig\",\"n\":\"kVaQrNhk8e91HVjPHRZPBDYtOa8tfl7CD71Q75nEfV2a2JbbLHNc_JEozcgu35rRYbL9fLtrgLENhXO_kNMszyMIhSl5zcviL7y0PShoOQ2E6WU1yeS2Omg_3O6dhMVXISO8hfrA_fioawA7BWpPYqJJWBk7-yqboSN8Dz_HP5sF_6Vtg_aVM8DIJTJx_gnK7TPGp-jOMeQHnX1Oh1YQwcFZLRrw9uLXzjR69wqxGBfwLH-2dCHiU-S30Rg-aRPI500iD2mxPwPTDLnK_zIWTolpwGNr9Y6XnrF6T78HU4_qdpSdqnGK4H0Ccfp_ecDv2B6E7p-udmTHXIbJobNWyQ\",\"e\":\"AQAB\",\"x5c\":[\"MIICmzCCAYMCBgF/aiCg2zANBgkqhkiG9w0BAQsFADARMQ8wDQYDVQQDDAZtYXN0ZXIwHhcNMjIwMzA4MTUyMTM3WhcNMzIwMzA4MTUyMzE3WjARMQ8wDQYDVQQDDAZtYXN0ZXIwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQCRVpCs2GTx73UdWM8dFk8ENi05ry1+XsIPvVDvmcR9XZrYltssc1z8kSjNyC7fmtFhsv18u2uAsQ2Fc7+Q0yzPIwiFKXnNy+IvvLQ9KGg5DYTpZTXJ5LY6aD/c7p2ExVchI7yF+sD9+KhrADsFak9ioklYGTv7KpuhI3wPP8c/mwX/pW2D9pUzwMglMnH+CcrtM8an6M4x5AedfU6HVhDBwVktGvD24tfONHr3CrEYF/Asf7Z0IeJT5LfRGD5pE8jnTSIPabE/A9MMucr/MhZOiWnAY2v1jpeesXpPvwdTj+p2lJ2qcYrgfQJx+n95wO/YHoTun652ZMdchsmhs1bJAgMBAAEwDQYJKoZIhvcNAQELBQADggEBADPJFvadV+dl6R1uDq3RCWo5QrgyUp1QP9BEDj2ZffgyYwvJ+Pbbs7ORuxajK75qjeilquQsdA/buslIO7yx+C4/3wEl7u6RzuOBQsPDXDc/mGYJNOUVgEnvGaIv97lRSiqY8bz62Y7LI3lNJiaancrpAy2IchDFihH9jV8ekEQIapmu13/YDOxQ4MGtj4PMepYT1grumHwl5yzNip3T7+aZxEVWzMY1wNcCc5W0Lx7bOH+3YqWDVjl6PPXkl4r9xr0U/jDpfbindowFtHra+ioPVUhhZsbWqiul9E7Sa5SOVOL+mw0foLpbC95yTAoHRa/lkHoA4rICyvTWMN1HICE=\"],\"x5t\":\"jew7pN3keOcNo6bZE_fd6V75L9U\",\"x5t#S256\":\"FP4Jme-1XIvs043AdaQBLypFUNQPocwqkbjl-h_0HBE\"},{\"kid\":\"F_u3j46hdxEZoU9NZC11zH8w10kX_C_Jlg_LDZLloj4\",\"kty\":\"RSA\",\"alg\":\"RSA-OAEP\",\"use\":\"enc\",\"n\":\"tFCRXmVMQtMm_3c_LGntLqHHr-kl0xwmdWgAizFaCN-qyfL4Cswtz57gye3nYlZutSQHkKrbK3EJ57Pj_QvRi9sERdvZLoP75CfmC67_zdKoAX29C-6csgIHVf7ed8sLfR4r-XtlcBOgaWUynrUVWGD3HK-pzhnRJzPQnLI5HgvRSEyJ6lOcaL2n-K68lhoKHf36FCeP6XxJBXHNs1_HoeHruTOsta72baedgftKwBW-uLJ3u34tzFUohZokDy_IUDmEbgBcmpqT5Zda3LQ56SN6Z6m7xl6S5vrkcsvuVi-Zji0DDo1oX2x0q6dalL9lf2SfF2IosBWr-lC7FDpDjQ\",\"e\":\"AQAB\",\"x5c\":[\"MIICmzCCAYMCBgF/aiCjcTANBgkqhkiG9w0BAQsFADARMQ8wDQYDVQQDDAZtYXN0ZXIwHhcNMjIwMzA4MTUyMTM4WhcNMzIwMzA4MTUyMzE4WjARMQ8wDQYDVQQDDAZtYXN0ZXIwggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQC0UJFeZUxC0yb/dz8sae0uocev6SXTHCZ1aACLMVoI36rJ8vgKzC3PnuDJ7ediVm61JAeQqtsrcQnns+P9C9GL2wRF29kug/vkJ+YLrv/N0qgBfb0L7pyyAgdV/t53ywt9Hiv5e2VwE6BpZTKetRVYYPccr6nOGdEnM9CcsjkeC9FITInqU5xovaf4rryWGgod/foUJ4/pfEkFcc2zX8eh4eu5M6y1rvZtp52B+0rAFb64sne7fi3MVSiFmiQPL8hQOYRuAFyampPll1rctDnpI3pnqbvGXpLm+uRyy+5WL5mOLQMOjWhfbHSrp1qUv2V/ZJ8XYiiwFav6ULsUOkONAgMBAAEwDQYJKoZIhvcNAQELBQADggEBAE8l+ulx8SDnhXJd65vJ58FOscuBHNW+wOCSyXxOnHz12DOOawyppUis0XRsRRWI8tpiofhehAD7eOUDCaXcblhNHblCc8uqsEP7/IIZ/V1OVLgjWIGYjS4lSwuCakXJNGKMYFXlq2yH7QcCI60UcHb1+cXwacOslUwUL/VkqznKcrYcG0lPsAgeqSvihqiHVjMW1HbLKMQ5I93eWeKR20sFyZIqSQaPZNbe0NgiZOghx6C6ncxEG6+2v5ZytwqQ9KA4RBWTuJ2gBOC9VDnOMHbpZwB0WUgcOyvBrr/L4awO9efyqSSTi7R2/ej9qz+j0ESvRJYeEVg5eV0J8WktKIE=\"],\"x5t\":\"mAD-BUSjqXfgOB4GqIrbsVwsLq0\",\"x5t#S256\":\"Xfr4M0kN3k-yRBkHxgjN7bYufEFHZbs2pCVQeLa_bgs\"}]}"
;

static const char test_token_str[] =
"{\"access_token\":\"eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJsZE43Zk1HeEdheU5tVGs5Q0xfSV9vci1HTjdUTjhyMzBESmg4QjUwQ0FnIn0.eyJleHAiOjE2NDczNTg4NTIsImlhdCI6MTY0NzM1ODc5MiwianRpIjoiOWQ3NWYxNTMtOTljZi00YThmLTliZDUtNGFhMmVlYmVhY2YzIiwiaXNzIjoiaHR0cHM6Ly9sb2dpbi5wcmltYXJ5MjAudWNzNTBkb21haW4ubmV0L3JlYWxtcy9tYXN0ZXIiLCJzdWIiOiIyMDUxNTRlNC1lMjBlLTRiY2YtYjQ0Mi1hZTc4ZTA1NzA5NzMiLCJ0eXAiOiJCZWFyZXIiLCJhenAiOiJhZG1pbi1jbGkiLCJzZXNzaW9uX3N0YXRlIjoiOTFjYmZiMmQtZGMwMS00ODVkLThmOGEtZjk0OGIyZDBkNDQzIiwiYWNyIjoiMSIsInNjb3BlIjoicHJvZmlsZSBlbWFpbCIsInNpZCI6IjkxY2JmYjJkLWRjMDEtNDg1ZC04ZjhhLWY5NDhiMmQwZDQ0MyIsImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwibmFtZSI6IktleWNsb2FrIiwicHJlZmVycmVkX3VzZXJuYW1lIjoidGVzdHVzZXIxIiwiZmFtaWx5X25hbWUiOiJLZXljbG9hayJ9.WbGiulEYbSwU50VvyqPJAP_Pr9VX0x7lf4ydDqjexzLh361iIzvXwWHHaJzAbl0PXBdHq4iz6zYN-gTsG2jC-v5LTI4D4aZQH4pbFjIzeBYEhXZcrMhDj-NxPCklRXNldk5SPhVyMDBw64AYhJkud4FNCETJf6kpTeW9_egydsphGfzXYvmNVv-DzDApFQDDGdvHa5WVbOa-gxn9Eu4iBnGobPTfI4ldrSVPxtWO6vEA3v09Ksaj5OrBqoG--5qJhUyRX898IkXCry09YP_V0l_nDQ4pG0EUehr62l8VZnf3gl_8nKAbYiVDN0u23ym9-psvK0CuLaAZdIzmC--giQ\",\"expires_in\":60,\"refresh_expires_in\":1800,\"refresh_token\":\"eyJhbGciOiJIUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJhY2MwMGY2OC03MTgzLTRmN2UtYWM4ZC1kNTU5NGY0ODFjZjEifQ.eyJleHAiOjE2NDczNjA1OTIsImlhdCI6MTY0NzM1ODc5MiwianRpIjoiOWYzOGNjOTEtNDEwNi00YjAxLWE5NmItMzg1Y2E1MmE2YWRiIiwiaXNzIjoiaHR0cHM6Ly9sb2dpbi5wcmltYXJ5MjAudWNzNTBkb21haW4ubmV0L3JlYWxtcy9tYXN0ZXIiLCJhdWQiOiJodHRwczovL2xvZ2luLnByaW1hcnkyMC51Y3M1MGRvbWFpbi5uZXQvcmVhbG1zL21hc3RlciIsInN1YiI6IjIwNTE1NGU0LWUyMGUtNGJjZi1iNDQyLWFlNzhlMDU3MDk3MyIsInR5cCI6IlJlZnJlc2giLCJhenAiOiJhZG1pbi1jbGkiLCJzZXNzaW9uX3N0YXRlIjoiOTFjYmZiMmQtZGMwMS00ODVkLThmOGEtZjk0OGIyZDBkNDQzIiwic2NvcGUiOiJwcm9maWxlIGVtYWlsIiwic2lkIjoiOTFjYmZiMmQtZGMwMS00ODVkLThmOGEtZjk0OGIyZDBkNDQzIn0.d3i4aqhB78znNdn1bV5qCP6c0OlIsq_dGUrI3C0Lrcw\",\"token_type\":\"Bearer\",\"not-before-policy\":0,\"session_state\":\"91cbfb2d-dc01-485d-8f8a-f948b2d0d443\",\"scope\":\"profile email\"}"
;

/* Helper functions copied from pam_oidc.c for compiling oidc.c with -DHACK */
void oidc_log(
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

void oidc_error(
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

#include <security/pam_modules.h>
#include <security/pam_appl.h>
int oidc_retcode(
	int code
) {
	int retcode;

	switch(code) {
	case 0:
		retcode = PAM_SUCCESS;
		break;
	case EINVAL:
		retcode = PAM_CRED_ERR;
		break;
	case EACCES:
		retcode = PAM_AUTH_ERR;
		break;
	case ENOMEM:
	default:
		retcode = PAM_SYSTEM_ERR;
		break;
	}

	return retcode;
}

int oidc_strdup(
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

int oidc_check_token_iss(
	oidc_serv_context_t *ctx,
	const void *utils,
	jwt_t *jwt
) {
	const char *iss = r_jwt_get_claim_str_value(jwt, "iss");
	if ((iss != NULL) && (*iss != '\0')) {
		// printf("iss: %s\n", iss);
		if (strcmp(iss, ctx->glob_context->trusted_iss)) {
			oidc_error(utils, 0,
				"OIDC issuer %s is unknown", iss);
			return EACCES;
		}
	} else {
		oidc_error(utils, 0,
			   "token contains no iss");
		return EACCES;
	}

	return 0;

}

int oidc_check_token_azp(
	oidc_serv_context_t *ctx,
	const void *utils,
	jwt_t *jwt
) {
	const char *azp = r_jwt_get_claim_str_value(jwt, "azp");
	if ((azp != NULL) && (*azp != '\0')) {
		// printf("azp: %s\n", azp);
		// TODO: fix the check below
		struct oidc_trusted_rp *rp;
		SLIST_FOREACH(rp, &ctx->glob_context->trusted_rp, next)
			if (strcmp(rp->name, azp) == 0)
				return 0;
	} else {
		oidc_error(utils, 0,
			   "token contains no azp");
		return EACCES;
	}

	return EACCES;
}

static int oidc_check_token_validity_dates(
	oidc_serv_context_t *ctx,
	const void *utils,
	jwt_t *jwt
) {
	time_t limit, now;
	time_t grace = ctx->glob_context->grace;
	struct tm now_tm;
	struct tm limit_tm;
	char now_str[1024];
	char limit_str[1024];

	now = time(NULL);
	(void)gmtime_r(&now, &now_tm);
	(void)strftime(now_str, sizeof(now_str), "%Y-%m-%dT%H:%M:%SZ", &now_tm);

	limit = r_jwt_get_claim_int_value(jwt, "iat");
	if (limit != 0) {
		(void)gmtime_r(&limit, &limit_tm);
		(void)strftime(limit_str, sizeof(limit_str), "%Y-%m-%dT%H:%M:%SZ", &limit_tm);
		oidc_log(utils, LOG_DEBUG,
			 "OIDC claim "
			 "iat = %ld",
			 limit);
		if (limit == (time_t)-1) {
			oidc_error(utils, 0, 
				   "Invalid iat %ld",
				   limit);
			return EINVAL;
		}

		if (now < limit - grace) {
			oidc_error(utils, 0, 
				   "OIDC token not yet valid: iat %s, "
				   "current time is %s",
				   limit_str, now_str);
			return EACCES;
		}
	}
	limit = r_jwt_get_claim_int_value(jwt, "iat");
	if (limit != 0) {
		(void)gmtime_r(&limit, &limit_tm);
		(void)strftime(limit_str, sizeof(limit_str), "%Y-%m-%dT%H:%M:%SZ", &limit_tm);
		oidc_log(utils, LOG_DEBUG,
			 "OIDC claim "
			 "exp = %ld",
			 limit);
		if (limit == (time_t)-1) {
			oidc_error(utils, 0, 
				   "Invalid exp %ld",
				   limit);
			return EINVAL;
		}

		if (now > limit + grace) {
			oidc_error(utils, 0, 
				   "OIDC token expired at %s, "
				   "current time is %s",
				   limit_str, now_str);
			return EACCES;
		}
	}

	return 0;
}


int oidc_check_token_uid(
	oidc_serv_context_t *ctx,
	const void *utils,
	jwt_t *jwt
) {
	int error;
	const char *preferred_username = r_jwt_get_claim_str_value(jwt, "preferred_username");
	if ((preferred_username != NULL) && (*preferred_username != '\0')) {
		if ((error = oidc_strdup(utils, preferred_username, &ctx->userid, NULL)) != 0) {
			return error;
		}
	} else {
		oidc_error(utils, 0,
			   "token contains no preferred_username");
			   // "token contains no %s", gctx->uid_attr);
		return EACCES;
	}

	return 0;

}


int oidc_check_jwt_signature(
	oidc_serv_context_t *ctx,
	const void *utils,
	jwt_t *jwt,
	jwk_t *jwk
) {
	int error = 0;
	AUTOPTR(char) claims = NULL;

	if (r_jwt_verify_signature(jwt, jwk, 0) != RHN_OK) {
		oidc_error(utils, 0, "Error r_jwt_verify_signature");
		error = EINVAL;
		goto out;
	}

	claims = r_jwt_get_full_claims_str(jwt);
	printf("Verified payload:\n%s\n", claims);

out:
	return error;
}


jwk_t * oidc_get_jwk(
	oidc_serv_context_t *ctx,
	const void *utils
) {
	int error = 0;
	AUTOPTR(jwks_t) jwks = NULL;
	jwk_t *jwk;
	unsigned char output[2048];
	size_t output_len = 2048;

	if (r_jwks_init(&jwks) != RHN_OK) {
		oidc_error(utils, 0, "Error r_jwks_init");
		error = EINVAL;
		goto out;
	}

	// if (r_jwks_import_from_str(jwks, jwks_str) != RHN_OK) {  // rhonabwy-0.9.13 style
	if (r_jwks_import_from_json_str(jwks, ctx->glob_context->trusted_jwks_str) != RHN_OK) {
		oidc_error(utils, 0, "Error r_jwks_import_from_str");
		error = EINVAL;
		goto out;
	}

	jwk = r_jwks_get_at(jwks, 0);  // TODO: find the proper key type
	if (!jwk) {
		oidc_error(utils, 0, "Error r_jwks_get_at");
		error = EINVAL;
		goto out;
	}

	if (r_jwk_export_to_pem_der(jwk, R_FORMAT_PEM, output, &output_len, 0) != RHN_OK) {
		oidc_error(utils, 0, "Error r_jwk_export_to_pem_der");
		error = EINVAL;
		goto out;
	}
	printf("Exported key:\n%.*s\n", (int)output_len, output);
	return jwk;

out:
	return NULL;
}


int oidc_check_jwt(
	oidc_serv_context_t *ctx,
	const void *utils,
	const char **userid,
	char *msg,
	int flags
) {
	unsigned int msg_len;
	int error = EINVAL;
	AUTOPTR(jwk_t) jwk = NULL;
	AUTOPTR(jwt_t) jwt = NULL;

	if (msg == NULL) {
		oidc_error(utils, 0, "No token");
		return oidc_retcode(EINVAL);
	}

	/*
	 * The message must be long enough to hold an jwt
	 */
	msg_len = strlen(msg);
	if (msg_len < OIDC_MINLEN) {  // TODO: is this correct for OIDC?
		oidc_error(utils, 0, "Token too short");
		return oidc_retcode(EINVAL);
	}

	/*
	 * Remove any trailing cruft (space, newlines)
	 */
	while (msg_len > 0 && !isgraph((int)msg[msg_len - 1]))
		msg[msg_len--] = '\0';

	if (sasl_decode64(msg, msg_len, msg, msg_len, &msg_len) != 0) {
		oidc_error(utils, 0, "Cannot base64-decode message");
		return oidc_retcode(EINVAL);
	}
	msg[msg_len] = '\0';

	json_t * j_input = json_loads(msg, JSON_DECODE_ANY, NULL);
	msg = (char *) json_string_value(json_object_get(j_input, "access_token"));
	if (!msg) {
		oidc_error(utils, 0, "Error No access_token found in OIDC message");
		error = EINVAL;
		goto out;
	}
	msg_len = strlen(msg);

	// TODO maybe move to sasl_server_plug_init & pam_global_context_init ?
	jwk = oidc_get_jwk(ctx, utils);
	if (!jwk) {
		oidc_error(utils, 0, "Error oidc_get_jwk");
		error = EINVAL;
		goto out;
	}

	// parse the token
	if (r_jwt_init(&jwt) != RHN_OK) {
		oidc_error(utils, 0, "Error oidc_get_jwk");
		error = EINVAL;
		goto out;
	}

	if (r_jwt_parse(jwt, msg, 0) != RHN_OK) {
		oidc_error(utils, 0, "Error r_jwt_parse");
		error = EINVAL;
		goto out;
	}

	if ((error = oidc_check_jwt_signature(ctx, utils, jwt, jwk)) != 0)
		goto out;
	if ((error = oidc_check_token_iss(ctx, utils, jwt)) != 0)
		goto out;
	if ((error = oidc_check_token_azp(ctx, utils, jwt)) != 0)
		goto out;
	if ((error = oidc_check_token_validity_dates(ctx, utils, jwt)) != 0)
		goto out;
	if ((error = oidc_check_token_uid(ctx, utils, jwt)) != 0)
		goto out;

	*userid = ctx->userid;
out:
	return oidc_retcode(error);
}

#ifdef HACK
/* To compile with gcc oidc.c -lrhonabwy -lsasl2 -lorcania -lyder -ljansson -DHACK */

#include <yder.h>
static struct oidc_trusted_rp trusted_rp;
static oidc_glob_context_t server_glob_context;

int main() {
	int rc;

	oidc_glob_context_t *gctx = &server_glob_context;
	gctx->grace = (time_t)6000000000000;
	gctx->trusted_iss = "https://login.primary20.ucs50domain.net/realms/master";
	gctx->trusted_jwks_str = (char *)test_jwks_str;

	trusted_rp.name = "admin-cli";
	SLIST_INIT(&gctx->trusted_rp);
	SLIST_INSERT_HEAD(&gctx->trusted_rp, &trusted_rp, next);

	oidc_serv_context_t ctx;
	ctx.glob_context = gctx;

	const void *utils = NULL;
	const char *userid[256];
	int flags = 0;
	char msg[4096];
	unsigned int msg_len = 4096;

	y_init_logs("Rhonabwy", Y_LOG_MODE_CONSOLE, Y_LOG_LEVEL_DEBUG, NULL, "Starting Rhonabwy JWS tests");

	unsigned int token_len = strlen(test_token_str);
	if (sasl_encode64(test_token_str, token_len, msg, msg_len, &msg_len) != 0) {
		oidc_error(utils, 0, "Cannot base64-encode message");
		exit(1);
	}

	rc = oidc_check_jwt(&ctx, utils, userid, msg, flags);
	if (!rc) {
		printf("Got user: %s\n", ctx.userid);
	} else {
		fprintf(stderr, "oidc_check_jwt failed (%d), see syslog for details\n", rc);
	}

	y_close_logs();
}
#endif /*HACK*/
