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


#include "php.h"
#include "php_krb5.h"
#include "compat.h"

/* Class definition */

zend_class_entry *krb5_ce_gssapi_context;

typedef struct _krb5_gssapi_context_object {
#if PHP_MAJOR_VERSION < 7
		zend_object std;
#endif
		gss_cred_id_t creds;
		gss_ctx_id_t context;
#if PHP_MAJOR_VERSION >= 7
		zend_object std;
#endif
} krb5_gssapi_context_object;

ZEND_BEGIN_ARG_INFO_EX(krb5_GSSAPIContext_registerAcceptorIdentity, 0, 0, 1)
	ZEND_ARG_INFO(0, keytab)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(krb5_GSSAPIContext_acquireCredentials, 0, 0, 1)
	ZEND_ARG_OBJ_INFO(0, ccache, KRB5CCache, 0)
	ZEND_ARG_INFO(0, name)
	ZEND_ARG_INFO(0, type)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(krb5_GSSAPIContext_none, 0, 0, 0)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(krb5_GSSAPIContext_initSecContextArgs, 0, 0, 1)
	ZEND_ARG_INFO(0, target)
	ZEND_ARG_INFO(0, input_token)
	ZEND_ARG_INFO(0, reqflags)
	ZEND_ARG_INFO(0, timereq)
	ZEND_ARG_INFO(1, output_token)
	ZEND_ARG_INFO(1, ret_flags)
	ZEND_ARG_INFO(1, time_rec)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(krb5_GSSAPIContext_acceptSecContextArgs, 0, 0, 1)
	ZEND_ARG_INFO(0, input_token)
	ZEND_ARG_INFO(1, output_token)
	ZEND_ARG_INFO(1, src_name)
	ZEND_ARG_INFO(1, ret_flags)
	ZEND_ARG_INFO(1, time_rec)
	ZEND_ARG_OBJ_INFO(0, deleg, KRB5CCache, 0)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(krb5_GSSAPIContext_getMic, 0, 0, 1)
	ZEND_ARG_INFO(0, message)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(krb5_GSSAPIContext_verifyMicArgs, 0, 0, 2)
	ZEND_ARG_INFO(0, message)
	ZEND_ARG_INFO(0, mic)
ZEND_END_ARG_INFO()


ZEND_BEGIN_ARG_INFO_EX(krb5_GSSAPIContext_wrapArgs, 0, 0, 2)
	ZEND_ARG_INFO(0, input)
	ZEND_ARG_INFO(1, output)
	ZEND_ARG_INFO(0, encrypt)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(krb5_GSSAPIContext_unwrapArgs, 0, 0, 2)
	ZEND_ARG_INFO(0, input)
	ZEND_ARG_INFO(1, output)
ZEND_END_ARG_INFO()


PHP_METHOD(GSSAPIContext, registerAcceptorIdentity);
PHP_METHOD(GSSAPIContext, acquireCredentials);
PHP_METHOD(GSSAPIContext, inquireCredentials);
PHP_METHOD(GSSAPIContext, initSecContext);
PHP_METHOD(GSSAPIContext, acceptSecContext);
PHP_METHOD(GSSAPIContext, getMic);
PHP_METHOD(GSSAPIContext, verifyMic);
PHP_METHOD(GSSAPIContext, wrap);
PHP_METHOD(GSSAPIContext, unwrap);
PHP_METHOD(GSSAPIContext, getTimeRemaining);

static zend_function_entry krb5_gssapi_context_functions[] = {
	PHP_ME(GSSAPIContext, registerAcceptorIdentity, krb5_GSSAPIContext_registerAcceptorIdentity, ZEND_ACC_PUBLIC)
	PHP_ME(GSSAPIContext, acquireCredentials,       krb5_GSSAPIContext_acquireCredentials,       ZEND_ACC_PUBLIC)
	PHP_ME(GSSAPIContext, inquireCredentials,       krb5_GSSAPIContext_none,                     ZEND_ACC_PUBLIC)
	PHP_ME(GSSAPIContext, initSecContext,           krb5_GSSAPIContext_initSecContextArgs,       ZEND_ACC_PUBLIC)
	PHP_ME(GSSAPIContext, acceptSecContext,         krb5_GSSAPIContext_acceptSecContextArgs,     ZEND_ACC_PUBLIC)
	PHP_ME(GSSAPIContext, getMic,                   krb5_GSSAPIContext_getMic,                   ZEND_ACC_PUBLIC)
	PHP_ME(GSSAPIContext, verifyMic,                krb5_GSSAPIContext_verifyMicArgs,            ZEND_ACC_PUBLIC)
	PHP_ME(GSSAPIContext, wrap,                     krb5_GSSAPIContext_wrapArgs,                 ZEND_ACC_PUBLIC)
	PHP_ME(GSSAPIContext, unwrap,                   krb5_GSSAPIContext_unwrapArgs,               ZEND_ACC_PUBLIC)
	PHP_ME(GSSAPIContext, getTimeRemaining,         krb5_GSSAPIContext_none,                     ZEND_ACC_PUBLIC)
	PHP_FE_END
};

