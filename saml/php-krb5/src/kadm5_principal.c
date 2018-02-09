/**
* Copyright (c) 2007 Moritz Bechler
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

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Principal_none, 0, 0, 0)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Principal__construct, 0, 0, 1)
	ZEND_ARG_INFO(0, principal)
	ZEND_ARG_OBJ_INFO(0, connection, KADM5, 0)
	ZEND_ARG_INFO(0, noload)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Principal_changePassword, 0, 0, 1)
	ZEND_ARG_INFO(0, password)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Principal_rename, 0, 0, 1)
	ZEND_ARG_INFO(0, dst_name)
	ZEND_ARG_INFO(0, dst_pw)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Principal_time, 0, 0, 1)
	ZEND_ARG_INFO(0, time)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Principal_setKeyVNO, 0, 0, 1)
	ZEND_ARG_INFO(0, kvno)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Principal_setAttributes, 0, 0, 1)
	ZEND_ARG_INFO(0, attrs)
ZEND_END_ARG_INFO()


ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Principal_setPolicy, 0, 0, 1)
	ZEND_ARG_INFO(0, policy)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Principal_setTLData, 0, 0, 1)
	ZEND_ARG_INFO(0, tldata)
ZEND_END_ARG_INFO()

static zend_function_entry krb5_kadm5_principal_functions[] = {
	PHP_ME(KADM5Principal, __construct,             arginfo_KADM5Principal__construct,     ZEND_ACC_PUBLIC | ZEND_ACC_CTOR)
	PHP_ME(KADM5Principal, load,                    arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, save,                    arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, delete,                  arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, rename,                  arginfo_KADM5Principal_rename,         ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, changePassword,          arginfo_KADM5Principal_changePassword, ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getPropertyArray,        arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getName,                 arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getExpiryTime,           arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, setExpiryTime,           arginfo_KADM5Principal_time,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getLastPasswordChange,   arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getPasswordExpiryTime,   arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, setPasswordExpiryTime,   arginfo_KADM5Principal_time,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getMaxTicketLifetime,    arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, setMaxTicketLifetime,    arginfo_KADM5Principal_time,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getMaxRenewableLifetime, arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, setMaxRenewableLifetime, arginfo_KADM5Principal_time,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getLastModifier,         arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getLastModificationDate, arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getKeyVNO,               arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, setKeyVNO,               arginfo_KADM5Principal_setKeyVNO,      ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getMasterKeyVNO,         arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, setAttributes,           arginfo_KADM5Principal_setAttributes,  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getAttributes,           arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getAuxAttributes,        arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getPolicy,               arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, setPolicy,               arginfo_KADM5Principal_setPolicy,      ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, clearPolicy,             arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getLastSuccess,          arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getLastFailed,           arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getFailedAuthCount,      arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, resetFailedAuthCount,    arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, setTLData,               arginfo_KADM5Principal_setTLData,      ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Principal, getTLData,               arginfo_KADM5Principal_none,           ZEND_ACC_PUBLIC)
	PHP_FE_END
};

zend_object_handlers krb5_kadm5_principal_handlers;

/* KADM5Principal ctor/dtor */
#if PHP_MAJOR_VERSION < 7
static void php_krb5_kadm5_principal_object_dtor(void *obj, zend_object_handle handle TSRMLS_DC)
{
	krb5_kadm5_principal_object *object = (krb5_kadm5_principal_object*)obj;
	
	krb5_kadm5_object *conn = object->conn;
	if(conn) {
		kadm5_free_principal_ent(conn->handle, &object->data);
	}

	zend_object_std_dtor(&(object->std) TSRMLS_CC);
	efree(object);
}
#else
static void php_krb5_kadm5_principal_object_free(zend_object *obj TSRMLS_DC)
{
	krb5_kadm5_principal_object *object = (krb5_kadm5_principal_object*)((char *)obj - XtOffsetOf(krb5_kadm5_principal_object, std));
	krb5_kadm5_object *conn = object->conn;
	if(conn) {
		kadm5_free_principal_ent(conn->handle, &object->data);

	}
	zend_object_std_dtor(obj);
}
#endif

