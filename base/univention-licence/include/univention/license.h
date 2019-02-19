/**	@file license.h
 *	@brief libuniventionlicense
 *
 *	a C-lib for the license handling, include ldap access, key handling,
 *	sign and verify functions and base64 convert.
 */
#ifndef __UNIVENTION_LICENSE_H__
#define __UNIVENTION_LICENSE_H__

/*!
 *	@brief a license object data structure
 *
 *	this structure contains a key and a value array with size elements.
 *	to cleanup such a object use univention_licenseObject_free().
*/
typedef struct
{
		char **val; /*!< the array of key strings*/
		char **key; /*!< the array of value strings */
		int size;	/*!< the size of both arrays*/
} lObj;

/*!
 *	@brief a data element for the qsort of a license
*/
typedef struct
{
		char* key;	/*!< ptr to a key string*/
		char* val;	/*!< ptr to a value string*/
} sortElement;

/*!
 *	@brief a array of strings
*/
typedef struct
{
		char** line; /*< the array of strings */
		int    num;  /*< the number of lines*/
} lStrings;

/* main client functions */
int 	univention_license_select(const char* licensetyp);
int 	univention_license_selectDN(const char* licenseDN);
lStrings*	univention_license_get_value(const char* attributeName);
void	univention_license_free(void);

/* main admin function */
int 	univention_license_check(const char* objectDN);

/* main create license function */
char* 	univention_license_sign_license(const char* licenseDN);


/* license handling */
int 	univention_license_init(void);
lObj*	univention_license_get_global_license(void);

int 	univention_license_check_basedn(void);
int 	univention_license_check_enddate(void);
int 	univention_license_check_searchpath(const char* objectDN);
int 	univention_license_check_signature(void);

lStrings* univention_licenseStrings_malloc(int num);
void	univention_licenseStrings_free(lStrings* strings);
lObj*	univention_licenseObject_malloc(int size);
void	univention_licenseObject_free(lObj* license);

/*public key handling*/
int 	univention_license_key_init(void);
void	univention_license_key_free(void);
int 	univention_license_key_public_key_installed(void);
int 	univention_license_key_public_key_load(void);
int 	univention_license_verify(const char* data, const char* signature);

/*private key*/
int 	univention_license_key_private_key_installed(void);
int 	univention_license_key_private_key_load_file(const char* filename, const char* passwd);

/*signature handling*/
int 	univention_license_compare_string(const char* a, const char* b);
int 	univention_license_qsort_hook(sortElement* a, sortElement* b);
lObj*	univention_license_sort(lObj* license);

char*	univention_license_build_data(lObj* license);
unsigned int 	univention_license_base64_to_raw(const char* base64data, unsigned char** rawdata);
char*	univention_license_raw_to_base64(const unsigned char* data, unsigned int datalen);

char*	univention_license_sign(const char* data);

/*ldap*/
int 	univention_license_ldap_init(void);
char*	univention_license_ldap_get_basedn(void);
void 	univention_license_ldap_free(void);

int 	univention_license_ldap_open_connection(void);
void	univention_license_ldap_close_connection(void);

lStrings*	univention_license_ldap_get_strings(const char* objectDN, const char* attribute);
lObj*		univention_license_ldap_search_licenseObject(const char* searchBaseDN, const char* licensetyp, int num);
lObj*		univention_license_ldap_get_licenseObject(const char* licenseDN);

lObj*		univention_license_ldap_get(const char* search_base, int scope, const char* filter, char** attr, const char* attrFilter, int num);
#endif
