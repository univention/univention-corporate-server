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

#include "php_krb5.h"
#include "php_krb5_kadm.h"
#include "compat.h"


zend_class_entry *krb5_ce_kadm5;
zend_class_entry *krb5_ce_kadm5_principal;
zend_class_entry *krb5_ce_kadm5_policy;
zend_class_entry *krb5_ce_kadm5_tldata;

zend_object_handlers krb5_kadm5_handlers;

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5__construct, 0, 0, 2)
	ZEND_ARG_INFO(0, principal)
	ZEND_ARG_INFO(0, credentials)
	ZEND_ARG_INFO(0, use_keytab)
	ZEND_ARG_ARRAY_INFO(0, config, 0)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5_getPrincipal, 0, 0, 1)
	ZEND_ARG_INFO(0, principal)
	ZEND_ARG_INFO(0, noload)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5_getPrincipals, 0, 0, 0)
	ZEND_ARG_INFO(0, filter)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5_createPrincipal, 0, 0, 1)
	ZEND_ARG_OBJ_INFO(0, principal, KADM5Principal, 0)
	ZEND_ARG_INFO(0, password)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5_getPolicy, 0, 0, 1)
	ZEND_ARG_INFO(0, policy)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5_createPolicy, 0, 0, 1)
	ZEND_ARG_OBJ_INFO(0, policy, KADM5Policy, 0)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5_getPolicies, 0, 0, 0)
	ZEND_ARG_INFO(0, filter)
ZEND_END_ARG_INFO()



static zend_function_entry krb5_kadm5_functions[] = {
	PHP_ME(KADM5, __construct,     arginfo_KADM5__construct,      ZEND_ACC_CTOR | ZEND_ACC_PUBLIC)
	PHP_ME(KADM5, getPrincipal,    arginfo_KADM5_getPrincipal,    ZEND_ACC_PUBLIC)
	PHP_ME(KADM5, getPrincipals,   arginfo_KADM5_getPrincipals,   ZEND_ACC_PUBLIC)
	PHP_ME(KADM5, createPrincipal, arginfo_KADM5_createPrincipal, ZEND_ACC_PUBLIC)
	PHP_ME(KADM5, getPolicy,       arginfo_KADM5_getPolicy,       ZEND_ACC_PUBLIC)
	PHP_ME(KADM5, createPolicy,    arginfo_KADM5_createPolicy,    ZEND_ACC_PUBLIC)
	PHP_ME(KADM5, getPolicies,     arginfo_KADM5_getPolicies,     ZEND_ACC_PUBLIC)
	PHP_FE_END
};

/* KADM5 ctor/dtor */

/* {{{ */
void php_krb5_free_kadm5_object(krb5_kadm5_object *obj) {
	if(obj) {
		kadm5_destroy(&obj->handle);
		if ( obj->config.realm != NULL ) {
			efree(obj->config.realm);
		}

		if ( obj->config.admin_server != NULL ) {
			efree(obj->config.admin_server);
		}

		krb5_free_context(obj->ctx);
		efree(obj);
	}
}
/* }}} */

/* {{{ */
#if PHP_MAJOR_VERSION < 7
static void php_krb5_kadm5_object_dtor(void *obj, zend_object_handle handle TSRMLS_DC)
{
	krb5_kadm5_object *object = (krb5_kadm5_object*)obj;
	zend_object_std_dtor(&(object->std) TSRMLS_CC);
	php_krb5_free_kadm5_object(object);
}
#else
static void php_krb5_kadm5_object_free(zend_object *obj TSRMLS_DC)
{
	krb5_kadm5_object *object = (krb5_kadm5_object*)((char *)obj - XtOffsetOf(krb5_kadm5_object, std));
	kadm5_destroy(&object->handle);
	if ( object->config.realm != NULL ) {
		efree(object->config.realm);
	}

	if ( object->config.admin_server != NULL ) {
		efree(object->config.admin_server);
	}
	if ( object->ctx ) {
		krb5_free_context(object->ctx);
		object->ctx = NULL;
	}
	zend_object_std_dtor(obj);
}
#endif
/* }}} */

