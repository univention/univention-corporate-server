/**
* Copyright (c) 2016 Moritz Bechler
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

#include "config.h"
#include "php_krb5.h"
#include "php_krb5_kadm.h"
#include "compat.h"

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5TLData_none, 0, 0, 0)
ZEND_END_ARG_INFO()

ZEND_BEGIN_ARG_INFO_EX(arginfo_KADM5TLData__construct, 0, 0, 0)
ZEND_END_ARG_INFO()

static zend_function_entry krb5_kadm5_tldata_functions[] = {
	PHP_ME(KADM5TLData, __construct, arginfo_KADM5TLData__construct, ZEND_ACC_PUBLIC | ZEND_ACC_CTOR)
	PHP_ME(KADM5TLData, getType, arginfo_KADM5TLData_none, ZEND_ACC_PUBLIC)
	PHP_ME(KADM5TLData, getData, arginfo_KADM5TLData_none, ZEND_ACC_PUBLIC)
	PHP_FE_END
};

zend_object_handlers krb5_kadm5_tldata_handlers;

/* KADM5Principal ctor/dtor */
#if PHP_MAJOR_VERSION < 7
static void php_krb5_kadm5_tldata_object_dtor(void *obj, zend_object_handle handle TSRMLS_DC)
{
	krb5_kadm5_tldata_object *object = (krb5_kadm5_tldata_object*)obj;
	zend_object_std_dtor(&(object->std) TSRMLS_CC);

	if(object) {
		if ( object->data.tl_data_contents ) {
			efree(object->data.tl_data_contents);
		}
		efree(object);
	}
}
#else
static void php_krb5_kadm5_tldata_object_free(zend_object *obj TSRMLS_DC)
{
	krb5_kadm5_tldata_object *object = (krb5_kadm5_tldata_object*)((char *)obj - XtOffsetOf(krb5_kadm5_tldata_object, std));
	if ( object->data.tl_data_contents ) {
		efree(object->data.tl_data_contents);
	}
}
#endif

int php_krb5_register_kadm5_tldata(TSRMLS_D) {


	zend_class_entry kadm5_tldata;
	INIT_CLASS_ENTRY(kadm5_tldata, "KADM5TLData", krb5_kadm5_tldata_functions);
	krb5_ce_kadm5_tldata = zend_register_internal_class(&kadm5_tldata TSRMLS_CC);
	krb5_ce_kadm5_tldata->create_object = php_krb5_kadm5_tldata_object_new;
	memcpy(&krb5_kadm5_tldata_handlers, zend_get_std_object_handlers(), sizeof(zend_object_handlers));
#if PHP_MAJOR_VERSION >= 7
	krb5_kadm5_tldata_handlers.offset = XtOffsetOf(krb5_kadm5_tldata_object, std);
	krb5_kadm5_tldata_handlers.free_obj = php_krb5_kadm5_tldata_object_free;
#endif
	return SUCCESS;
}


#if PHP_MAJOR_VERSION < 7
zend_object_value php_krb5_kadm5_tldata_object_new(zend_class_entry *ce TSRMLS_DC)
{
	zend_object_value retval;
	krb5_kadm5_tldata_object *object;
	extern zend_object_handlers krb5_kadm5_tldata_handlers;

	object = emalloc(sizeof(krb5_kadm5_tldata_object));

	memset(&object->data, 0, sizeof(krb5_tl_data));

	zend_object_std_init(&(object->std), ce TSRMLS_CC);

#if PHP_VERSION_ID < 50399
	zend_hash_copy(object->std.properties, &ce->default_properties,
					(copy_ctor_func_t) zval_add_ref, NULL, 
					sizeof(zval*));
#else
	object_properties_init(&(object->std), ce);
#endif

	retval.handle = zend_objects_store_put(object, php_krb5_kadm5_tldata_object_dtor, NULL, NULL TSRMLS_CC);
	retval.handlers = &krb5_kadm5_tldata_handlers;
	return retval;
}
#else
zend_object* php_krb5_kadm5_tldata_object_new(zend_class_entry *ce TSRMLS_DC)
{
	krb5_kadm5_tldata_object *object = ecalloc(1, sizeof(krb5_kadm5_tldata_object) + zend_object_properties_size(ce));
	zend_object_std_init(&object->std, ce TSRMLS_CC);
	object_properties_init(&object->std, ce);
	object->std.handlers = &krb5_kadm5_tldata_handlers;
	return &object->std;
}
#endif


/* {{{ proto KADM5TLData KADM5TLData::__construct( long type [, string data])
 */