zend_object_handlers krb5_gssapi_context_handlers;

#ifdef ZTS
MUTEX_T gssapi_mutex;
#endif

/* Helper functions */

#define ASSERT_GSS_SUCCESS(status,minor_status,retval) if(GSS_ERROR(status)) { \
	php_krb5_gssapi_handle_error(status, minor_status TSRMLS_CC); \
	RETURN_FALSE; \
}

/* {{{ */
void php_krb5_gssapi_handle_error(OM_uint32 major, OM_uint32 minor TSRMLS_DC)
{
	OM_uint32 error_context = 0;
	OM_uint32 minor_status = 0;
	gss_buffer_desc error_buffer;

	gss_display_status (&minor_status, major, GSS_C_GSS_CODE,
					GSS_C_NO_OID, &error_context, &error_buffer);


	while(error_context) {
		php_error_docref(NULL TSRMLS_CC, E_WARNING, "%s (%ld,%ld)", (char*) error_buffer.value, (unsigned long int) major, (unsigned long int)minor);
		gss_release_buffer(&minor_status, &error_buffer);
		gss_display_status (&minor_status, major, GSS_C_GSS_CODE,
				GSS_C_NO_OID, &error_context, &error_buffer);
	}
	php_error_docref(NULL TSRMLS_CC, E_WARNING, "%s (%ld,%ld)", (char*) error_buffer.value,  (unsigned long int) major,  (unsigned long int)minor);
	gss_release_buffer(&minor_status, &error_buffer);

	if(minor) {
		php_error_docref(NULL TSRMLS_CC, E_WARNING, "GSSAPI mechanism error #%ld",  (unsigned long int) minor);
		gss_display_status (&minor_status, minor, GSS_C_MECH_CODE,
					GSS_C_NO_OID, &error_context, &error_buffer);

		while(error_context) {
			php_error_docref(NULL TSRMLS_CC, E_WARNING, "%s", (char*) error_buffer.value);
			gss_release_buffer(&minor_status, &error_buffer);

			gss_display_status (&minor_status, minor_status, GSS_C_MECH_CODE,
                                                GSS_C_NO_OID, &error_context, &error_buffer);
		}
		php_error_docref(NULL TSRMLS_CC, E_WARNING, "%s (%ld)", (char*)  error_buffer.value,  (unsigned long int) minor);
		gss_release_buffer(&minor_status, &error_buffer);
	}
}
/* }}} */

/* Setup functions */

/* {{{ */
#if PHP_MAJOR_VERSION < 7
void php_krb5_gssapi_context_object_dtor(void *obj, zend_object_handle handle TSRMLS_DC)
{
	OM_uint32 minor_status = 0;
	krb5_gssapi_context_object *object = (krb5_gssapi_context_object*)obj;
	OBJECT_STD_DTOR(object->std);


	if(object->creds != GSS_C_NO_CREDENTIAL) {
		gss_release_cred(&minor_status, &object->creds);
	}

	if(object->context != GSS_C_NO_CONTEXT) {
		gss_delete_sec_context(&minor_status, &object->context,  GSS_C_NO_BUFFER);
	}

	efree(object);
}
#else
void php_krb5_gssapi_context_object_free(zend_object *obj TSRMLS_DC) {
	OM_uint32 minor_status = 0;
	krb5_gssapi_context_object *object = (krb5_gssapi_context_object*)((char *)obj - XtOffsetOf(krb5_gssapi_context_object, std));
	
	if(object->creds != GSS_C_NO_CREDENTIAL) {
		gss_release_cred(&minor_status, &object->creds);
	}

	if(object->context != GSS_C_NO_CONTEXT) {
		gss_delete_sec_context(&minor_status, &object->context,  GSS_C_NO_BUFFER);
	}
	zend_object_std_dtor(obj);
}
#endif
/* }}} */