/* {{{ */
#if PHP_MAJOR_VERSION < 7
zend_object_value php_krb5_kadm5_object_new(zend_class_entry *ce TSRMLS_DC)
{
	zend_object_value retval;
	krb5_kadm5_object *object;

	object = emalloc(sizeof(krb5_kadm5_object));
	memset(&object->config, 0, sizeof (kadm5_config_params));

	zend_object_std_init(&(object->std), ce TSRMLS_CC);

#if PHP_VERSION_ID < 50399
	zend_hash_copy(object->std.properties, &ce->default_properties,
					(copy_ctor_func_t) zval_add_ref, NULL,
					sizeof(zval*));
#else
	object_properties_init(&(object->std), ce);
#endif

	retval.handle = zend_objects_store_put(object, php_krb5_kadm5_object_dtor, NULL, NULL TSRMLS_CC);

	retval.handlers = &krb5_kadm5_handlers;
	return retval;
}
#else
zend_object* php_krb5_kadm5_object_new(zend_class_entry *ce TSRMLS_DC)
{
	krb5_kadm5_object *object = ecalloc(1, sizeof(krb5_kadm5_object) + zend_object_properties_size(ce));
	zend_object_std_init(&object->std, ce TSRMLS_CC);
	object_properties_init(&object->std, ce);
	object->std.handlers = &krb5_kadm5_handlers;
	return &object->std;
}
#endif
/* }}} */

/* Register classes */
/* {{{ */
int php_krb5_kadm5_register_classes(TSRMLS_D) {
	zend_class_entry kadm5;

	/** register KADM5 **/
	INIT_CLASS_ENTRY(kadm5, "KADM5", krb5_kadm5_functions);
	krb5_ce_kadm5 = zend_register_internal_class(&kadm5 TSRMLS_CC);
	krb5_ce_kadm5->create_object = php_krb5_kadm5_object_new;
	memcpy(&krb5_kadm5_handlers, zend_get_std_object_handlers(), sizeof(zend_object_handlers));
#if PHP_MAJOR_VERSION >= 7
	krb5_kadm5_handlers.offset = XtOffsetOf(krb5_kadm5_object, std);
	krb5_kadm5_handlers.free_obj = php_krb5_kadm5_object_free;
#endif

	/** register KADM5Principal **/
	php_krb5_register_kadm5_principal(TSRMLS_C);

	/** register KADM5Policy **/
	php_krb5_register_kadm5_policy(TSRMLS_C);

	/** register KADM5TLData **/
	php_krb5_register_kadm5_tldata(TSRMLS_C);

	return SUCCESS;
}
/* }}} */

static int php_krb5_kadm_parse_config(kadm5_config_params *kadm_params, zval *config TSRMLS_DC) {
	int retval = 0;
	zval *tmp = NULL;

	if (Z_TYPE_P(config) != IS_ARRAY) {
		return KRB5KRB_ERR_GENERIC;
	}

	/* realm */
	tmp = zend_compat_hash_find(HASH_OF(config), "realm", sizeof("realm"));
	if ( tmp != NULL ) {
		zend_string *realm = zval_get_string(tmp TSRMLS_CC);
		if ((kadm_params->realm = emalloc(1+realm->len))) {
			strncpy(kadm_params->realm, realm->val, realm->len);
			kadm_params->realm[realm->len] = '\0';
		}
		zend_string_release(realm);
		kadm_params->mask |= KADM5_CONFIG_REALM;
	}

	/* admin_server */
	tmp = zend_compat_hash_find(HASH_OF(config), "admin_server", sizeof("admin_server"));
	if (tmp != NULL) {
		zend_string *admin_server = zval_get_string(tmp TSRMLS_CC);
		if ((kadm_params->admin_server = emalloc(1+admin_server->len))) {
			strncpy(kadm_params->admin_server, admin_server->val, admin_server->len);
			kadm_params->admin_server[admin_server->len] = '\0';
                }
		zend_string_release(admin_server);
		kadm_params->mask |= KADM5_CONFIG_ADMIN_SERVER;
	}

	/* admin_port */
	tmp = zend_compat_hash_find(HASH_OF(config), "kadmind_port", sizeof("kadmind_port"));
	if (tmp != NULL) {
		kadm_params->kadmind_port = zval_get_long(tmp TSRMLS_CC);
		kadm_params->mask |= KADM5_CONFIG_KADMIND_PORT;
	}

	return retval;
}

