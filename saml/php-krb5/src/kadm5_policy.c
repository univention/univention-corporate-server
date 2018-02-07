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

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Policy_none, 0, 0, 0)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Policy__construct, 0, 0, 1)
	ZEND_ARG_INFO(0, policy)
	ZEND_ARG_OBJ_INFO(0, conn, KADM5, 0)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Policy_setMinPasswordLife, 0, 0, 1)
	ZEND_ARG_INFO(0, min_life)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Policy_setMaxPasswordLife, 0, 0, 1)
	ZEND_ARG_INFO(0, max_life)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Policy_setMinPasswordLength, 0, 0, 1)
	ZEND_ARG_INFO(0, min_length)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Policy_setMinPasswordClasses, 0, 0, 1)
	ZEND_ARG_INFO(0, min_classes)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Policy_setHistoryNum, 0, 0, 1)
	ZEND_ARG_INFO(0, history_num)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Policy_setLockoutDuration, 0, 0, 1)
	ZEND_ARG_INFO(0, duration)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Policy_setMaxFailureCount, 0, 0, 1)
	ZEND_ARG_INFO(0, failcnt)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5Policy_setFailureInterval, 0, 0, 1)
	ZEND_ARG_INFO(0, interval)
ZEND_END_ARG_INFO()

static zend_function_entry krb5_kadm5_policy_functions[] = {
	PHP_ME(KADM5Policy, __construct,           arginfo_KADM5Policy__construct,            ZEND_ACC_PUBLIC | ZEND_ACC_CTOR)
	PHP_ME(KADM5Policy, load,                  arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, save,                  arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, delete,                arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, getPropertyArray,      arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, getName,               arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, getMinPasswordLife,    arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, setMinPasswordLife,    arginfo_KADM5Policy_setMinPasswordLife,    ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, getMaxPasswordLife,    arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, setMaxPasswordLife,    arginfo_KADM5Policy_setMaxPasswordLife,    ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, getMinPasswordLength,  arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, setMinPasswordLength,  arginfo_KADM5Policy_setMinPasswordLength,  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, getMinPasswordClasses, arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, setMinPasswordClasses, arginfo_KADM5Policy_setMinPasswordClasses, ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, getHistoryNum,         arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, setHistoryNum,         arginfo_KADM5Policy_setHistoryNum,         ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, getReferenceCount,     arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, getMaxFailureCount,    arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, setMaxFailureCount,    arginfo_KADM5Policy_setMaxFailureCount,    ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, getFailureInterval,    arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, setFailureInterval,    arginfo_KADM5Policy_setFailureInterval,    ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, getLockoutDuration,    arginfo_KADM5Policy_none,                  ZEND_ACC_PUBLIC)
	PHP_ME(KADM5Policy, setLockoutDuration,    arginfo_KADM5Policy_setLockoutDuration,    ZEND_ACC_PUBLIC)
	PHP_FE_END
};

zend_object_handlers krb5_kadm5_policy_handlers;

#if PHP_MAJOR_VERSION < 7
static void php_krb5_kadm5_policy_object_dtor(void *obj, zend_object_handle handle TSRMLS_DC)
{
	krb5_kadm5_policy_object *object = (krb5_kadm5_policy_object*)obj;


	if(object->policy) {
		efree(object->policy);
	}

	krb5_kadm5_object *conn = object->conn;
	if(conn) {
		kadm5_free_policy_ent(conn->handle, &object->data);
	}
	zend_object_std_dtor(&(object->std) TSRMLS_CC);
	efree(object);
}
#else
static void php_krb5_kadm5_policy_object_free(zend_object *obj) {
	krb5_kadm5_policy_object *object = (krb5_kadm5_policy_object*)((char *)obj - XtOffsetOf(krb5_kadm5_policy_object, std));
	krb5_kadm5_object *conn = object->conn;
	if(object->policy) {
		efree(object->policy);
	}
	if(conn) {
			kadm5_free_policy_ent(conn->handle, &object->data);
	}
	zend_object_std_dtor(obj);
}
#endif