int php_krb5_register_kadm5_principal(TSRMLS_D) {
	zend_class_entry kadm5_principal;
	INIT_CLASS_ENTRY(kadm5_principal, "KADM5Principal", krb5_kadm5_principal_functions);
	krb5_ce_kadm5_principal = zend_register_internal_class(&kadm5_principal TSRMLS_CC);
	krb5_ce_kadm5_principal->create_object = php_krb5_kadm5_principal_object_new;
	memcpy(&krb5_kadm5_principal_handlers, zend_get_std_object_handlers(), sizeof(zend_object_handlers));
#if PHP_MAJOR_VERSION >= 7
	krb5_kadm5_principal_handlers.offset = XtOffsetOf(krb5_kadm5_principal_object, std);
	krb5_kadm5_principal_handlers.free_obj = php_krb5_kadm5_principal_object_free;
#endif
	return SUCCESS;
}

#if PHP_MAJOR_VERSION < 7
zend_object_value php_krb5_kadm5_principal_object_new(zend_class_entry *ce TSRMLS_DC)
{
	zend_object_value retval;
	krb5_kadm5_principal_object *object;
	extern zend_object_handlers krb5_kadm5_principal_handlers;

	object = emalloc(sizeof(krb5_kadm5_principal_object));

	memset(&object->data, 0, sizeof(kadm5_principal_ent_rec));
	object->loaded = FALSE;
	object->update_mask = 0;
	object->conn = NULL;

	zend_object_std_init(&(object->std), ce TSRMLS_CC);

#if PHP_VERSION_ID < 50399
	zend_hash_copy(object->std.properties, &ce->default_properties,
					(copy_ctor_func_t) zval_add_ref, NULL, 
					sizeof(zval*));
#else
	object_properties_init(&(object->std), ce);
#endif

	retval.handle = zend_objects_store_put(object, php_krb5_kadm5_principal_object_dtor, NULL, NULL TSRMLS_CC);
	retval.handlers = &krb5_kadm5_principal_handlers;
	return retval;
}
#else
zend_object* php_krb5_kadm5_principal_object_new(zend_class_entry *ce TSRMLS_DC) {
	krb5_kadm5_principal_object *object = ecalloc(1, sizeof(krb5_kadm5_principal_object) + zend_object_properties_size(ce));
	zend_object_std_init(&object->std, ce TSRMLS_CC);
	object_properties_init(&object->std, ce);
	object->std.handlers = &krb5_kadm5_principal_handlers;
	return &object->std;
}
#endif

/* {{{ proto KADM5Principal KADM5Principal::__construct(string $principal [, KADM5 $connection [, boolean $noload] ])
 */
