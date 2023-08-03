/* $Id: pam_oidc.c,v 1.14 2017/08/13 14:29:00 manu Exp $ */

/*
 * Copyright (c) 2009 Emmanuel Dreyfus
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

#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <unistd.h>
#include <syslog.h>
#include <errno.h>
#include <pwd.h>
#include <sys/param.h>
#include <sys/queue.h>

#include <security/pam_modules.h>
#include <security/pam_appl.h>

#include "oidc.h"

#ifndef PAM_EXTERN
#define PAM_EXTERN
#endif

#define GCTX_DATA "CRUDEOIDC-GCTX"

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

static void gctx_cleanup(
	pam_handle_t *pamh,
	void *data,
	int error
) {
	oidc_glob_context_t *gctx = (oidc_glob_context_t *)data;

	if (gctx != NULL) {
		struct oidc_trusted_rp *item;

		/*
		if (gctx->uid_attr != NULL) {
			free((void *)gctx->uid_attr);
			gctx->uid_attr = NULL;
		}
		*/

		while ((item = SLIST_FIRST(&gctx->trusted_rp)) != NULL) {
			SLIST_REMOVE_HEAD(&gctx->trusted_rp, next);
			free(item);
		}

		if (gctx->trusted_jwks_str != NULL) {
			free((void *)gctx->trusted_jwks_str);
			gctx->trusted_jwks_str = NULL;
		}

		if (gctx->trusted_iss != NULL) {
			free((void *)gctx->trusted_iss);
			gctx->trusted_iss = NULL;
		}

		free(gctx);
		gctx = NULL;
	}
}

static oidc_glob_context_t * pam_global_context_init(
	pam_handle_t *pamh,
	int ac,
	const char **av
) {
	int error;
	const void *data;
	oidc_glob_context_t *gctx;
	int i;
	const char *cacert = NULL;
	const char *uid_attr = "uid";


	if (pam_get_data(pamh, GCTX_DATA, &data) == PAM_SUCCESS) {
		gctx = (oidc_glob_context_t *)data;
		syslog(LOG_ERR, "pam_get_data success, data = %p", data);
		return gctx;
	}

	if ((gctx = malloc(sizeof(*gctx))) == NULL) {
		syslog(LOG_ERR, "malloc() failed: %s", strerror(errno));
		return NULL;
	}

	memset(gctx, 0, sizeof(*gctx));

	SLIST_INIT(&gctx->trusted_rp);
	gctx->grace = (time_t)600;

	/*
	 * Get options
	 */
#define SETARG(argv,prop) 					\
	(strncmp((argv), (prop "="), strlen(prop "=")) == 0) ? 	\
	(argv) + strlen(prop "=") : NULL

	int num_of_iss = 0;
	int num_of_jwks = 0;
	for (i = 0; i < ac; i++) {
		const char *data;

		/*
		if ((data = SETARG(av[i], "userid")) != NULL) {
			uid_attr = data;
			continue;
		}
		*/

		if ((data = SETARG(av[i], "grace")) != NULL) {
			gctx->grace = atoi(data);
			continue;
		}

		if ((data = SETARG(av[i], "trusted_rp")) != NULL) {
			struct oidc_trusted_rp *item;

			if ((item = malloc(sizeof(*item))) == NULL) {
				error = PAM_SYSTEM_ERR;
				syslog(LOG_ERR,
				       "malloc() failed: %s", strerror(errno));
				goto cleanup;
			}

			SLIST_INSERT_HEAD(&gctx->trusted_rp, item, next);

			if ((item->name = strdup(data)) == NULL) {
				error = PAM_SYSTEM_ERR;
				syslog(LOG_ERR,
				       "strdup() failed: %s", strerror(errno));
				goto cleanup;
			}

			continue;
		}

		if ((data = SETARG(av[i], "iss")) != NULL) {
			if (num_of_iss > 0) { // TODO: support multiple issuers
				error = PAM_SYSTEM_ERR;
				syslog(LOG_ERR,
				       "multiple iss given");
				goto cleanup;
			}

			if ((gctx->trusted_iss = strdup(data)) == NULL) {
				error = PAM_SYSTEM_ERR;
				syslog(LOG_ERR,
				       "strdup() failed: %s", strerror(errno));
				goto cleanup;
			}

			num_of_iss++;
			continue;
		}

		if ((data = SETARG(av[i], "jwks")) != NULL) {
			if (num_of_jwks > 0) { // TODO: support multiple issuers
				error = PAM_SYSTEM_ERR;
				syslog(LOG_ERR,
				       "multiple jwks given");
				goto cleanup;
			}

			if (access(data, R_OK) != 0) {
				syslog(LOG_ERR,
				       "Unable to read Issuer JWKS file \"%s\"",
				       data);
				continue;
			}

			if ((gctx->trusted_jwks_str = malloc(JWKS_BUFFSIZE)) == NULL) {
				error = PAM_SYSTEM_ERR;
				syslog(LOG_ERR,
				       "malloc() failed: %s", strerror(errno));
				goto cleanup;
			}

			FILE *jwks_fp;
			jwks_fp = fopen(data, "r");
			fgets(gctx->trusted_jwks_str, JWKS_BUFFSIZE, jwks_fp); //TODO: Error handling
			fclose(jwks_fp);

			if (!gctx->trusted_jwks_str) {
				error = PAM_SYSTEM_ERR;
				syslog(LOG_ERR,
				   "Failed to load JWKS from \"%s\"", data);
				goto cleanup;
			}

			num_of_jwks++;
			syslog(LOG_DEBUG, "Loaded JWKS from \"%s\"", data);
			continue;
		}

		if ((cacert = SETARG(av[i], "cacert")) != NULL) {
			if (access(cacert, R_OK) != 0) {
				error = PAM_OPEN_ERR;
				syslog(LOG_ERR,
				       "Unable to read CA bundle \"%s\"",
				       cacert);
				goto cleanup;
			}
			continue;
		}
	}

	if (!num_of_iss || !num_of_jwks) {
		syslog(LOG_ERR, "iss and/or jwks missing");
		error = PAM_OPEN_ERR;
		goto cleanup;
	}

	/*
	if ((gctx->uid_attr = strdup(uid_attr)) == NULL) {
		error = PAM_SYSTEM_ERR;
		syslog(LOG_ERR, "strdup failed: %s", strerror(errno));
		goto cleanup;
	}
	*/

	error = pam_set_data(pamh, GCTX_DATA, (void *)gctx, gctx_cleanup);
	if (error != PAM_SUCCESS) {
		syslog(LOG_ERR, "pam_set_data() failed: %s",
		       pam_strerror(pamh, error));
		goto cleanup;
	}

	return gctx;

cleanup:
	gctx_cleanup(pamh, gctx, error);
	return NULL;
}

