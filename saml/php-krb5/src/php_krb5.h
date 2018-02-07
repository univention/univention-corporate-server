/**
* Copyright (c) 2008 Moritz Bechler
*
* Permission is hereby granted, free of charge, to any person obtaining a copy
* of this software and associated documentation files (the "Software"), to deal
* in the Software without restriction, including without limitation the rights
* to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
* copies of the Software, and to permit persons to whom the Software is
* furnished to do so, subject to the following conditions:
*
* The above copyright notice and this permission notice shall be included in
* all copies or substantial portions of the Software.
*
* THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
* IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
* FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
* AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
* LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
* OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
* THE SOFTWARE.
**/

#ifndef PHP_KRB5_H
#define PHP_KRB5_H

#ifdef ZTS
#include "TSRM.h"
#endif

#include "php.h"
#include "Zend/zend_exceptions.h"
#include "php_krb5_gssapi.h"

#ifdef HAVE_KADM5
#define KADM5_API_VERSION 3
#endif

#define PHP_SUCCESS SUCCESS

#define KRB5_PRIVATE 1

#include <krb5.h>
#include <gssapi/gssapi.h>
#include <gssapi/gssapi_krb5.h>

#define PHP_KRB5_EXT_NAME "krb5"
#define PHP_KRB5_VERSION "1.1.2"


extern zend_module_entry krb5_module_entry;
#define phpext_krb5_ptr &krb5_module_entry

#ifdef PHP_WIN32
#define PHP_KRB5_API __dllspec(dllexport)
#else
#define PHP_KRB5_API
#endif


PHP_MINIT_FUNCTION(krb5);
PHP_MSHUTDOWN_FUNCTION(krb5);
PHP_MINFO_FUNCTION(krb5);

extern zend_class_entry *krb5_ce_ccache;

typedef struct _krb5_ccache_object {
#if PHP_MAJOR_VERSION < 7
	zend_object std;
#endif
	krb5_context ctx;
	krb5_ccache cc;
	char *keytab;
#if PHP_MAJOR_VERSION >= 7
	zend_object std;
#endif
} krb5_ccache_object;

krb5_error_code php_krb5_display_error(krb5_context ctx, krb5_error_code code, char* str TSRMLS_DC);


/* KRB5NegotiateAuth Object */
int php_krb5_negotiate_auth_register_classes(TSRMLS_D);

/* KADM5 glue */
#ifdef HAVE_KADM5
int php_krb5_kadm5_register_classes(TSRMLS_D);
#endif



#endif /* PHP_KRB5_H */