/* {{{ proto KADM5::__construct(string $principal, string $credentials [, bool $use_keytab=0 [, array $config]])
	Initialize a connection with the KADM server using the given credentials */
PHP_METHOD(KADM5, __construct)
{
	kadm5_ret_t retval;

	char *sprinc;
	strsize_t sprinc_len;

	char *spass = NULL;
	strsize_t spass_len;

	zend_bool use_keytab = 0;

	zval* config = NULL;
	krb5_kadm5_object *obj;

	KRB5_SET_ERROR_HANDLING(EH_THROW);
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "ss|ba", &sprinc, &sprinc_len,
					&spass, &spass_len,
					&use_keytab, &config) == FAILURE) {
		RETURN_FALSE;
	}
	KRB5_SET_ERROR_HANDLING(EH_NORMAL);

	if(strlen(spass) == 0) {
		zend_throw_exception(NULL, "You may not specify an empty password or keytab", 0 TSRMLS_CC);
		RETURN_FALSE;
	}

	obj = KRB5_THIS_KADM;


	if (config != NULL && php_krb5_kadm_parse_config(&(obj->config), config TSRMLS_CC)) {
		zend_throw_exception(NULL, "Failed to parse kadmin config", 0 TSRMLS_CC);
		RETURN_FALSE;
	}

	if(krb5_init_context(&obj->ctx)) {
		zend_throw_exception(NULL, "Failed to initialize kerberos library", 0 TSRMLS_CC);
		RETURN_FALSE;
	}

		
	if(!use_keytab) {
 		retval = kadm5_init_with_password(obj->ctx, sprinc, spass, KADM5_ADMIN_SERVICE, &obj->config, 
 						KADM5_STRUCT_VERSION, KADM5_API_VERSION_3, NULL, &obj->handle);
 	} else {

		if (strlen(spass) != spass_len) {
			zend_throw_exception(NULL, "Invalid keytab path", 0 TSRMLS_CC);
			krb5_free_context(obj->ctx);
			obj->ctx = NULL;
			RETURN_FALSE;
		}
#if PHP_VERSION_ID < 50399
  		if((PG(safe_mode) && !php_checkuid(spass, NULL, CHECKUID_CHECK_FILE_AND_DIR)) ||
  			php_check_open_basedir(spass TSRMLS_CC)) {
			krb5_free_context(obj->ctx);
			obj->ctx = NULL;
  			RETURN_FALSE;
  		}
#else
  		if( php_check_open_basedir(spass TSRMLS_CC)) {
			krb5_free_context(obj->ctx);
			obj->ctx = NULL;
  			RETURN_FALSE;
  		}
#endif

 		retval = kadm5_init_with_skey(obj->ctx,sprinc, spass, KADM5_ADMIN_SERVICE, &obj->config, 
 						KADM5_STRUCT_VERSION, KADM5_API_VERSION_3, NULL, &obj->handle);
	}

	if(retval != KADM5_OK) {
		const char* errmsg = krb5_get_error_message(obj->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(obj->ctx, errmsg);
		krb5_free_context(obj->ctx);
		obj->ctx = NULL;
		RETURN_FALSE;
	}

	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5::getPrinicipal(string $principal [, boolean $noload ])
	Fetch a principal entry by name */
PHP_METHOD(KADM5, getPrincipal)
{
	

	zval *sprinc = NULL;
	zend_bool noload = FALSE;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "z|b", &sprinc, &noload) == FAILURE) {
		RETURN_FALSE;
	}

	object_init_ex(return_value, krb5_ce_kadm5_principal);