PAM_EXTERN int pam_sm_authenticate(
	pam_handle_t *pamh,
	int flags,
	int ac,
	const char **av
) {
	oidc_serv_context_t ctx;
	struct passwd *pwd;
	struct passwd pwres;
	char pwbuf[1024];
	const char *user;
	const void *host;
	const char *oidc_user;
	const void *oidc_msg;
	int error;

	/* Check host, and skip OIDC check if it is listed  */
	if (pam_get_item(pamh, PAM_RHOST, &host) == PAM_SUCCESS) {
		int i;

		for (i = 0; i < ac; i++) {
			const char *from = "only_from=";
			const char *list;
			char *last;
			char *p;

			if (strncmp(av[i], from, strlen(from)) != 0)
				continue;

			/*
			 * We found a list of hosts for which OIDC
			 * check must be available
			 */
			list = av[i] + strlen(from);

			for ((p = strtok_r((char *)list, ",", &last));
			     (p != NULL);
			     (p = strtok_r(NULL, ",", &last)))
				if (strcmp(p, host) == 0)
					break;

			/*
			 * Remote host is not in the list,
			 * no OIDC check performed.
			 */
			if (p == NULL)
				return PAM_IGNORE;
		}
	}

	/* identify user */
	if ((error = pam_get_user(pamh, &user, NULL)) != PAM_SUCCESS) {
		syslog(LOG_ERR, "pam_get_user() failed: %s",
		       pam_strerror(pamh, error));
		return error;
	}

	if (getpwnam_r(user, &pwres, pwbuf, sizeof(pwbuf), &pwd) != 0) {
		syslog(LOG_ERR, "getpwnam_r(%s) failed: %s",
		       user, strerror(errno));
		return PAM_TRY_AGAIN;
	}

	if (pwd == NULL)
		syslog(LOG_WARNING, "inexistant user %s", user);

	error = pam_get_item(pamh, PAM_AUTHTOK, &oidc_msg);
	if (error != PAM_SUCCESS) {
		syslog(LOG_ERR, "pam_get_item(PAM_AUTHTOK) failed: %s",
		       pam_strerror(pamh, error));
		return error;
	}

	if (oidc_msg == NULL) {
		struct pam_message msg;
		struct pam_message *msgp;
		struct pam_response *resp;
		const void *convptr;
		const struct pam_conv *conv;

		error = pam_get_item(pamh, PAM_CONV, &convptr);
		if (error != PAM_SUCCESS) {
			syslog(LOG_ERR, "pam_get_item(PAM_CONV) failed: %s",
			       pam_strerror(pamh, error));
			return error;
		}

		conv = convptr;

		msg.msg_style = PAM_PROMPT_ECHO_OFF;
		msg.msg = "OIDC message: ";
		msgp = &msg;
		resp = NULL;
		if ((error = conv->conv(1, (const struct pam_message **)&msgp,
		    &resp, conv->appdata_ptr)) != PAM_SUCCESS) {
			syslog(LOG_ERR, "PAM conv error: %s",
			       pam_strerror(pamh, error));
			return error;
		}

		if (resp == NULL)
			return PAM_CONV_ERR;

		oidc_msg = resp[0].resp;
		resp[0].resp = NULL;
		free(resp);
		pam_set_item(pamh, PAM_AUTHTOK, oidc_msg);
	}

	/* Is it big enough to make sense? */
	if (strlen(oidc_msg) < OIDC_MINLEN) {
		syslog(LOG_ERR, "oidc_msg is too small: minlength = %d",
		       OIDC_MINLEN);
		return PAM_AUTH_ERR;
	};

	/* We are now committed to check the OIDC token */
	memset(&ctx, 0, sizeof(ctx));
	ctx.glob_context = pam_global_context_init(pamh, ac, av);
	if (ctx.glob_context == NULL)
		return PAM_SYSTEM_ERR;

	// oidc_check_all_assertions(&ctx, NULL, &oidc_user, (char *)oidc_msg, MAYBE_COMPRESS);
	error = oidc_check_jwt(&ctx, NULL, &oidc_user, (char *)oidc_msg, MAYBE_COMPRESS);

	if ((error != 0) || (oidc_user == NULL)) {
		error = PAM_AUTH_ERR;
		goto out;
	}

	if (strcmp(user, oidc_user) != 0) {
		error = PAM_AUTH_ERR;
		syslog(LOG_INFO, "oidc token user \"%s\", "
				 "requested user \"%s\"", oidc_user, user);
		goto out;
	}

#if 0
	if ((error = pam_set_item(pamh, PAM_USER, user)) != PAM_SUCCESS) {
		syslog(LOG_ERR, "pam_set_item(PAM_USER) failed: %s",
		       pam_strerror(pamh, error));
		goto out;
	}
#endif

	error = PAM_SUCCESS;
out:
	if (ctx.userid != NULL)
		free(ctx.userid);

	return error;
}