/* {{{ */
#if PHP_MAJOR_VERSION < 7
zend_object_value php_krb5_gssapi_context_object_new(zend_class_entry *ce TSRMLS_DC)
{
	zend_object_value retval;
	krb5_gssapi_context_object *object;

	object = emalloc(sizeof(krb5_gssapi_context_object));

	object->context = GSS_C_NO_CONTEXT;
	object->creds = GSS_C_NO_CREDENTIAL;

	INIT_STD_OBJECT(object->std, ce);

#if PHP_VERSION_ID < 50399
	zend_hash_copy(object->std.properties, &ce->default_properties,
	        		(copy_ctor_func_t) zval_add_ref, NULL,
					sizeof(zval*));
#else
	object_properties_init(&(object->std), ce);
#endif

	retval.handle = zend_objects_store_put(object, php_krb5_gssapi_context_object_dtor, NULL, NULL TSRMLS_CC);

	retval.handlers = &krb5_gssapi_context_handlers;
	return retval;
}
#else
zend_object *php_krb5_gssapi_context_object_new(zend_class_entry *ce TSRMLS_DC) {
	krb5_gssapi_context_object *object;
	object = ecalloc(1, sizeof(krb5_gssapi_context_object) + zend_object_properties_size(ce));

	object->context = GSS_C_NO_CONTEXT;
	object->creds = GSS_C_NO_CREDENTIAL;

	zend_object_std_init(&object->std, ce TSRMLS_CC);
	object_properties_init(&object->std, ce);
	object->std.handlers = &krb5_gssapi_context_handlers;
	return &object->std;
}
#endif
/* }}} */

/* {{{ */
int php_krb5_gssapi_register_classes(TSRMLS_D)
{
	zend_class_entry gssapi_context;


#ifdef ZTS
	/* initialize GSSAPI mutex */
	gssapi_mutex = tsrm_mutex_alloc();
	if(!gssapi_mutex) {
		php_error_docref(NULL TSRMLS_CC, E_ERROR, "Failed to initialize mutex in GSSAPI module");
		return FAILURE;
	}
#endif


	/* register classes */
	INIT_CLASS_ENTRY(gssapi_context, "GSSAPIContext", krb5_gssapi_context_functions);
	krb5_ce_gssapi_context = zend_register_internal_class(&gssapi_context TSRMLS_CC);
	krb5_ce_gssapi_context->create_object = php_krb5_gssapi_context_object_new;

	memcpy(&krb5_gssapi_context_handlers, zend_get_std_object_handlers(), sizeof(zend_object_handlers));
#if PHP_MAJOR_VERSION >= 7
	krb5_gssapi_context_handlers.offset = XtOffsetOf(krb5_gssapi_context_object, std);
	krb5_gssapi_context_handlers.free_obj = php_krb5_gssapi_context_object_free;
#endif

	return SUCCESS;
}
/* }}} */

/* {{{ */
int php_krb5_gssapi_shutdown(TSRMLS_D)
{
#ifdef ZTS
	tsrm_mutex_free(gssapi_mutex);
#endif

	return SUCCESS;
}
/* }}} */


/* GSSAPI Methods */

/* {{{ proto void GSSAPIContext::registerAcceptorIdentity(string $keytab)
 */
PHP_METHOD(GSSAPIContext, registerAcceptorIdentity)
{
	char *keytab;
	strsize_t keytab_len = 0;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, ARG_PATH, &keytab, &keytab_len) == FAILURE) {
		RETURN_FALSE;
	}

	if(krb5_gss_register_acceptor_identity(keytab) != GSS_S_COMPLETE) {
		zend_throw_exception(NULL, "Failed to set acceptor identitiy", 0 TSRMLS_CC);
		return;
	}
}


#ifdef ZTS
#define LOCK_MUTEX \
	if(tsrm_mutex_lock(gssapi_mutex)) { \
		php_error_docref(NULL TSRMLS_CC,  E_ERROR, "Failed to obtain mutex lock in GSSAPI module");\
		return;\
	}
#define UNLOCK_MUTEX \
	if(tsrm_mutex_unlock(gssapi_mutex)) {\
		php_error_docref(NULL TSRMLS_CC,  E_ERROR, "Failed to release mutex lock in GSSAPI module");\
		return;\
	}
#else
#define LOCK_MUTEX
#define UNLOCK_MUTEX
#endif

#define STORE_CONTEXT(ccache, oldkrb5ccname, oldkrb5ktname) { \
	const char *ccnametmp = krb5_cc_get_name(ccache->ctx, ccache->cc); \
        const char *cctypetmp = krb5_cc_get_type(ccache->ctx, ccache->cc); \