int php_krb5_register_kadm5_policy(TSRMLS_D) {
	zend_class_entry kadm5_policy;
	INIT_CLASS_ENTRY(kadm5_policy, "KADM5Policy", krb5_kadm5_policy_functions);
	krb5_ce_kadm5_policy = zend_register_internal_class(&kadm5_policy TSRMLS_CC);
	krb5_ce_kadm5_policy->create_object = php_krb5_kadm5_policy_object_new;
	memcpy(&krb5_kadm5_policy_handlers, zend_get_std_object_handlers(), sizeof(zend_object_handlers));
#if PHP_MAJOR_VERSION >= 7
	krb5_kadm5_policy_handlers.offset = XtOffsetOf(krb5_kadm5_policy_object, std);
	krb5_kadm5_policy_handlers.free_obj = php_krb5_kadm5_policy_object_free;
#endif
	return SUCCESS;
}


#if PHP_MAJOR_VERSION < 7
zend_object_value php_krb5_kadm5_policy_object_new(zend_class_entry *ce TSRMLS_DC) 
{
	zend_object_value retval;
	krb5_kadm5_policy_object *object;
	extern zend_object_handlers krb5_kadm5_policy_handlers;

	object = emalloc(sizeof(krb5_kadm5_policy_object));

	memset(&object->data, 0, sizeof(kadm5_policy_ent_rec));
	object->conn = NULL;
	object->update_mask = 0;
	
	zend_object_std_init(&(object->std), ce TSRMLS_CC);

#if PHP_VERSION_ID < 50399
	zend_hash_copy(object->std.properties, &ce->default_properties,
					(copy_ctor_func_t) zval_add_ref, NULL, 
					sizeof(zval*));
#else
	object_properties_init(&(object->std), ce);
#endif

	retval.handle = zend_objects_store_put(object, php_krb5_kadm5_policy_object_dtor, NULL, NULL TSRMLS_CC);

	retval.handlers = &krb5_kadm5_policy_handlers;
	return retval;
}
#else
zend_object* php_krb5_kadm5_policy_object_new(zend_class_entry *ce TSRMLS_DC) {
	krb5_kadm5_policy_object *object = ecalloc(1, sizeof(krb5_kadm5_policy_object) + zend_object_properties_size(ce));
	zend_object_std_init(&object->std, ce TSRMLS_CC);
	object_properties_init(&object->std, ce);
	object->std.handlers = &krb5_kadm5_policy_handlers;
	return &object->std;
}
#endif

/* {{{ proto KADM5Policy::__construct(string $policy [, KADM5 $conn ])
 */
PHP_METHOD(KADM5Policy, __construct)
{
	krb5_kadm5_policy_object *this = KRB5_THIS_KADM_POLICY;
	char *spolicy = NULL;
	strsize_t spolicy_len;

	krb5_kadm5_policy_object *obj;

	zval *connobj = NULL;


	KRB5_SET_ERROR_HANDLING(EH_THROW);
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "s|O", &spolicy, &spolicy_len, &connobj, krb5_ce_kadm5) == FAILURE) {
		RETURN_NULL();
	}
	KRB5_SET_ERROR_HANDLING(EH_NORMAL);

	obj = KRB5_THIS_KADM_POLICY;
	obj->policy = estrndup(spolicy, spolicy_len);

	if(connobj && Z_TYPE_P(connobj) == IS_OBJECT) {
		zend_update_property(krb5_ce_kadm5_principal, getThis(), "connection", sizeof("connection"), connobj TSRMLS_CC);
		this->conn = KRB5_KADM(connobj);

#if PHP_MAJOR_VERSION < 7
		zval *dummy_retval, *func;
		MAKE_STD_ZVAL(func);
		_ZVAL_STRING(func, "load");
		MAKE_STD_ZVAL(dummy_retval);
		if(call_user_function(&krb5_ce_kadm5_policy->function_table, 
								&getThis(), func, dummy_retval, 0, 
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
		_ZVAL_STRING(&func, "load");
		if(call_user_function(&krb5_ce_kadm5_policy->function_table, getThis(), &func, &dummy_retval, 0, 
								NULL TSRMLS_CC) == FAILURE) {	
			zval_ptr_dtor(&func);
			zval_ptr_dtor(&dummy_retval);
			zend_throw_exception(NULL, "Failed to update KADM5Policy object", 0 TSRMLS_CC);
			return;
		}
		zval_ptr_dtor(&func);
		zval_ptr_dtor(&dummy_retval);
#endif
	}
}
/* }}} */

#if PHP_MAJOR_VERSION < 7
#define KRB5_KADM_POLICY_GET_CONNECTION zend_read_property(krb5_ce_kadm5_policy, getThis(), "connection", sizeof("connection"),1 TSRMLS_CC);
#else
#define KRB5_KADM_POLICY_GET_CONNECTION zend_read_property(krb5_ce_kadm5_policy, getThis(), "connection", sizeof("connection"),1, NULL TSRMLS_CC);
#endif

/* {{{ proto KADM5Policy::load()
 */
PHP_METHOD(KADM5Policy, load)
{
	kadm5_ret_t retval;
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;
	krb5_kadm5_object *kadm5;
	zval *connobj = NULL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	connobj = KRB5_KADM_POLICY_GET_CONNECTION;
	if ( Z_ISNULL_P(connobj) ) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}
	
	kadm5 = KRB5_KADM(connobj);
	if(!kadm5) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}

	retval = kadm5_get_policy(kadm5->handle, obj->policy, &obj->data);
	if(retval != KADM5_OK || !obj->data.policy) {
		const char *errmsg = krb5_get_error_message(kadm5->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(kadm5->ctx, errmsg);
		return;
	}
}
/* }}} */