/* ARGSUSED0 */
PAM_EXTERN int pam_sm_setcred(
	pam_handle_t *pamh,
	int flags,
	int ac,
	const char **av
) {
	return PAM_SUCCESS;
}

/* ARGSUSED0 */
PAM_EXTERN int pam_sm_acct_mgmt(
	pam_handle_t *pamh,
	int flags,
	int ac,
	const char **av
) {
	return PAM_SUCCESS;
}

/* ARGSUSED0 */
PAM_EXTERN int pam_sm_open_session(
	pam_handle_t *pamh,
	int flags,
	int ac,
	const char **av
) {
	return PAM_SUCCESS;
}

PAM_EXTERN int pam_sm_close_session(
	pam_handle_t *pamh,
	int flags,
	int ac,
	const char **av
) {
	return PAM_SUCCESS;
}

PAM_EXTERN int pam_sm_chauthtok(
	pam_handle_t *pamh,
	int flags,
	int ac,
	const char **av
) {
	return PAM_SUCCESS;
}

#ifdef PAM_STATIC
struct pam_module _pam_oidc_modstruct = {
	"pam_oidc",
	pam_sm_authenticate,
	pam_sm_setcred,
	pam_sm_acct_mgmt,
	pam_sm_open_session,
	pam_sm_close_session,
	pam_sm_chauthtok
};
#endif /* PAM_STATIC */
