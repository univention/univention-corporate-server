/* $Id: oidc.h,v 1.7 2017/05/24 22:47:15 manu Exp $ */
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
#define OIDC_MINLEN 128

struct oidc_trusted_rp {
	const char *name;
	SLIST_ENTRY(oidc_trusted_rp) next;
};

static const int JWKS_BUFFSIZE = 4096; // TODO: fix

typedef struct {
	// const char *uid_attr;
	time_t grace;
	int flags;
	SLIST_HEAD(oidc_trusted_rp_head, oidc_trusted_rp) trusted_rp;
        const char *trusted_iss;
        char *trusted_jwks_str;
} oidc_glob_context_t;
/* oidc_glob_context_t flags */

typedef struct {
        oidc_glob_context_t *glob_context;
        char *userid;
} oidc_serv_context_t;

void oidc_log(const void *, int, const char *, ...);
void oidc_error(const void *, int, const char *, ...);
int oidc_strdup(const void *, const char *, char **, int *);
int oidc_retcode(int);

int oidc_check_jwt(oidc_serv_context_t *, const void *, const char **, char *, int);