\
	ccname = malloc(strlen(ccnametmp) + strlen(cctypetmp) + 2); \
	memset(ccname,0, strlen(ccnametmp) + strlen(cctypetmp) + 2); \
\
	strcat(ccname, cctypetmp);\
	strcat(ccname, ":");\
	strcat(ccname, ccnametmp);\
	LOCK_MUTEX\
	/* save current KRB5CCNAME for resetting purposes */\
	oldkrb5ccname = getenv("KRB5CCNAME");\
	oldkrb5ktname = getenv("KRB5_KTNAME");\
\
	setenv("KRB5CCNAME", ccname, 1);\
	if(ccache->keytab) {\
		setenv("KRB5_KTNAME", ccache->keytab, 1);\
	}\
	free(ccname);\
}

#define RESTORE_CONTEXT(oldkrb5ccname, oldkrb5ktname) \
	/* reset KRB5CCNAME environment */\
	if(oldkrb5ccname) {\
		setenv("KRB5CCNAME", oldkrb5ccname, 1);\
	} else {\
		unsetenv("KRB5CCNAME");\
	}\
\
	if(oldkrb5ktname) {\
		setenv("KRB5_KTNAME", oldkrb5ktname, 1);\
	} else {\
		unsetenv("KRB5_KTNAME");\
	}\
	UNLOCK_MUTEX


/* {{{ proto void GSSAPIContext::acquireCredentials( KRB5CCache $ccache [, string $name = null [, int $type = GSS_C_BOTH ]])
   Obtain credentials for context establishment  */
PHP_METHOD(GSSAPIContext, acquireCredentials)
{
	OM_uint32           status = 0;
	OM_uint32           minor_status = 0;

	zval* zccache;
	krb5_ccache_object *ccache = NULL;
	char *ccname = NULL;
	
	zend_long type = GSS_C_BOTH;
	
	char *pname = NULL;
	gss_buffer_desc nametmp;
	gss_name_t name = GSS_C_NO_NAME;
	strsize_t namelen = 0;
	
	memset(&nametmp, 0, sizeof(nametmp));
	

	krb5_gssapi_context_object *context = KRB5_THIS_GSSAPI_CONTEXT;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "O|sl", &zccache, krb5_ce_ccache,
		&(nametmp.value), &namelen,
		&type) == FAILURE) {
		RETURN_FALSE;
	}
	if ( namelen > 0 ) {
		nametmp.length = namelen;
	}

	ccache = KRB5_CCACHE(zccache);

	if ( ccache->keytab == NULL ) {
		type = GSS_C_INITIATE;	
	}

	char *oldkrb5ccname = NULL, *oldkrb5ktname = NULL;
	STORE_CONTEXT(ccache, oldkrb5ccname, oldkrb5ktname);

	if(context->creds != GSS_C_NO_CREDENTIAL) {
		gss_release_cred(&minor_status, &(context->creds));
	}


	if(nametmp.length == 0) {
		krb5_principal ccprinc;
		krb5_error_code err = krb5_cc_get_principal(ccache->ctx, ccache->cc, &ccprinc);
		if ( err != 0 ) {
			RESTORE_CONTEXT(oldkrb5ccname, oldkrb5ktname);
			zend_throw_exception(NULL, "Failed to locate default principal in ccache", 0 TSRMLS_CC);
			return;
		}

		krb5_unparse_name(ccache->ctx, ccprinc, &pname);
		nametmp.value = pname;
		nametmp.length = strlen(pname);
		krb5_free_principal(ccache->ctx, ccprinc);
	}

	
	if(nametmp.length != 0) { 
		status = gss_import_name(&minor_status, &nametmp, GSS_C_NO_OID, &name);

		if(GSS_ERROR(status)) {
			if ( pname != NULL ) {
				krb5_free_unparsed_name(ccache->ctx, pname);
			}
			RESTORE_CONTEXT(oldkrb5ccname, oldkrb5ktname);
			ASSERT_GSS_SUCCESS(status,minor_status,);
		}
	}


	if ( pname != NULL ) {
		krb5_free_unparsed_name(ccache->ctx, pname);
	}

	status =  gss_acquire_cred (
	     &minor_status,
	     name,
	     GSS_C_INDEFINITE,
	     GSS_C_NO_OID_SET,
	     type,
	     &(context->creds),
	     NULL,
	     NULL);

	RESTORE_CONTEXT(oldkrb5ccname, oldkrb5ktname);
	ASSERT_GSS_SUCCESS(status,minor_status,);
} /* }}} */

