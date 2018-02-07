#ifndef PHP_KRB5_COMPAT_H
#define PHP_KRB5_COMPAT_H


#if PHP_MAJOR_VERSION < 7
struct _zend_string {
	char *val;
	int   len;
	int   persistent;
};
typedef struct _zend_string zend_string;
typedef long zend_long;
typedef int strsize_t;

static zend_always_inline zend_string *zend_string_alloc(int len, int persistent)
{
	/* single alloc, so free the buf, will also free the struct */
	char *buf = safe_pemalloc(sizeof(zend_string)+len+1,1,0,persistent);
	zend_string *str = (zend_string *)(buf+len+1);

	str->val = buf;
	str->len = len;
	str->persistent = persistent;

	return str;
}

static zend_always_inline zend_string *zend_string_init(char *s, int len, int persistent) {
	/* single alloc, so free the buf, will also free the struct */
	char *buf = safe_pemalloc(sizeof(zend_string)+len+1,1,0,persistent);
	zend_string *str = (zend_string *)(buf+len+1);

	str->val = buf;
	str->len = len;
	str->persistent = persistent;

	memcpy(str->val, s, len);

	return str;
}

static zend_always_inline void zend_string_free(zend_string *s)
{
	pefree(s->val, s->persistent);
}


static zend_always_inline void zend_string_release(zend_string *s)
{
	zend_string_free(s);
}
/* compatibility macros */
#define _RETURN_STRING(a)      RETURN_STRING(a,1)
/* new macros */
#define RETURN_NEW_STR(s)     RETURN_STRINGL(s->val,s->len,0);
#define ZVAL_DEREF(z)

#define Z_ISNULL_P(z) (z == NULL)

#define _ZVAL_STRINGL(a,b,c) ZVAL_STRINGL(a,b,c,1)
#define _ZVAL_STRING(a,b) ZVAL_STRING(a,b,1)
#define _RETVAL_STRINGL(a,b) RETVAL_STRINGL(a,b,1)
#define _RETVAL_STRING(a) RETVAL_STRING(a,1)

#define _DECLARE_ZVAL(name) zval * name = NULL
#define _INIT_ZVAL INIT_ZVAL
#define _ALLOC_INIT_ZVAL(name) ALLOC_INIT_ZVAL(name)
#define _RELEASE_ZVAL(name) zval_ptr_dtor(&name)
#define _add_next_index_string(...) add_next_index_string(__VA_ARGS__, 1)
#define _add_assoc_string(...) add_assoc_string(__VA_ARGS__, 1)
#define _add_assoc_string_ex(...) add_assoc_string_ex(__VA_ARGS__, 1)
#define _add_assoc_stringl_ex(...) add_assoc_stringl_ex(__VA_ARGS__, 1)

//#define Z_OBJCE_P(zv) zend_get_class_entry(zv TSRMLS_CC)

static inline long zval_get_long(zval *zv TSRMLS_DC) {
	zval* copy;
	long val;
	MAKE_STD_ZVAL(copy);
	MAKE_COPY_ZVAL(&zv, copy);
	convert_to_long(copy);
	val = Z_LVAL_P(copy);
	zval_ptr_dtor(&copy);
	return val;
}

static inline zend_string *zval_get_string(zval *zv TSRMLS_DC) {
	zval* copy;
	zend_string *val;
	MAKE_STD_ZVAL(copy);
	MAKE_COPY_ZVAL(&zv, copy);
	convert_to_string(copy);
	val = zend_string_init(Z_STRVAL_P(copy), Z_STRLEN_P(copy)+1, 0);
	val->val[Z_STRLEN_P(copy)] = 0;
	zval_ptr_dtor(&copy);
	return val;
}

#define KRB5_CCACHE(zv) (krb5_ccache_object *) zend_object_store_get_object(zv TSRMLS_CC)
#define KRB5_NEGOTIATE_AUTH(zv) (krb5_negotiate_auth_object *) zend_object_store_get_object(zv TSRMLS_CC)
#define KRB5_GSSAPI_CONTEXT(zv) (krb5_gssapi_context_object *) zend_object_store_get_object(zv TSRMLS_CC)


#define KRB5_KADM(zv) (krb5_kadm5_object*)zend_object_store_get_object(zv TSRMLS_CC)
#define KRB5_KADM_POLICY(zv) (krb5_kadm5_policy_object*)zend_object_store_get_object(zv TSRMLS_CC)
#define KRB5_KADM_PRINCIPAL(zv) (krb5_kadm5_principal_object*)zend_object_store_get_object(zv TSRMLS_CC)
#define KRB5_KADM_TLDATA(zv) (krb5_kadm5_tldata_object*)zend_object_store_get_object(zv TSRMLS_CC)


#else
#include "zend_operators.h"

typedef size_t strsize_t;
/* removed/uneeded macros */
#define TSRMLS_CC
/* compatibility macros */
#define _RETURN_STRING(a)      RETURN_STRING(a)

#define _DECLARE_ZVAL(name) zval name ## _v; zval * name = &name ## _v
#define _ALLOC_INIT_ZVAL(name) ZVAL_NULL(name)
#define _RELEASE_ZVAL(name) zval_ptr_dtor(name)
#define _add_next_index_string add_next_index_string
#define _add_assoc_string(z, k, s) add_assoc_string_ex(z, k, strlen(k), s)
#define _add_assoc_string_ex add_assoc_string_ex
#define _add_assoc_stringl_ex add_assoc_stringl_ex

#define _ZVAL_STRINGL(a,b,c) ZVAL_STRINGL(a,b,c)
#define _ZVAL_STRING(a,b) ZVAL_STRING(a,b)
#define _RETVAL_STRINGL(a,b) RETVAL_STRINGL(a,b)
#define _RETVAL_STRING(a) RETVAL_STRING(a)