PHP_METHOD(KADM5Principal, __construct)
{

	krb5_kadm5_principal_object *this = KRB5_THIS_KADM_PRINCIPAL;
	char *sprinc = NULL;
	strsize_t sprinc_len;

	zend_bool noload = FALSE;
	zval *obj = NULL;


	KRB5_SET_ERROR_HANDLING(EH_THROW);
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "s|Ob", &sprinc, &sprinc_len, &obj, krb5_ce_kadm5, &noload) == FAILURE) {
		RETURN_NULL();
	}
	KRB5_SET_ERROR_HANDLING(EH_NORMAL);

	zend_update_property_string(krb5_ce_kadm5_principal, getThis(), "princname", sizeof("princname"), sprinc TSRMLS_CC);

	if(obj && Z_TYPE_P(obj) == IS_OBJECT) {
		zend_update_property(krb5_ce_kadm5_principal, getThis(), "connection", sizeof("connection"), obj TSRMLS_CC);
		this->conn = KRB5_KADM(obj);

		if ( noload != TRUE ) {
#if PHP_MAJOR_VERSION < 7
			zval *dummy_retval, *func;
			MAKE_STD_ZVAL(func);
			ZVAL_STRING(func, "load", 1);
			MAKE_STD_ZVAL(dummy_retval);
			if(call_user_function(&krb5_ce_kadm5_principal->function_table, 
									&getThis(), func, dummy_retval, 0, 
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
			if(call_user_function(&krb5_ce_kadm5_policy->function_table, getThis(), &func, &dummy_retval, 0, 
									NULL TSRMLS_CC) == FAILURE) {	
				zval_dtor(&func);
				zval_dtor(&dummy_retval);
				zend_throw_exception(NULL, "Failed to update KADM5Policy object", 0 TSRMLS_CC);
				return;
			}
			zval_dtor(&func);
			zval_dtor(&dummy_retval);
#endif
		}
	}
}
/* }}} */


#if PHP_MAJOR_VERSION < 7
#define KRB5_KADM_PRINCIPAL_GET_CONNECTION zend_read_property(krb5_ce_kadm5_principal, getThis(), "connection", sizeof("connection"),1 TSRMLS_CC)
#else
#define KRB5_KADM_PRINCIPAL_GET_CONNECTION zend_read_property(krb5_ce_kadm5_principal, getThis(), "connection", sizeof("connection"),1, NULL TSRMLS_CC)
#endif

#if PHP_MAJOR_VERSION < 7
#define KRB5_KADM_PRINCIPAL_GET_PRINCNAME zend_read_property(krb5_ce_kadm5_principal, getThis(), "princname", sizeof("princname"),1 TSRMLS_CC)
#else
#define KRB5_KADM_PRINCIPAL_GET_PRINCNAME zend_read_property(krb5_ce_kadm5_principal, getThis(), "princname", sizeof("princname"),1, NULL TSRMLS_CC)
#endif

/* {{{ proto KADM5Principal KADM5Principal::load()
 */
PHP_METHOD(KADM5Principal, load)
{
	kadm5_ret_t retval;
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	krb5_kadm5_object *kadm5;
	zval *connobj = NULL;
	zval *princname = NULL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}

	connobj = KRB5_KADM_PRINCIPAL_GET_CONNECTION;
	princname = KRB5_KADM_PRINCIPAL_GET_PRINCNAME;

	if ( Z_ISNULL_P(connobj)) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}

	kadm5 = KRB5_KADM(connobj);
	if(!kadm5) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}

	if ( obj->data.principal ) {
		krb5_free_principal(kadm5->ctx, obj->data.principal);
		obj->data.principal = NULL;
	}

	zend_string *pnstr = zval_get_string(princname TSRMLS_CC);
	fprintf(stderr, "Loading %s\n", pnstr->val);
	if(krb5_parse_name(kadm5->ctx, pnstr->val, &obj->data.principal)) {
		zend_string_release(pnstr);
		zend_throw_exception(NULL, "Failed to parse principal name", 0 TSRMLS_CC);
		return;
	}
	zend_string_release(pnstr);

	retval = kadm5_get_principal(kadm5->handle, obj->data.principal, &obj->data, KADM5_PRINCIPAL_NORMAL_MASK | KADM5_TL_DATA);
	if(retval != KADM5_OK) {
		krb5_free_principal(kadm5->ctx, obj->data.principal);
		obj->data.principal = NULL;
		const char* errmsg = krb5_get_error_message(kadm5->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(kadm5->ctx, errmsg);
		return;
	}

	obj->loaded = TRUE;
	obj->update_mask = 0;
	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::save()
 */
PHP_METHOD(KADM5Principal, save)
{
	kadm5_ret_t retval;
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	krb5_kadm5_object *kadm5;
	zval *connobj = NULL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}


	connobj = KRB5_KADM_PRINCIPAL_GET_CONNECTION;
	if ( Z_ISNULL_P(connobj)) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}

	kadm5 = KRB5_KADM(connobj);
	if(!kadm5) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}

	if(obj->update_mask == 0) {
		RETURN_TRUE;
	}

	retval = kadm5_modify_principal(kadm5->handle, &obj->data, obj->update_mask);
	if(retval != KADM5_OK) {
		const char* errmsg = krb5_get_error_message(kadm5->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(kadm5->ctx, errmsg);
		return;
	}

	obj->update_mask = 0;

	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::changePassword(string $password)
 */
PHP_METHOD(KADM5Principal, changePassword)
{
	kadm5_ret_t retval;
	krb5_kadm5_object *kadm5 = NULL;
	zval *connobj = NULL;
	zval *princname = NULL;

	char *newpass = NULL;
	strsize_t newpass_len;

	krb5_principal princ;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "s", &newpass, &newpass_len) == FAILURE) {
		RETURN_FALSE;
	}

	connobj = KRB5_KADM_PRINCIPAL_GET_CONNECTION;
	princname = KRB5_KADM_PRINCIPAL_GET_PRINCNAME;


	if ( Z_ISNULL_P(connobj) ) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}

	kadm5 = KRB5_KADM(connobj);
	if(!kadm5) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}
   
   	zend_string *pnstr = zval_get_string(princname TSRMLS_CC);
	if(krb5_parse_name(kadm5->ctx, pnstr->val, &princ)) {
		zend_string_release(pnstr);
		zend_throw_exception(NULL, "Failed to parse principal name", 0 TSRMLS_CC);
		return;
	}
	zend_string_release(pnstr);

	retval = kadm5_chpass_principal(kadm5->handle, princ, newpass);
	krb5_free_principal(kadm5->ctx, princ);

	if(retval != KADM5_OK) {
		const char* errmsg = krb5_get_error_message(kadm5->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(kadm5->ctx, errmsg);
		return;
	}

	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::delete()
 */
PHP_METHOD(KADM5Principal, delete)
{
	kadm5_ret_t retval;
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	krb5_kadm5_object *kadm5;
	zval *connobj = NULL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}

	if ( ! obj->loaded ) {
		zend_throw_exception(NULL, "Object is not loaded", 0 TSRMLS_CC);
		return;
	}

	connobj = KRB5_KADM_PRINCIPAL_GET_CONNECTION;
	if ( Z_ISNULL_P(connobj) ) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}

	kadm5 = KRB5_KADM(connobj);
	if(!kadm5) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}


	retval = kadm5_delete_principal(kadm5->handle, obj->data.principal);
	if(retval != KADM5_OK) {
		const char* errmsg = krb5_get_error_message(kadm5->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(kadm5->ctx, errmsg);
		return;
	}
	obj->loaded = FALSE;

	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::rename(string $dst_name [, string $dst_pw ])
 */
PHP_METHOD(KADM5Principal, rename)
{
	kadm5_ret_t retval;
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	krb5_kadm5_object *kadm5;
	zval *connobj = NULL;
	char *dst_name = NULL, *dst_pw = NULL;
	strsize_t dst_name_len, dst_pw_len;
	krb5_principal dst_princ;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "s|s", &dst_name, &dst_name_len,
								&dst_pw, &dst_pw_len) == FAILURE) {
		RETURN_FALSE;
	}

	if ( ! obj->loaded ) {
		zend_throw_exception(NULL, "Object is not loaded", 0 TSRMLS_CC);
		return;
	}

	connobj = KRB5_KADM_PRINCIPAL_GET_CONNECTION;
	if ( Z_ISNULL_P(connobj)) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}
	kadm5 = KRB5_KADM(connobj);
	if(!kadm5) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}


	krb5_parse_name(kadm5->ctx, dst_name, &dst_princ);
	retval = kadm5_rename_principal(kadm5->handle, obj->data.principal, dst_princ);
	if(retval != KADM5_OK) {
		krb5_free_principal(kadm5->ctx, dst_princ);
		const char* errmsg = krb5_get_error_message(kadm5->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(kadm5->ctx, errmsg);
		return;
	}
	
	if(dst_pw) {
		retval = kadm5_chpass_principal(kadm5->handle, dst_princ, dst_pw);
		if(retval != KADM5_OK) {
			krb5_free_principal(kadm5->ctx, dst_princ);
			const char* errmsg = krb5_get_error_message(kadm5->ctx, (int)retval);
			zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
			krb5_free_error_message(kadm5->ctx, errmsg);
			return;
		}
	}

	retval = kadm5_get_principal(kadm5->handle, dst_princ, &obj->data, KADM5_PRINCIPAL_NORMAL_MASK);
	if(retval != KADM5_OK) {
		krb5_free_principal(kadm5->ctx, dst_princ);
		const char* errmsg = krb5_get_error_message(kadm5->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(kadm5->ctx, errmsg);
		return;
	}

	krb5_free_principal(kadm5->ctx, dst_princ);
}
/* }}} */

/** property accessors **/

/* {{{ proto array KADM5Principal::getPropertyArray()
 */
PHP_METHOD(KADM5Principal, getPropertyArray)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	krb5_kadm5_object *kadm5;
	zval *connobj = NULL;
	connobj = KRB5_KADM_PRINCIPAL_GET_CONNECTION;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}


	kadm5 = KRB5_KADM(connobj);
	if(!kadm5) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}

	array_init(return_value);

	char *tstring;
	if ( obj->data.principal != NULL ) {
		krb5_unparse_name(kadm5->ctx, obj->data.principal, &tstring);
		_add_assoc_string(return_value, "princname", tstring);
		krb5_free_unparsed_name(kadm5->ctx, tstring);
	} else {
		zend_string *val = zval_get_string(KRB5_KADM_PRINCIPAL_GET_PRINCNAME TSRMLS_CC);
		_add_assoc_string(return_value, "princname", val->val);
		zend_string_release(val);
	}



	add_assoc_long(return_value, "princ_expire_time", obj->data.princ_expire_time);
	add_assoc_long(return_value, "last_pwd_change", obj->data.last_pwd_change);
	add_assoc_long(return_value, "pw_expiration", obj->data.pw_expiration);
	add_assoc_long(return_value, "max_life", obj->data.max_life);
	
	if ( obj->data.mod_name ) {
		krb5_unparse_name(kadm5->ctx, obj->data.mod_name, &tstring);
		_add_assoc_string(return_value, "mod_name", tstring);
		krb5_free_unparsed_name(kadm5->ctx, tstring);
	}

	add_assoc_long(return_value, "mod_date", obj->data.mod_date);
	add_assoc_long(return_value, "attributes", obj->data.attributes);
	add_assoc_long(return_value, "kvno", obj->data.kvno);
	add_assoc_long(return_value, "mkvno", obj->data.mkvno);
	if(obj->data.policy) _add_assoc_string(return_value, "policy", obj->data.policy);
	add_assoc_long(return_value, "aux_attributes", obj->data.aux_attributes);
	add_assoc_long(return_value, "max_renewable_life", obj->data.max_renewable_life);
	add_assoc_long(return_value, "last_success", obj->data.last_success);
	add_assoc_long(return_value, "last_failed", obj->data.last_failed);
	add_assoc_long(return_value, "fail_auth_count", obj->data.fail_auth_count);

	if ( obj->data.n_tl_data  > 0 ) {
		zval *tldata = ecalloc(1, sizeof(zval));
		_ALLOC_INIT_ZVAL(tldata);
		array_init(tldata);
		php_krb5_kadm5_tldata_to_array(tldata, obj->data.tl_data, obj->data.n_tl_data TSRMLS_CC);
		add_assoc_zval(return_value, "tldata", tldata);
		//zval_ptr_dtor(tldata);
	}
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getName()
 */