/* {{{ proto array GSSAPIContext::inquireCredentials( )
   Get information about the credentials used for context establishment  */
PHP_METHOD(GSSAPIContext, inquireCredentials)
{
	OM_uint32           status = 0;
	OM_uint32           minor_status = 0;
	krb5_gssapi_context_object *context = KRB5_THIS_GSSAPI_CONTEXT;

	gss_name_t name = GSS_C_NO_NAME;
	OM_uint32 lifetime = 0;
	gss_cred_usage_t cred_usage = GSS_C_BOTH;
	gss_OID_set mechs = GSS_C_NO_OID_SET;
	gss_buffer_desc nametmp;
	memset(&nametmp, 0, sizeof(gss_buffer_desc));

	if (zend_parse_parameters_none() == FAILURE) {
		RETURN_FALSE;
	}

	status = gss_inquire_cred (
	     &minor_status,
	     context->creds,
	     &name,
	     &lifetime,
	     &cred_usage,
	     &mechs);

	ASSERT_GSS_SUCCESS(status,minor_status,);

	
	status = gss_display_name(&minor_status, name, &nametmp, NULL);
	ASSERT_GSS_SUCCESS(status,minor_status,);

	array_init(return_value);
	char *nameval = estrdup(nametmp.value);
	_add_assoc_string(return_value, "name", nameval);
	efree(nameval);

	add_assoc_long(return_value, "lifetime_remain", lifetime);

	if(cred_usage == GSS_C_BOTH) {
		_add_assoc_string(return_value, "cred_usage", "both");
	} else if(cred_usage == GSS_C_INITIATE) {
		_add_assoc_string(return_value, "cred_usage", "initiate");
	} else if(cred_usage == GSS_C_ACCEPT) {
		_add_assoc_string(return_value, "cred_usage", "accept");
	}

	status = gss_release_buffer(&minor_status, &nametmp);
	ASSERT_GSS_SUCCESS(status,minor_status,);

	status = gss_release_name(&minor_status, &name);
	ASSERT_GSS_SUCCESS(status,minor_status,);

	size_t i = 0;
	_DECLARE_ZVAL(mech_array);
	_ALLOC_INIT_ZVAL(mech_array);
	array_init(mech_array);

	for(i = 0; i < mechs->count; i++) {
		gss_OID_desc oid = *(mechs->elements + i);
		gss_buffer_desc tmp;
		status = gss_oid_to_str(&minor_status, &oid, &tmp);
		ASSERT_GSS_SUCCESS(status,minor_status,);

		_add_next_index_string(mech_array, tmp.value);

		status = gss_release_buffer(&minor_status, &tmp);
		ASSERT_GSS_SUCCESS(status,minor_status,);
	}

	add_assoc_zval(return_value, "mechs", mech_array);

	status = gss_release_oid_set(&minor_status, &mechs);
	ASSERT_GSS_SUCCESS(status,minor_status,);

} /* }}} */

/* {{{ proto boolean GSSAPIContext::initSecContext( string $target [, string $input_token [, int $req_flags [, int $time_eq [, string &$output_token [, int &$ret_flags [, int &$time-rec ]]]]]] )
   Initiate a security context */