#if PHP_MAJOR_VERSION < 7
	zval *dummy_retval, *ctor, *znoload;
	zval *args[3];
	MAKE_STD_ZVAL(ctor);
	ZVAL_STRING(ctor, "__construct",1);
	MAKE_STD_ZVAL(znoload);
	ZVAL_BOOL(znoload, noload);


	args[0] = sprinc;
	args[1] = getThis();
	args[2] = znoload;

	MAKE_STD_ZVAL(dummy_retval);
	if(call_user_function(&krb5_ce_kadm5_principal->function_table,
							&return_value, ctor, dummy_retval, 3,
							args TSRMLS_CC) == FAILURE) {
		zval_dtor(ctor);
		zval_dtor(dummy_retval);
		zend_throw_exception(NULL, "Failed to instantiate KADM5Principal object", 0 TSRMLS_CC);
	}

	zval_ptr_dtor(&ctor);
	zval_ptr_dtor(&dummy_retval);
	zval_ptr_dtor(&znoload);
#else
	zval ctor;
	zval args[3];
	zval dummy_retval;
	ZVAL_STRING(&ctor, "__construct");
	args[0] = *sprinc;
	args[1] = *getThis();
	ZVAL_BOOL(&args[2], noload);
	if(call_user_function(&krb5_ce_kadm5_principal->function_table, return_value, &ctor, &dummy_retval, 3, 
							args TSRMLS_CC) == FAILURE) {	
		zval_dtor(&ctor);
		zval_dtor(&dummy_retval);
		zval_dtor(&args[2]);
		zend_throw_exception(NULL, "Failed to instantiate KADM5Principal object", 0 TSRMLS_CC);
		return;
	}
	zval_dtor(&ctor);
	zval_dtor(&dummy_retval);
	zval_dtor(&args[2]);
#endif
} /* }}} */

/* {{{ proto array KADM5::getPrinicipals([string $filter])
	Fetch an array of all principals matching $filter */
PHP_METHOD(KADM5, getPrincipals)
{
	kadm5_ret_t retval;
	krb5_kadm5_object *obj;

	char *sexp = NULL;
	strsize_t sexp_len;

	char **princs;
	int princ_count;

	int i;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "|s", &sexp, &sexp_len) == FAILURE) {
		RETURN_FALSE;
	}

	obj = KRB5_THIS_KADM;
	retval = kadm5_get_principals(obj->handle, sexp, &princs, &princ_count);

	if(retval) {
		const char *errmsg = krb5_get_error_message(obj->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(obj->ctx, errmsg);
		return;
	}

	array_init(return_value);

	for(i = 0; i < princ_count; i++) {
		_add_next_index_string(return_value, princs[i]);
	}

	kadm5_free_name_list(obj->handle, princs, princ_count);
} /* }}} */

/* {{{ proto void KADM5::createPrincipal(KADM5Principal $principal [, string $password ])
	Creates a principal */
PHP_METHOD(KADM5, createPrincipal)
{
	kadm5_ret_t retval = 0;
	zval *princ = NULL, *princname = NULL;
	krb5_kadm5_principal_object *principal = NULL;
	krb5_kadm5_object *obj = NULL;


	char *pw = NULL;
	strsize_t pw_len = 0;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "O|s", &princ, krb5_ce_kadm5_principal, &pw, &pw_len) == FAILURE) {
		return;
	}

	if ( Z_ISNULL_P(princ) ) {
		zend_throw_exception(NULL, "Invalid principal object", 0 TSRMLS_CC);
		return;
	}

	principal = KRB5_KADM_PRINCIPAL(princ);
	obj = KRB5_THIS_KADM;