PHP_METHOD(KADM5Principal, getName)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	
	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	if(obj->loaded) {
		char *princname;
		krb5_kadm5_object *kadm5;
		zval *connobj = NULL;

		connobj = KRB5_KADM_PRINCIPAL_GET_CONNECTION;
		if ( Z_ISNULL_P(connobj)) {
			zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
			return;
		}
		kadm5 = KRB5_KADM(connobj);
		if ( !kadm5 ) {
			zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
			return;
		}

		krb5_unparse_name(kadm5->ctx,obj->data.principal,&princname);
		_RETVAL_STRING(princname);
		krb5_free_unparsed_name(kadm5->ctx, princname);
	} else {
		zend_string *val = zval_get_string(KRB5_KADM_PRINCIPAL_GET_PRINCNAME TSRMLS_CC);
		_RETVAL_STRING(val->val);
		zend_string_release(val);
	}
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getExpiryTime()
 */
PHP_METHOD(KADM5Principal, getExpiryTime)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}

	RETURN_LONG(obj->data.princ_expire_time);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::setExpiryTime(int $expiry_time)
 */
PHP_METHOD(KADM5Principal, setExpiryTime)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	zend_long expiry_time;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &expiry_time) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.princ_expire_time = expiry_time;
	obj->update_mask |= KADM5_PRINC_EXPIRE_TIME;

	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getLastPasswordChange()
 */