PHP_METHOD(GSSAPIContext, initSecContext)
{
	OM_uint32  status = 0;
	OM_uint32  minor_status = 0;
	krb5_gssapi_context_object *context = KRB5_THIS_GSSAPI_CONTEXT;


	zend_long req_flags = 0;
	OM_uint32 ret_flags = 0;
	zend_long time_req = 0;
	OM_uint32 time_rec = 0;
	gss_buffer_desc tokenbuf;
	gss_buffer_desc inputtoken;
	gss_buffer_desc target;
	strsize_t target_len = 0;
	strsize_t inputtoken_len = 0;

	memset(&inputtoken, 0, sizeof(inputtoken));
	memset(&target, 0, sizeof(target));
	memset(&tokenbuf, 0, sizeof(tokenbuf));

	zval *ztokenbuf = NULL;
	zval *zret_flags = NULL;
	zval *ztime_rec = NULL;

#if PHP_MAJOR_VERSION >= 7
	const char *args = "s|sllz/z/z/";
#else
	
	const char *args = "s|sllzzz";
#endif

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, args,
								&(target.value), &target_len,
								&(inputtoken.value), &inputtoken_len,
								&req_flags,
								&time_req,
								&ztokenbuf,
								&zret_flags,
								&ztime_rec
								) == FAILURE) {
		return;
	}
	target.length = target_len;
	inputtoken.length = inputtoken_len;
	


	gss_name_t targetname;
	status = gss_import_name(&minor_status, &target,GSS_C_NO_OID, &targetname);
	ASSERT_GSS_SUCCESS(status,minor_status,);

	status =  gss_init_sec_context(
	     &minor_status,
	     context->creds,
	     &context->context,
	     targetname,
	     GSS_C_NO_OID,
	     req_flags,
	     time_req,
	     NULL,
	     &inputtoken,
	     NULL,
	     &tokenbuf,
	     &ret_flags,
	     &time_rec);

	if(status & GSS_S_CONTINUE_NEEDED) {
		RETVAL_FALSE;
	} else if(status) {
		gss_release_name(&minor_status, &targetname);
		gss_release_buffer(&minor_status, &tokenbuf);
		ASSERT_GSS_SUCCESS(status,minor_status,);
	} else {
		RETVAL_TRUE;
	}

	if(ztokenbuf) {
		zval_dtor(ztokenbuf);
		_ZVAL_STRINGL(ztokenbuf, tokenbuf.value, tokenbuf.length);
	}

	status = gss_release_buffer(&minor_status, &tokenbuf);
	ASSERT_GSS_SUCCESS(status,minor_status,);

	if(zret_flags) {
		zval_dtor(zret_flags);
		ZVAL_LONG(zret_flags, ret_flags);
	}

	if(ztime_rec) {
		zval_dtor(ztime_rec);
		ZVAL_LONG(ztime_rec, time_rec);
	}

	status = gss_release_name(&minor_status, &targetname);
	ASSERT_GSS_SUCCESS(status,minor_status,);


} /* }}} */

/* {{{ proto boolean GSSAPIContext::acceptSecContext( string $token [, string &$output_token [, string &$remote_principal [, int &$ret_flags [, int &$time_rec [, KRB5CCache deleg]]]]] )
   Establish/accept a remotely initiated security context */