/* {{{ proto KADM5Policy::save()
 */
PHP_METHOD(KADM5Policy, save)
{
	kadm5_ret_t retval;
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;
	krb5_kadm5_object *kadm5;
	zval *connobj = NULL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	connobj = KRB5_KADM_POLICY_GET_CONNECTION;
	if ( Z_ISNULL_P(connobj) ) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}

	kadm5 = KRB5_KADM(connobj);
	if(!kadm5) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}

	retval = kadm5_modify_policy(kadm5->handle, &obj->data, obj->update_mask);
	if(retval != KADM5_OK) {
		const char *errmsg = krb5_get_error_message(kadm5->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(kadm5->ctx, errmsg);
		return;
	}
}
/* }}} */

/* {{{ proto KADM5Policy::delete()
 */
PHP_METHOD(KADM5Policy, delete)
{
	kadm5_ret_t retval;
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;
	krb5_kadm5_object *kadm5;
	zval *connobj = NULL;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	connobj = KRB5_KADM_POLICY_GET_CONNECTION;
	if ( Z_ISNULL_P(connobj) ) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}

	kadm5 = KRB5_KADM(connobj);
	if(!kadm5) {
		zend_throw_exception(NULL, "No valid connection available", 0 TSRMLS_CC);
		return;
	}

	retval = kadm5_delete_policy(kadm5->handle, obj->policy);
	if(retval != KADM5_OK) {
		const char *errmsg = krb5_get_error_message(kadm5->ctx, (int)retval);
		zend_throw_exception(NULL, errmsg, (int)retval TSRMLS_CC);
		krb5_free_error_message(kadm5->ctx, errmsg);
		return;
	}
}
/* }}} */


/* {{{ proto KADM5Policy::getPropertyArray()
 */
PHP_METHOD(KADM5Policy, getPropertyArray)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	array_init(return_value);
	_add_assoc_string(return_value, "policy", obj->policy);
	add_assoc_long(return_value, "pw_min_life", obj->data.pw_min_life);
	add_assoc_long(return_value, "pw_max_life", obj->data.pw_max_life);
	add_assoc_long(return_value, "pw_min_length", obj->data.pw_min_length);
	add_assoc_long(return_value, "pw_min_classes", obj->data.pw_min_classes);
	add_assoc_long(return_value, "pw_history_num", obj->data.pw_history_num);
	add_assoc_long(return_value, "pw_lockout_duration", obj->data.pw_lockout_duration);
	add_assoc_long(return_value, "pw_failcnt_interval", obj->data.pw_failcnt_interval);
	add_assoc_long(return_value, "pw_max_fail", obj->data.pw_max_fail);
	add_assoc_long(return_value, "policy_refcnt", obj->data.policy_refcnt);
}
/* }}} */

/* {{{ proto KADM5Policy::getName()
 */
PHP_METHOD(KADM5Policy, getName)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	_RETURN_STRING(obj->policy);
}
/* }}} */

/* {{{ proto KADM5Policy::getMinPasswordLife()
 */
PHP_METHOD(KADM5Policy, getMinPasswordLife)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.pw_min_life);
}
/* }}} */

/* {{{ proto KADM5Policy::setMinPasswordLife(int $min_life)
 */