PHP_METHOD(KADM5Principal, getLastPasswordChange)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.last_pwd_change);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getPasswordExpiryTime()
 */
PHP_METHOD(KADM5Principal, getPasswordExpiryTime)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.pw_expiration);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::setPasswordExpiryTime(int $pwd_expiry_time)
 */
PHP_METHOD(KADM5Principal, setPasswordExpiryTime)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	zend_long pwd_expiry_time;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &pwd_expiry_time) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.pw_expiration = pwd_expiry_time;
	obj->update_mask |= KADM5_PW_EXPIRATION;

	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getMaxTicketLifetime()
 */
PHP_METHOD(KADM5Principal, getMaxTicketLifetime)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.max_life);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::setMaxTicketLifetime(int $max_lifetime)
 */
PHP_METHOD(KADM5Principal, setMaxTicketLifetime)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	zend_long max_lifetime;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &max_lifetime) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.max_life = max_lifetime;
	obj->update_mask |= KADM5_MAX_LIFE;

	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getMaxRenewableLifetime()
 */
PHP_METHOD(KADM5Principal, getMaxRenewableLifetime)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.max_renewable_life);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::setMaxRenewableLifetime(int $max_renewable_lifetime)
 */
PHP_METHOD(KADM5Principal, setMaxRenewableLifetime)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	zend_long max_renewable_lifetime;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &max_renewable_lifetime) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.max_renewable_life = max_renewable_lifetime;
	obj->update_mask |= KADM5_MAX_RLIFE;

	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getLastModifier()
 */