PHP_METHOD(GSSAPIContext, acceptSecContext)
{
	OM_uint32           status = 0;
	OM_uint32           minor_status = 0;
	krb5_gssapi_context_object *context = KRB5_THIS_GSSAPI_CONTEXT;

	gss_buffer_desc inputtoken;
	gss_buffer_desc tokenbuf;
	gss_name_t src_name = GSS_C_NO_NAME;
	gss_cred_id_t deleg_creds = GSS_C_NO_CREDENTIAL;
	strsize_t inputtoken_len = 0;

	memset(&inputtoken, 0, sizeof(inputtoken));
	memset(&tokenbuf, 0, sizeof(tokenbuf));

	OM_uint32 ret_flags = 0;
	OM_uint32 time_rec = 0;

	zval* ztokenbuf = NULL;
	zval* zret_flags = NULL;
	zval* ztime_rec = NULL;
	zval* zsrc_name = NULL;
	zval* zdeleg_creds = NULL;

#if PHP_MAJOR_VERSION >= 7
	const char *args = "s|z/z/z/z/O";
#else
	
	const char *args = "s|zzzzO";
#endif

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, args,
			&(inputtoken.value), &inputtoken_len,
			&ztokenbuf,
			&zsrc_name,
			&zret_flags,
			&ztime_rec,
			&zdeleg_creds, krb5_ce_ccache) == FAILURE) {
		return;
	}

	inputtoken.length = inputtoken_len;

	status =  gss_accept_sec_context (
			&minor_status,
			&context->context,
			context->creds,
			&inputtoken,
			GSS_C_NO_CHANNEL_BINDINGS,
			&src_name,
			NULL,
			&tokenbuf,
			&ret_flags,
			&time_rec,
			&deleg_creds);

	 if(status & GSS_S_CONTINUE_NEEDED) {
		 RETVAL_FALSE;
	 } else if(GSS_ERROR(status)) {
		 OM_uint32 tmpstat = 0;
		 gss_release_name(&tmpstat, &src_name);
		 gss_release_buffer(&tmpstat, &tokenbuf);
		 RETVAL_FALSE;
		 ASSERT_GSS_SUCCESS(status,minor_status,);
	 } else {
		 RETVAL_TRUE;
	 }

	 if(ztokenbuf) {
		 zval_dtor(ztokenbuf);
		 _ZVAL_STRINGL(ztokenbuf, tokenbuf.value, tokenbuf.length);
	 }

	 status = gss_release_buffer(&minor_status, &tokenbuf);
	 ASSERT_GSS_SUCCESS(status,minor_status,);

	 if(zsrc_name) {
		 gss_buffer_desc nametmp;
		 status = gss_display_name(&minor_status, src_name, &nametmp, NULL);
		 ASSERT_GSS_SUCCESS(status,minor_status,);
		 zval_dtor(zsrc_name);
		 _ZVAL_STRINGL(zsrc_name, nametmp.value, nametmp.length);
		 status = gss_release_buffer(&minor_status, &nametmp);
		 ASSERT_GSS_SUCCESS(status,minor_status,);
	 }

	 if(zret_flags) {
		 zval_dtor(zret_flags);
		 ZVAL_LONG(zret_flags, ret_flags);
	 }

	 if(ztime_rec) {
		 zval_dtor(ztime_rec);
		 ZVAL_LONG(ztime_rec, time_rec);
	 }

	 if(zdeleg_creds && deleg_creds != GSS_C_NO_CREDENTIAL) {
		 krb5_ccache_object *deleg_ccache = KRB5_CCACHE(zdeleg_creds);
		 krb5_error_code retval = 0;
		 krb5_principal princ;
		 
		 if(!deleg_ccache) {
			 zend_throw_exception(NULL, "Invalid KRB5CCache object given", 0 TSRMLS_CC);
			 RETURN_FALSE;
		 }
		 
		 /* use principal name for ccache initialization */
		 gss_buffer_desc nametmp;
		 status = gss_display_name(&minor_status, src_name, &nametmp, NULL);
		 ASSERT_GSS_SUCCESS(status,minor_status,);
		 
		 if((retval = krb5_parse_name(deleg_ccache->ctx, nametmp.value, &princ))) {
			 php_krb5_display_error(deleg_ccache->ctx, retval,  "Failed to parse principal name (%s)" TSRMLS_CC);
			 RETURN_FALSE;
		 }
		 
		 if((retval = krb5_cc_initialize(deleg_ccache->ctx, deleg_ccache->cc, princ))) {
		 		krb5_free_principal(deleg_ccache->ctx,princ);
		 		php_krb5_display_error(deleg_ccache->ctx, retval,  "Failed to initialize credential cache (%s)" TSRMLS_CC);
		 		RETURN_FALSE;
		 }

		 krb5_free_principal(deleg_ccache->ctx,princ);
		 /* copy credentials to ccache */ 
		 status = gss_krb5_copy_ccache(&minor_status, deleg_creds, deleg_ccache->cc);

		 if(GSS_ERROR(status)) {
			 php_krb5_gssapi_handle_error(status, minor_status TSRMLS_CC);
			 zend_throw_exception(NULL, "Failure while imporing delegated ticket", 0 TSRMLS_CC);
			 RETURN_FALSE;
		 }
	 }

	 status = gss_release_name(&minor_status, &src_name);
	 ASSERT_GSS_SUCCESS(status,minor_status,);

} /* }}} */

/* {{{ proto int GSSAPIContext::getTimeRemaining( )
   Returns the time in seconds the GSSAPI context will stay valid  */
PHP_METHOD(GSSAPIContext, getTimeRemaining)
{
	OM_uint32 status = 0;
	OM_uint32 minor_status = 0;
	OM_uint32 time_rec = 0;
	krb5_gssapi_context_object *context = KRB5_THIS_GSSAPI_CONTEXT;

	if (zend_parse_parameters_none() == FAILURE) {
		RETURN_FALSE;
	}
	if(context->context == GSS_C_NO_CONTEXT) {
		RETURN_LONG(0);
	}

	status = gss_context_time(&minor_status, context->context, &time_rec);

	ASSERT_GSS_SUCCESS(status,minor_status,);

	RETURN_LONG(time_rec);
} /* }}} */

/* {{{ proto string GSSAPIContext::getMic( string message )
   Calculates a MIC for the given message */
PHP_METHOD(GSSAPIContext, getMic)
{
	OM_uint32 status = 0;
	OM_uint32 minor_status = 0;
	gss_buffer_desc input;
	gss_buffer_desc output;
	krb5_gssapi_context_object *context = KRB5_THIS_GSSAPI_CONTEXT;
	strsize_t input_length = 0;

	memset(&input, 0 , sizeof(input));


	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "s",
			&(input.value), &input_length) == FAILURE) {
		return;
	}
	input.length = input_length;


	status = gss_get_mic (
	     &minor_status,
	     context->context,
	     GSS_C_QOP_DEFAULT,
	     &input,
	     &output);


	ASSERT_GSS_SUCCESS(status,minor_status,);

	_RETVAL_STRINGL(output.value, output.length);

	status = gss_release_buffer(&minor_status, &output);
	ASSERT_GSS_SUCCESS(status,minor_status,);
} /* }}} */