#if PHP_MAJOR_VERSION < 7
	princname = zend_read_property(krb5_ce_kadm5_principal, princ, "princname",
									sizeof("princname"),1 TSRMLS_CC);
#else
	princname = zend_read_property(krb5_ce_kadm5_principal, princ, "princname",
									sizeof("princname"),1, NULL TSRMLS_CC);
#endif
	if ( principal->data.principal ) {
		krb5_free_principal(obj->ctx, principal->data.principal);
	}

	zend_string *pnamestr = zval_get_string(princname TSRMLS_CC);
	if(krb5_parse_name(obj->ctx, pnamestr->val, &principal->data.principal)) {
		zend_string_release(pnamestr);
		zend_throw_exception(NULL, "Failed to parse principal name", 0 TSRMLS_CC);
		return;
	}
	zend_string_release(pnamestr);
	principal->update_mask |= KADM5_PRINCIPAL;
	principal->conn = obj;
	zend_update_property(krb5_ce_kadm5_principal, princ, "connection", sizeof("connection"), getThis() TSRMLS_CC);

	retval = kadm5_create_principal(obj->handle, &principal->data, principal->update_mask, pw);
	if(retval != KADM5_OK) {
		const char* errmsg =  krb5_get_error_message(obj->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(obj->ctx, errmsg);
		return;
	}


#if PHP_MAJOR_VERSION < 7
	zval *dummy_retval = NULL, *func = NULL;
	MAKE_STD_ZVAL(func);
	ZVAL_STRING(func, "load", 1);
	MAKE_STD_ZVAL(dummy_retval);
	if(call_user_function(&krb5_ce_kadm5_principal->function_table,
							&princ, func, dummy_retval, 0,
							NULL TSRMLS_CC) == FAILURE) {

		zval_ptr_dtor(&func);
		zval_ptr_dtor(&dummy_retval);

		zend_throw_exception(NULL, "Failed to update KADM5Principal object", 0 TSRMLS_CC);
		return;
	}

	zval_ptr_dtor(&func);
	zval_ptr_dtor(&dummy_retval);
#else
	zval func;
	zval dummy_retval;
	ZVAL_STRING(&func, "load");
	if(call_user_function(&krb5_ce_kadm5_principal->function_table, princ, &func, &dummy_retval, 0, 
							NULL TSRMLS_CC) == FAILURE) {	
		zval_dtor(&func);
		zval_dtor(&dummy_retval);
		zend_throw_exception(NULL, "Failed to update KADM5Principal object", 0 TSRMLS_CC);
		return;
	}
	zval_dtor(&func);
	zval_dtor(&dummy_retval);
#endif
}

/* {{{ proto KADM5Policy KADM5::getPolicy(string $policy)
	Fetches a policy */
PHP_METHOD(KADM5, getPolicy)
{
	

	zval *spolicy = NULL;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "z", &spolicy) == FAILURE) {
		return;
	}

	object_init_ex(return_value, krb5_ce_kadm5_policy);

#if PHP_MAJOR_VERSION < 7
	zval *dummy_retval, *ctor;
	zval *args[2];
	MAKE_STD_ZVAL(ctor);
	ZVAL_STRING(ctor, "__construct", 1);

	args[0] = spolicy;
	args[1] = getThis();

	MAKE_STD_ZVAL(dummy_retval);
	if(call_user_function(&krb5_ce_kadm5_policy->function_table,
							&return_value, ctor, dummy_retval, 2,
							args TSRMLS_CC) == FAILURE) {
		zval_dtor(ctor);
		zval_dtor(dummy_retval);
		zend_throw_exception(NULL, "Failed to instantiate KADM5Policy object", 0 TSRMLS_CC);
		return;
	}

	zval_ptr_dtor(&ctor);
	zval_ptr_dtor(&dummy_retval);