PHP_METHOD(KADM5Principal, getLastModifier)
{
	char *princname;
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	krb5_kadm5_object *kadm5;
	zval *connobj = NULL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}

	
	if(obj->loaded) {
		connobj = KRB5_KADM_PRINCIPAL_GET_CONNECTION;
		if ( Z_ISNULL_P(connobj)) {
			zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
			return;
		}
		kadm5 = KRB5_KADM(connobj);
		if ( !kadm5 ) {
			zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
			return;
		}
		
		krb5_unparse_name(kadm5->ctx,obj->data.mod_name,&princname);
		_RETVAL_STRING(princname);
		krb5_free_unparsed_name(kadm5->ctx, princname);
		return;
	} else {
		RETURN_NULL();
	}
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getLastModificationDate()
 */
PHP_METHOD(KADM5Principal, getLastModificationDate)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.mod_date);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getKeyVNO()
 */
PHP_METHOD(KADM5Principal, getKeyVNO)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.kvno);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::setKeyVNO(int $kvno)
 */
PHP_METHOD(KADM5Principal, setKeyVNO)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	zend_long kvno;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &kvno) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.kvno = kvno;
	obj->update_mask |= KADM5_KVNO;

	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getMasterKeyVNO()
 */
PHP_METHOD(KADM5Principal, getMasterKeyVNO)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.mkvno);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::setAttributes(int $attrs)
 */
PHP_METHOD(KADM5Principal, setAttributes)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	zend_long attrs;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &attrs) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.attributes = attrs;
	obj->update_mask |= KADM5_ATTRIBUTES;

	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getAttributes()
 */
PHP_METHOD(KADM5Principal, getAttributes)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.attributes);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getAuxAttributes()
 */
PHP_METHOD(KADM5Principal, getAuxAttributes)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.aux_attributes);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getPolicy()
 */
