/**	@file license.h
 	@brief libuniventionlicense
	
	a C-lib for the license handling, include ldap access, key handling,
	sign and verify functions and base64 convert.
 */
#ifndef __UNIVENTION_LICENSE_H__
#define __UNIVENTION_LICENSE_H__

#include <string.h>
#include <time.h>

#include <openssl/err.h>
#include <openssl/objects.h>
#include <openssl/sha.h>
#include <openssl/rsa.h>
#include <openssl/bio.h>
#include <openssl/pem.h>

#include <univention/debug.h>
#include <univention/config.h>

#include <ldap.h>

/*!
	@brief a license object data structure

	this structure contains a key and a value array with size elements.
	to cleanup such a object use univention_licenseObject_free().
*/
typedef struct
{
		char **val; /*!< the array of key strings*/
		char **key; /*!< the array of value strings */
		int size;	/*!< the size of both arrays*/
}lObj;


/*!
	@brief a data element for the qsort of a license
*/
typedef struct
{
		char* key;	/*!< ptr to a key string*/
		char* val;	/*!< ptr to a value string*/
}sortElement;

/*!
	@brief a array of strings
*/
typedef struct
{
		char** line; /*< the array of strings */
		int    num;  /*< the number of lines*/
}lStrings;

/*main client functions*/
int 	univention_license_select(char* licensetyp);
int 	univention_license_selectDN(char* licenseDN);
lStrings*	univention_license_get_value(char* attributeName);
void	univention_license_free(void);

/*main admin funtion*/
int 	univention_license_check(char* objectDN);

/*main create license function*/
char* 	univention_license_sign_license(char* licenseDN);


/*license handling*/
int 	univention_license_init(void);
lObj*	univention_license_get_global_license(void);

int 	univention_license_check_basedn();
int 	univention_license_check_enddate();
int 	univention_license_check_searchpath(char* objectDN);
int 	univention_license_check_signature();

lStrings* univention_licenseStrings_malloc(int num);
void	univention_licenseStrings_free(lStrings* strings);
lObj*	univention_licenseObject_malloc(int size);
void	univention_licenseObject_free(lObj* license);

/*public key handling*/
int 	univention_license_key_init(void);
void	univention_license_key_free(void);
int 	univention_license_key_public_key_installed(void);
int 	univention_license_key_public_key_load(void);
int 	univention_license_verify (char* data, char* signature);

/*private key*/
int 	univention_license_key_private_key_installed(void);
int 	univention_license_key_private_key_load_file(char* filename, char* passwd);

/*signature handling*/
int 	univention_license_compare_string(char* a, char* b);
int 	univention_license_qsort_hook(sortElement* a, sortElement* b);
lObj*	univention_license_sort(lObj* license);

char*	univention_license_build_data(lObj* license);
int 	univention_license_base64_to_raw(char* base64data, char** rawdata);
char*	univention_license_raw_to_base64(char* data, int datalen);

char*	univention_license_sign(char* data);

/*ldap*/
int 	univention_license_ldap_init(void);
char*	univention_license_ldap_get_basedn(void);
void 	univention_license_ldap_free(void);

int 	univention_license_ldap_open_connection(void);
void	univention_license_ldap_close_connection(void);

lStrings*	univention_license_ldap_get_strings(char* objectDN, char* attribute);
lObj*		univention_license_ldap_search_licenseObject(char* searchBaseDN, char* licensetyp, int num);
lObj*		univention_license_ldap_get_licenseObject(char* licenseDN);

lObj*		univention_license_ldap_get(char* search_base, int scope, char* filter, char** attr, char* attrFilter, int num);
#endif