#define KRB5_CCACHE(zv) (krb5_ccache_object*)((char *)Z_OBJ_P(zv) - XtOffsetOf(krb5_ccache_object, std))
#define KRB5_NEGOTIATE_AUTH(zv)  (krb5_negotiate_auth_object*)((char *)Z_OBJ_P(zv) - XtOffsetOf(krb5_negotiate_auth_object, std))
#define KRB5_GSSAPI_CONTEXT(zv)  (krb5_gssapi_context_object*)((char *)Z_OBJ_P(zv) - XtOffsetOf(krb5_gssapi_context_object, std))

#define KRB5_KADM(zv) (krb5_kadm5_object*)((char *)Z_OBJ_P(zv) - XtOffsetOf(krb5_kadm5_object, std))
#define KRB5_KADM_POLICY(zv) (krb5_kadm5_policy_object*)((char *)Z_OBJ_P(zv) - XtOffsetOf(krb5_kadm5_policy_object, std))
#define KRB5_KADM_PRINCIPAL(zv) (krb5_kadm5_principal_object*)((char *)Z_OBJ_P(zv) - XtOffsetOf(krb5_kadm5_principal_object, std))
#define KRB5_KADM_TLDATA(zv) (krb5_kadm5_tldata_object*)((char *)Z_OBJ_P(zv) - XtOffsetOf(krb5_kadm5_tldata_object, std))

#endif

static zend_always_inline zval* zend_compat_hash_index_find(HashTable *ht, zend_ulong idx)
{
#if PHP_MAJOR_VERSION < 7
	zval **tmp, *result;

	if (zend_hash_index_find(ht, idx, (void **) &tmp) == FAILURE) {
		return NULL;
	}

	result = *tmp;
	return result;
#else
	return zend_hash_index_find(ht, idx);
#endif
}

static zend_always_inline zval* zend_compat_hash_find(HashTable *ht, char *key, size_t len)
{
#if PHP_MAJOR_VERSION < 7
	zval **tmp;
	if (zend_hash_find(ht, key, len, (void **) &tmp) == FAILURE) {
		return NULL;
	}
	return *tmp;
#else
	zval *result;
	zend_string *key_str = zend_string_init(key, len-1, 0);
	result = zend_hash_find(ht, key_str);
	zend_string_release(key_str);
	return result;
#endif
}

#define KRB5_THIS_CCACHE KRB5_CCACHE(getThis())
#define KRB5_THIS_NEGOTIATE_AUTH KRB5_NEGOTIATE_AUTH(getThis())
#define KRB5_THIS_GSSAPI_CONTEXT KRB5_GSSAPI_CONTEXT(getThis())

#define KRB5_THIS_KADM KRB5_KADM(getThis())
#define KRB5_THIS_KADM_POLICY KRB5_KADM_POLICY(getThis())
#define KRB5_THIS_KADM_PRINCIPAL KRB5_KADM_PRINCIPAL(getThis())
#define KRB5_THIS_KADM_TLDATA KRB5_KADM_TLDATA(getThis())




/* PHP Compatability */
#if (PHP_MAJOR_VERSION == 5 && PHP_MINOR_VERSION == 1 && PHP_RELEASE_VERSION > 2) || (PHP_MAJOR_VERSION == 5 && PHP_MINOR_VERSION > 1) || (PHP_MAJOR_VERSION > 5)

#define INIT_STD_OBJECT(object, ce) zend_object_std_init(&(object), ce TSRMLS_CC);

#else

#define INIT_STD_OBJECT(object, ce) \
	{ 	\
		ALLOC_HASHTABLE(object.properties); \
		zend_hash_init(object.properties,0, NULL, ZVAL_PTR_DTOR, 0); \
		object.ce = ce; \
		object.guards = NULL; \
	}

#endif


#if (PHP_MAJOR_VERSION == 5 && PHP_MINOR_VERSION == 1 && PHP_RELEASE_VERSION > 2) || (PHP_MAJOR_VERSION == 5 && PHP_MINOR_VERSION > 1) || (PHP_MAJOR_VERSION > 5)
#define OBJECT_STD_DTOR(object) zend_object_std_dtor(&(object) TSRMLS_CC);
#else
#define OBJECT_STD_DTOR(object) \
	{ 	\
		if(object.guards) { \
			zend_hash_destroy(object.guards); \
			FREE_HASHTABLE(object.guards); \
		} \
		if(object.properties) { \
			zend_hash_destroy(object.properties); \
			FREE_HASHTABLE(object.properties); \
		} \
	}
#endif

#if defined(PHP_VERSION_ID) && PHP_VERSION_ID >= 50400
#define ARG_PATH "p"
#else
#define ARG_PATH "s"
#endif

#if defined(PHP_VERSION_ID) && PHP_VERSION_ID >= 50300
/* php_set_error_handling() is deprecated */
#define KRB5_SET_ERROR_HANDLING(type)  zend_replace_error_handling(type, NULL, NULL TSRMLS_CC)
#else
#define KRB5_SET_ERROR_HANDLING(type)  php_set_error_handling(type, NULL  TSRMLS_CC)
#endif

/* For PHP < 5.3 */
#ifndef zend_parse_parameters_none
#define zend_parse_parameters_none() zend_parse_parameters(ZEND_NUM_ARGS() TSRMLS_CC, "")
#endif

/* For PHP < 5.3 */
#ifndef PHP_FE_END
#define PHP_FE_END {NULL, NULL, NULL}
#endif

#endif