#else
	zval ctor;
	zval args[2];
	zval dummy_retval;
	ZVAL_STRING(&ctor, "__construct");
	args[0] = *spolicy;
	args[1] = *getThis();
	if(call_user_function(&krb5_ce_kadm5_policy->function_table, return_value, &ctor, &dummy_retval, 2, 
							args TSRMLS_CC) == FAILURE) {	
		zval_dtor(&ctor);
		zval_dtor(&dummy_retval);
		zend_throw_exception(NULL, "Failed to instantiate KADM5Policy object", 0 TSRMLS_CC);
		return;
	}
	zval_dtor(&ctor);
	zval_dtor(&dummy_retval);
#endif
} /* }}} */

/* {{{ proto void KADM5::createPolicy(KADM5Policy $policy)
	Creates a Policy */
PHP_METHOD(KADM5, createPolicy) {
	kadm5_ret_t retval;
	zval *zpolicy;
	krb5_kadm5_policy_object *policy;
	krb5_kadm5_object *obj;



	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "O", &zpolicy, krb5_ce_kadm5_policy) == FAILURE) {
		return;
	}

	policy = KRB5_KADM_POLICY(zpolicy);
	obj = KRB5_THIS_KADM;

	policy->update_mask |= KADM5_POLICY;
	policy->conn = obj;
	policy->data.policy = policy->policy;
	zend_update_property(krb5_ce_kadm5_policy, zpolicy, "connection", sizeof("connection"), getThis() TSRMLS_CC);

	retval = kadm5_create_policy(obj->handle, &policy->data, policy->update_mask);
	if(retval != KADM5_OK) {
		policy->data.policy = NULL;
		const char* errmsg = krb5_get_error_message(obj->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(obj->ctx, errmsg);
		return;
	}

	policy->data.policy = NULL;

#if PHP_MAJOR_VERSION < 7
	zval *dummy_retval, *func;
	MAKE_STD_ZVAL(func);
	ZVAL_STRING(func, "load", 1);
	MAKE_STD_ZVAL(dummy_retval);
	if(call_user_function(&krb5_ce_kadm5_policy->function_table,
							&zpolicy, func, dummy_retval, 0,
							NULL TSRMLS_CC) == FAILURE) {
		zval_ptr_dtor(&func);
		zval_ptr_dtor(&dummy_retval);
		zend_throw_exception(NULL, "Failed to update KADM5Policy object", 0 TSRMLS_CC);
		return;
	}

	zval_ptr_dtor(&func);
	zval_ptr_dtor(&dummy_retval);
#else
	zval func;
	zval dummy_retval;
	ZVAL_STRING(&func, "load");
	if(call_user_function(&krb5_ce_kadm5_policy->function_table, zpolicy, &func, &dummy_retval, 0, 
							NULL TSRMLS_CC) == FAILURE) {	
		zval_dtor(&func);
		zval_dtor(&dummy_retval);
		zend_throw_exception(NULL, "Failed to update KADM5Policy object", 0 TSRMLS_CC);
		return;
	}
	zval_dtor(&func);
	zval_dtor(&dummy_retval);
#endif
} /* }}} */

/* {{{ proto array KADM5::getPolicies([string $filter])
	Fetches all policies */
PHP_METHOD(KADM5, getPolicies)
{
	kadm5_ret_t retval;
	krb5_kadm5_object *obj;

	char *sexp = NULL;
	strsize_t sexp_len;

	char **policies;
	int pol_count;

	int i;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "|s", &sexp, &sexp_len) == FAILURE) {
		RETURN_FALSE;
	}

	obj = KRB5_THIS_KADM;
	retval = kadm5_get_policies(obj->handle, sexp, &policies, &pol_count);

	if(retval) {
		const char* errmsg =  krb5_get_error_message(obj->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(obj->ctx, errmsg);
		return;
	}

	array_init(return_value);

	for(i = 0; i < pol_count; i++) {
		_add_next_index_string(return_value, policies[i]);
	}

	kadm5_free_name_list(obj->handle, policies, pol_count);
} /* }}} */