PHP_METHOD(KADM5Policy, setMinPasswordLife)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;
	zend_long min_life;
	
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &min_life) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.pw_min_life = min_life;
	obj->update_mask |= KADM5_PW_MIN_LIFE;
	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Policy::getMaxPasswordLife()
 */
PHP_METHOD(KADM5Policy, getMaxPasswordLife)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.pw_max_life);
}
/* }}} */

/* {{{ proto KADM5Policy::setMaxPasswordLife(int $max_life)
 */
PHP_METHOD(KADM5Policy, setMaxPasswordLife)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;
	zend_long max_life;
	
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &max_life) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.pw_max_life = max_life;
	obj->update_mask |= KADM5_PW_MAX_LIFE;
	RETURN_TRUE;
}
/* }}} */


/* {{{ proto KADM5Policy::getMinPasswordLength()
 */
PHP_METHOD(KADM5Policy, getMinPasswordLength)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.pw_min_length);
}
/* }}} */

/* {{{ proto KADM5Policy::setMinPasswordLength(int $min_length)
 */
PHP_METHOD(KADM5Policy, setMinPasswordLength)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;
	zend_long min_length;
	
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &min_length) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.pw_min_length = min_length;
	obj->update_mask |= KADM5_PW_MIN_LENGTH;
	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Policy::getMinPasswordClasses()
 */
PHP_METHOD(KADM5Policy, getMinPasswordClasses)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.pw_min_classes);
}
/* }}} */

/* {{{ proto KADM5Policy::setMinPasswordClasses(int $min_classes)
 */
PHP_METHOD(KADM5Policy, setMinPasswordClasses)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;
	zend_long min_classes;
	
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &min_classes) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.pw_min_classes = min_classes;
	obj->update_mask |= KADM5_PW_MIN_CLASSES;
	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Policy::getHistoryNum()
 */
PHP_METHOD(KADM5Policy, getHistoryNum)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.pw_history_num);
}
/* }}} */

/* {{{ proto KADM5Policy::setHistoryNum(int $history_num)
 */
PHP_METHOD(KADM5Policy, setHistoryNum)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;
	zend_long history_num;
	
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &history_num) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.pw_history_num = history_num;
	obj->update_mask |= KADM5_PW_HISTORY_NUM;
	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Policy::getReferenceCount()
 */
PHP_METHOD(KADM5Policy, getReferenceCount)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.policy_refcnt);
}
/* }}} */


/* {{{ proto KADM5Policy::getLockoutDuration()
 */
PHP_METHOD(KADM5Policy, getLockoutDuration)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.pw_lockout_duration);
}
/* }}} */

/* {{{ proto KADM5Policy::setLockoutDuration(long $duration)
 */
PHP_METHOD(KADM5Policy, setLockoutDuration)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;
	zend_long duration;
	
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &duration) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.pw_lockout_duration = duration;
	obj->update_mask |= KADM5_PW_LOCKOUT_DURATION;
	RETURN_TRUE;
}
/* }}} */

/* {{{ proto KADM5Policy::getMaxFailureCount()
 */
PHP_METHOD(KADM5Policy, getMaxFailureCount)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.pw_max_fail);
}
/* }}} */

/* {{{ proto KADM5Policy::setMaxFailureCount(long $maxcnt)
 */
PHP_METHOD(KADM5Policy, setMaxFailureCount)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;
	zend_long maxfail;
	
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &maxfail) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.pw_max_fail = maxfail;
	obj->update_mask |= KADM5_PW_MAX_FAILURE;
	RETURN_TRUE;
}
/* }}} */


/* {{{ proto KADM5Policy::getFailureInterval()
 */
PHP_METHOD(KADM5Policy, getFailureInterval)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;

	if (zend_parse_parameters_none() == FAILURE) {
		return;
	}
	RETURN_LONG(obj->data.pw_failcnt_interval);
}
/* }}} */


/* {{{ proto KADM5Policy::setFailureInterval(long $interval)
 */
PHP_METHOD(KADM5Policy, setFailureInterval)
{
	krb5_kadm5_policy_object *obj = KRB5_THIS_KADM_POLICY;
	zend_long failcnt_interval;
	
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "l", &failcnt_interval) == FAILURE) {
		RETURN_FALSE;
	}

	obj->data.pw_failcnt_interval = failcnt_interval;
	obj->update_mask |= KADM5_PW_FAILURE_COUNT_INTERVAL;
	RETURN_TRUE;
}
/* }}} */