/* {{{ proto bool GSSAPIContext::verifyMic( string $input, string $mic)
   Verifies a given message against a MIC */
PHP_METHOD(GSSAPIContext, verifyMic)
{
	OM_uint32 status = 0;
	OM_uint32 minor_status = 0;
	gss_buffer_desc input;
	gss_buffer_desc mic;
	krb5_gssapi_context_object *context = KRB5_THIS_GSSAPI_CONTEXT;
	strsize_t input_length = 0;
	strsize_t mic_length = 0;

	memset(&input, 0 , sizeof(input));
	memset(&mic, 0 , sizeof(mic));


	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "ss",
			&(input.value), &input_length,
			&(mic.value), &mic_length) == FAILURE) {
		return;
	}
	input.length = input_length;
	mic.length = mic_length;

	status =  gss_verify_mic (
			&minor_status,
			context->context,
			&input,
			&mic,
			NULL);

	RETVAL_FALSE;

	ASSERT_GSS_SUCCESS(status,minor_status,);

	RETVAL_TRUE;
} /* }}} */

/* {{{ proto bool GSSAPIContext::wrap( string $input, string &$output [, bool $encrypt = false ])
   Attaches a MIC to an input message and possibly encrypts the message */
PHP_METHOD(GSSAPIContext, wrap)
{
	OM_uint32 status = 0;
	OM_uint32 minor_status = 0;
	gss_buffer_desc input;
	gss_buffer_desc output;
	zval *zoutput;
	zend_long encrypt = 0;
	krb5_gssapi_context_object *context = KRB5_THIS_GSSAPI_CONTEXT;
	strsize_t input_length = 0;

	memset(&input, 0 , sizeof(input));
	memset(&output, 0 , sizeof(output));

#if PHP_MAJOR_VERSION >= 7
	const char *args = "sz/|b";
#else
	const char *args = "sz|b";
#endif

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, args,
			&(input.value), &input_length,
			&zoutput,
			&encrypt) == FAILURE) {
		return;
	}
	input.length = input_length;

	RETVAL_FALSE;

	status = gss_wrap (
			&minor_status,
			context->context,
			encrypt,
			GSS_C_QOP_DEFAULT,
			&input,
			NULL,
			&output);

	ASSERT_GSS_SUCCESS(status,minor_status,);

	if(zoutput) {
		zval_dtor(zoutput);
		_ZVAL_STRINGL(zoutput, output.value, output.length);
	}

	RETVAL_TRUE;

	status = gss_release_buffer(&minor_status, &output);
	ASSERT_GSS_SUCCESS(status,minor_status,);
} /* }}} */

/* {{{ proto bool GSSAPIContext::unwrap( string $input, string &$output)
   Verifies an input token with an attached MIC and possibly decrypts the message */
PHP_METHOD(GSSAPIContext, unwrap)
{

	OM_uint32 status = 0;
	OM_uint32 minor_status = 0;
	gss_buffer_desc input;
	gss_buffer_desc output;
	zval *zoutput;
	krb5_gssapi_context_object *context = KRB5_THIS_GSSAPI_CONTEXT;
	strsize_t input_length = 0;

	memset(&input, 0 , sizeof(input));
	memset(&output, 0 , sizeof(output));

#if PHP_MAJOR_VERSION >= 7
	const char *args = "sz/";
#else
	const char *args = "sz";
#endif

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, args,
			&(input.value), &input_length,
			&zoutput) == FAILURE) {
		return;
	}
	input.length = input_length;

	RETVAL_FALSE;

	status =  gss_unwrap (
	     &minor_status,
	     context->context,
	     &input,
	     &output,
	     NULL,
	     NULL);

	ASSERT_GSS_SUCCESS(status,minor_status,);

	if(zoutput) {
		zval_dtor(zoutput);
		_ZVAL_STRINGL(zoutput, output.value, output.length);
	}

	RETVAL_TRUE;

	status = gss_release_buffer(&minor_status, &output);
	ASSERT_GSS_SUCCESS(status,minor_status,);
} /* }}} */