PHP_METHOD(KADM5Principal, getPolicy)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	zval *connobj = NULL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	if(obj->data.policy) {

		connobj = KRB5_KADM_PRINCIPAL_GET_CONNECTION;
		if ( Z_ISNULL_P(connobj)) {
			zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
			return;
		}
		
#if PHP_MAJOR_VERSION < 7
		zval *func;
		zval *args[1];
		MAKE_STD_ZVAL(func);
		ZVAL_STRING(func, "getPolicy", 1);
		MAKE_STD_ZVAL(args[0]);
		ZVAL_STRING(args[0], obj->data.policy, 1);
		
		if(call_user_function(&krb5_ce_kadm5_policy->function_table, 
								&connobj, func, return_value, 1, 
								args TSRMLS_CC) == FAILURE) {
			zval_ptr_dtor(&args[0]);
			zval_ptr_dtor(&func);
			zend_throw_exception(NULL, "Failed to instantiate KADM5Policy object", 0 TSRMLS_CC);
			return;
		}

		zval_ptr_dtor(&args[0]);
		zval_ptr_dtor(&func);
#else
		zval func;
		zval args[1];
		ZVAL_STRING(&func, "getPolicy");
		ZVAL_STRING(&args[0], obj->data.policy);
		if(call_user_function(&krb5_ce_kadm5_policy->function_table, connobj, &func, return_value, 1, 
								args TSRMLS_CC) == FAILURE) {	
			zval_dtor(&args[0]);
			zval_dtor(&func);
			zend_throw_exception(NULL, "Failed to instantiate KADM5Policy object", 0 TSRMLS_CC);
			return;
		}
		zval_dtor(&args[0]);
		zval_dtor(&func);
#endif
	}
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::setPolicy(mixed $policy)
 */
PHP_METHOD(KADM5Principal, setPolicy)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	zval *policy = NULL;
	krb5_kadm5_policy_object *pol;
	zend_string *pstr;

	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "|z", &policy) == FAILURE) {
		RETURN_FALSE;
	}

	if(obj->data.policy) {
		free(obj->data.policy);
		obj->data.policy = NULL;
	}

	switch(Z_TYPE_P(policy)) {

		case IS_NULL:
			if(obj->data.policy) {
				obj->data.policy = NULL;
				obj->update_mask |= KADM5_POLICY_CLR;
			}
			break;

		case IS_OBJECT:
			if(Z_OBJCE_P(policy) == krb5_ce_kadm5_policy) {
				pol = KRB5_KADM_POLICY(policy);

				obj->data.policy = strdup(pol->policy);
				obj->update_mask |= KADM5_POLICY;
				break;
			}

		default:
			pstr = zval_get_string(policy TSRMLS_CC);
			obj->data.policy = strdup(pstr->val);
			obj->update_mask |= KADM5_POLICY;
			zend_string_release(pstr);
			break;

	}

	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::clearPolicy()
 */
PHP_METHOD(KADM5Principal, clearPolicy)
{	
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	if ( obj->data.policy ) {
		free(obj->data.policy);
	}
	obj->data.policy = NULL;
	obj->update_mask |= KADM5_POLICY_CLR;

	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getLastSuccess()
 */
PHP_METHOD(KADM5Principal, getLastSuccess)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.last_success);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getLastFailed()
 */
PHP_METHOD(KADM5Principal, getLastFailed)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.last_failed);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::getFailedAuthCount()
 */
PHP_METHOD(KADM5Principal, getFailedAuthCount)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.fail_auth_count);
}
/* }}} */

/* {{{ proto KADM5Principal KADM5Principal::resetFailedAuthCount()
 */
PHP_METHOD(KADM5Principal, resetFailedAuthCount)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	
	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	obj->data.fail_auth_count = 0;
	obj->update_mask |= KADM5_FAIL_AUTH_COUNT;
}
/* }}} */


/* {{{ proto array KADM5Principal::getTLData()
 *
 */
PHP_METHOD(KADM5Principal, getTLData)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	
	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}

	array_init(return_value);
	php_krb5_kadm5_tldata_to_array(return_value, obj->data.tl_data, obj->data.n_tl_data TSRMLS_CC);
}
/* }}} */

/* {{{ proto void KADM5Principal::setTLData(array)
 *
 */
PHP_METHOD(KADM5Principal, setTLData)
{
	krb5_kadm5_principal_object *obj = KRB5_THIS_KADM_PRINCIPAL;
	zval *array;
	
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "a", &array) == FAILURE) {
		RETURN_FALSE;
	}

	if ( obj->data.tl_data && obj->data.n_tl_data > 0 ) {
		php_krb5_kadm5_tldata_free(obj->data.tl_data, obj->data.n_tl_data TSRMLS_CC);
	}
	obj->data.tl_data = php_krb5_kadm5_tldata_from_array(array, &obj->data.n_tl_data TSRMLS_CC);
	obj->update_mask |= KADM5_TL_DATA;
}
/* }}} */