PHP_METHOD(KADM5TLData, __construct)
{
	zend_long type = 0;
	char *data;
	strsize_t data_len = 0;

	KRB5_SET_ERROR_HANDLING(EH_THROW);
	if(zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "ls", &type, &data, &data_len) == FAILURE) {
		RETURN_NULL();
	}
	KRB5_SET_ERROR_HANDLING(EH_NORMAL);


	krb5_kadm5_tldata_object *tldata = KRB5_THIS_KADM_TLDATA;

	tldata->data.tl_data_type = type;
	tldata->data.tl_data_length = data_len;
	tldata->data.tl_data_contents = emalloc(data_len);
	memcpy(tldata->data.tl_data_contents, data, data_len);
}
/* }}} */

/* {{{ proto long KADM5TLData::getType()
 */
PHP_METHOD(KADM5TLData, getType)
{
	krb5_kadm5_tldata_object *tldata = KRB5_THIS_KADM_TLDATA;

	RETURN_LONG(tldata->data.tl_data_type);
}
/* }}} */

/* {{{ proto string KADM5TLData::getData()
 */
PHP_METHOD(KADM5TLData, getData)
{
	krb5_kadm5_tldata_object *tldata = KRB5_THIS_KADM_TLDATA;

	_RETVAL_STRINGL((char*)tldata->data.tl_data_contents, tldata->data.tl_data_length);
}
/* }}} */


void php_krb5_kadm5_tldata_to_array(zval* array, krb5_tl_data *data, krb5_int16 num TSRMLS_DC) {
	krb5_tl_data *cur = data;
	int n = num;
	while ( n > 0 && cur ) {
		zval *entry = ecalloc(1, sizeof(zval));
		_ALLOC_INIT_ZVAL(entry);
		object_init_ex(entry, krb5_ce_kadm5_tldata);
		krb5_kadm5_tldata_object *tldata = KRB5_KADM_TLDATA(entry);
		tldata->data.tl_data_type = cur->tl_data_type;
		tldata->data.tl_data_length = cur->tl_data_length;
		tldata->data.tl_data_contents = emalloc(cur->tl_data_length);
		memcpy(tldata->data.tl_data_contents, cur->tl_data_contents, cur->tl_data_length);
		add_next_index_zval(array, entry);
		//zval_ptr_dtor(entry);
		cur = cur->tl_data_next;
		n--;
	}
}

void php_krb5_kadm5_tldata_free(krb5_tl_data *data, krb5_int16 count TSRMLS_DC) {
	 krb5_tl_data *cur = data;
	 krb5_tl_data *last = NULL;
         int n = count;
	 while ( n > 0 && cur ) {
	 	if ( cur->tl_data_contents ) {
			free(cur->tl_data_contents);			
		}
		last = cur;
	 	cur = cur->tl_data_next;
                n--;
		free(last);
	 }
}

krb5_tl_data* php_krb5_kadm5_tldata_from_array(zval *array, krb5_int16* count TSRMLS_DC) {

	HashTable *arr_hash = Z_ARRVAL_P(array);
	int have_count = 0;
	krb5_tl_data *head = NULL;
	krb5_tl_data *cur = NULL;

#if PHP_MAJOR_VERSION < 7
	HashPosition pointer;
	zval **entryp;
	for(	zend_hash_internal_pointer_reset_ex(arr_hash, &pointer); 
		zend_hash_get_current_data_ex(arr_hash, (void**) &entryp, &pointer) == SUCCESS; 
		zend_hash_move_forward_ex(arr_hash, &pointer)) {

		zval *entry = *entryp;
#else
	zval *entry;
	ZEND_HASH_FOREACH_VAL(arr_hash, entry) {
#endif
		if ( Z_TYPE_P(entry) != IS_OBJECT || Z_OBJCE_P(entry) != krb5_ce_kadm5_tldata ) {
			continue;
		}

		krb5_tl_data *last = cur;
		cur = malloc(sizeof(krb5_tl_data));
		memset(cur, 0, sizeof(krb5_tl_data));
		if ( last ) {
			last->tl_data_next = cur;
		}
		krb5_kadm5_tldata_object *tldata = KRB5_KADM_TLDATA(entry);
		cur->tl_data_type = tldata->data.tl_data_type;
		cur->tl_data_length = tldata->data.tl_data_length;
		cur->tl_data_contents = malloc(tldata->data.tl_data_length);
		memcpy(cur->tl_data_contents, tldata->data.tl_data_contents, tldata->data.tl_data_length);
		have_count++;
		if ( head == NULL ) {
			head = cur;
		}
#if PHP_MAJOR_VERSION < 7
	}
#else
	} ZEND_HASH_FOREACH_END();
#endif
	*count = have_count;
	return head;
}



