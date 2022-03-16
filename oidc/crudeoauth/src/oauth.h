/* $Id: oauth.h,v 1.7 2017/05/24 22:47:15 manu Exp $ */
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

#define MAYBE_COMPRESS 1
#define JWT_MINLEN 76 /* len(b64encode(b'{"access_token":"eyJhbGciOiJub25lIn0.eyJzdWIiOiJ7fX0.."}')) */

enum OAuthError {
	OK,
	INVALID_ISSUER,
	INVALID_AUDIENCE,
	INVALID_AUTHORIZED_PARTY,
	CLAIM_EXPIRED,
	MISSING_UID_CLAIM,
	INVALID_SIGNATURE,
	PARSE_ERROR,
	CONFIG_ERROR
};

struct oauth_trusted_list {
	const char *name;
	SLIST_ENTRY(oauth_trusted_list) next;
};

static const int JWKS_BUFFSIZE = 4096;

typedef struct {
	const char *uid_attr;
	time_t grace;
	int flags;
	SLIST_HEAD(oauth_trusted_aud_list_head, oauth_trusted_list) trusted_aud;
	SLIST_HEAD(oauth_trusted_azp_list_head, oauth_trusted_list) trusted_azp;
	const char *trusted_iss;
	char *trusted_jwks_str;
} oauth_glob_context_t;
/* oauth_glob_context_t flags */

typedef struct {
	oauth_glob_context_t *glob_context;
	char *userid;
} oauth_serv_context_t;

void oauth_log(const void *, int, const char *, ...);
void oauth_error(const void *, int, const char *, ...);
int oauth_strdup(const void *, const char *, char **, int *);
int oauth_retcode(enum OAuthError);

enum OAuthError oauth_check_jwt(oauth_serv_context_t *, const void *, const char **, char *, int);
const char* oauth_enum_error_string(enum OAuthError);
