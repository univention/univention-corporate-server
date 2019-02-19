/*! @file license_ldap.c
	@brief the ldap functions for the license lib
*/

#include "internal.h"

#include <univention/ldap.h>

univention_ldap_parameters_t* lp = NULL;

#define _UNIVENTION_LDAP_MACHINE_SECRET_LEN_MAX 60
int univention_ldap_set_machine_connection( univention_ldap_parameters_t *lp )
{
	FILE *secret;
	size_t len;

	asprintf(&lp->binddn, univention_config_get_string("ldap/hostdn"));
	if (!lp->binddn) {
		goto err;
	}

	secret = fopen("/etc/machine.secret", "r" );
	if (!secret)
		goto err1;

	lp->bindpw = calloc(_UNIVENTION_LDAP_MACHINE_SECRET_LEN_MAX, sizeof(char));
	if (!lp->bindpw) {
		fclose(secret);
		goto err1;
	}

	len = fread(lp->bindpw, _UNIVENTION_LDAP_MACHINE_SECRET_LEN_MAX, sizeof(char), secret);
	if (ferror(secret))
		len = -1;
	fclose(secret);

	for (; len >= 0; len--) {
		switch (lp->bindpw[len]) {
			case '\r':
			case '\n':
				lp->bindpw[len] = '\0';
			case '\0':
				continue;
			default:
				return 0;
		}
	}

	/* password already cleared memory. */
	if (lp->bindpw != NULL) {
		free(lp->bindpw);
		lp->bindpw = NULL;
	}
err1:
	if (lp->binddn != NULL) {
		free(lp->binddn);
		lp->binddn = NULL;
	}
err:
	return 1;
}	

/******************************************************************************/
/*!
	@brief initialize the ldap part of the lib, automatic called if need
	@todo remove the debug functions, in the moment the ldap server is always testing.
	
	@retval 1 if succeed
	@retval 0 on error
*/
int univention_license_ldap_init(void)
{
	lp = univention_ldap_new();
	if (univention_ldap_set_admin_connection(lp)) {
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "univention_ldap_set_admin_connection() failed, trying univention_ldap_set_machine_connection().");
		univention_ldap_set_machine_connection(lp);
	}
	univention_ldap_open(lp);

	return 1;
}

/******************************************************************************/
/*!
	@brief	close the ldap connection and clean up all ldap stuff
	this is called automatic from univention_license_free()
*/
void univention_license_ldap_free(void)
{
	univention_ldap_close(lp);
}

/******************************************************************************/
/*!
	@brief	get the baseDN of the ldap server
	@retval 1 if ok
	@retval 0 on error
*/
char* univention_license_ldap_get_basedn(void)
{
	return lp->base;
}

/******************************************************************************/
/*!
	@brief	open a connection to the ldap server, with the connection data received from UCR
	@retval	1	if the connection was already open or was opened successful
	@retval	0	if an error has occurred
*/
int univention_license_ldap_open_connection(void)
{

	if ( lp == NULL ) {
		 return univention_license_ldap_init();
	}

	return 1;
}

/******************************************************************************/
/*!
	@brief close the possible open connection to the ldap server,
	is automatic called by univention_license_ldap_free().
*/
void univention_license_ldap_close_connection(void)
{
	univention_ldap_close(lp);
}

/******************************************************************************/
/*! @brief search a licenseObject with a specific type in the searchBaseDN ldap path
	
	@param searchBaseDN	the ldap path where a licenseObject is searched
	@param licensetyp	the requested license type (the ldap attribute univentionLicenseModule have this value)
	@param num	the number of found objects to skip at first, so you can get the 2nd or 3rd one.
	
	@return Pointer to a lObj if found, or NULL if an error has occurred.
*/
lObj* univention_license_ldap_search_licenseObject(const char* searchBaseDN, const char* licensetyp, int num)
{
	lObj* ret=NULL;
	char* filter;
	int filter_len;
	char* attr[] = {NULL};
	int scope    = LDAP_SCOPE_ONELEVEL;
	
	//build searchfilter
	filter_len = strlen("(&(objectClass=univentionLicense)(univentionLicenseModule=") + strlen(licensetyp) + strlen("))");
	filter = malloc(sizeof(char) * filter_len + 1);
	filter[filter_len] = 0;
	sprintf(filter,"(&(objectClass=univentionLicense)(univentionLicenseModule=%s))", licensetyp);
	
	ret = univention_license_ldap_get(searchBaseDN, scope, filter, attr, "univentionLicense", num);
	
	free(filter);
	return ret;
}

/******************************************************************************/
/*!
	@brief try to get the licenseObject from the ldap object referenced by licenseDN
	@param licenseDN the ldap Object you want to get
	
	@return Pointer to a lObj if found, or NULL if an error has occurred.
*/
lObj* univention_license_ldap_get_licenseObject(const char* licenseDN)
{
	lObj* ret=NULL;
	int scope    = LDAP_SCOPE_BASE;
	char* filter = NULL;
	int filter_len;	
	char* attr[] = {NULL};		
	
	//build searchfilter
	filter_len = strlen("objectClass=univentionLicense");
	filter = malloc(sizeof(char) * filter_len + 1);
	filter[filter_len] = 0;
	sprintf(filter,"objectClass=univentionLicense");
		
	ret = univention_license_ldap_get(licenseDN, scope, filter, attr, "univentionLicense", 0);
	
    free(filter);
	return ret;
}

/******************************************************************************/
/*! 
	@brief get one or more strings form the ldap object attribute referenced by objectDN

	@param objectDN the referenced ldap Object DN
	@param attribute the selected ldap attribute name
	
	@retval	NULL	if attribute is not found
	@return lStrings a struct with num as the size of the line[] array of char*
*/
lStrings* univention_license_ldap_get_strings(const char* objectDN, const char* attribute)
{
	lStrings* ret = NULL;
	int numRet = 0;
	lObj* license = NULL;
	
	char* filter;
	int filterLen;
	char* attr[2];
	int scope = LDAP_SCOPE_BASE;
	
	filterLen = strlen(attribute) + strlen("=*");
	filter = malloc(sizeof(char) * (filterLen+1));
	sprintf(filter,"%s=*",attribute);
	filter[filterLen] = 0;
	
	attr[0] = (char *)attribute;
	attr[1] = NULL;
		
	license = univention_license_ldap_get(objectDN, scope, filter, attr, attribute, 0);
	
	if (license != NULL)
	{
		if (license->size > 0)
		{
			int i = 0;
			int count = 0;
			for (i=0; i < license->size; i++)
			{
				//count entries
				if (strcmp(license->key[i],attribute) == 0)
					count++;
			}
			if (count > 0)
			{
				ret = univention_licenseStrings_malloc(count);
				
				i=0;
				while (i < license->size && numRet < ret->num)
				{
					if (strcmp(license->key[i],attribute) == 0)
					{
						//copy strings
						ret->line[numRet++] = strdup(license->val[i]);
					}
					i++;
				}
			}
		}
		univention_licenseObject_free(license);
	}
	else
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "Can't get Attribute '%s' from Object '%s'.",attribute, objectDN);

    free(filter);
	return ret;
}

/******************************************************************************/
/*!
	@brief make a ldap search with the given parameters and convert a possible
	found ldap-licenseObject to a lObj.

	The ldap attributes must begin with 'univentionLicense' to get converted to c.
	The keys of the lObj will be sorted alphanumeric before return, so the
	data of a lObj will be always is the same order, this is nesseary for the 
	signature stuff.
	To be able to get a 2nd or 3rd Object the number of Objects to skip can be set.
	If you want to get the first Object set num to 0.
	
	@param search_base	the ldapsearch base
	@param scope		the ldapsearch scope level
	@param filter		the ldapsearch filter
	@param attr			the ldapsearch attribute filter
	@param attrFilter	filter all attributes that not begin with this
	@param num			the number of result objects to skip

	@return Pointer to a lObj if found, or NULL if an error has occurred.
*/
lObj* univention_license_ldap_get(const char* search_base, int scope, const char* filter, char** attr, const char* attrFilter, int num)
{
	lObj* ret=NULL;
	if (univention_license_ldap_open_connection())
	{
		LDAPMessage	*result = NULL;
		struct  timeval	timeout;
		int		rc;
		int		count;
		
		LDAPMessage	*element;
	
		timeout.tv_sec=3;
		timeout.tv_usec=0;
		
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "LDAPSearch: searchBaseDN '%s', scope '%i' filter '%s' attr[0] '%s'",search_base, scope, filter, attr[0]);
		if ((rc = ldap_search_ext_s(lp->ld, search_base, scope, filter, attr, 0, NULL, NULL, &timeout, 0, &result)) != LDAP_SUCCESS)
		{
			if ( rc == LDAP_NO_SUCH_OBJECT ) 
			{
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "Not found:%s. Filter:%s. LDAP_NO_SUCH_OBJECT", search_base, filter);
			}
			else
			{
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "Not found:%s. Filter:%s.", search_base, filter);
			}			
			ldap_msgfree(result);
			result = NULL;
		}
		else
		{
			count = ldap_count_entries(lp->ld, result);
			if ( count > 0 )
			{
				int valuecount = 0;
				char* attributeName = NULL;
				BerElement* ber_walker;
				
				if (count > 1)
				{
					univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "Found %d entries expected only 1 use the 1st.",count);
				}
				element = ldap_first_entry(lp->ld, result);
				
				if (num > 0)
				{
					if (count > num)
					{
						//skip num elements first
						while (element != NULL && num > 0)
						{
							element = ldap_next_entry(lp->ld, element);
							num--;
						}
					}
					else
					{
						element = NULL; //someone has skipped all elements
					}
				}
				
				if (element != NULL) //is there a element anymore?
				{
					/* count values*/
					for (attributeName = ldap_first_attribute(lp->ld, element, &ber_walker);
						 attributeName != NULL;
						 attributeName = ldap_next_attribute(lp->ld, element, ber_walker))
					{
						if (strncmp(attrFilter,attributeName,strlen(attrFilter)) == 0)
						{
							struct berval** values=NULL;
							values = ldap_get_values_len(lp->ld, element, attributeName);
							
							if ( values != NULL)
							{
								valuecount+= ldap_count_values_len(values);
							}
						}
						else
						{
							univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_INFO, "Ignore object attribute '%s' because it don't begin with '%s'.", attributeName, attrFilter);
						}
					}
					
					/*store key and val in license*/
					if (valuecount > 0)
					{
						int i = 0;
						ret = univention_licenseObject_malloc(valuecount);
						
						/*convert LDAPMessage to C Object*/
						for (attributeName = ldap_first_attribute(lp->ld, element, &ber_walker);
							 attributeName != NULL;
							 attributeName = ldap_next_attribute(lp->ld, element, ber_walker))
						{
							if (strncmp(attrFilter,attributeName,strlen(attrFilter)) == 0)
							{
								struct berval** values = NULL;

								values = ldap_get_values_len(lp->ld, element, attributeName);
								if ( values != NULL)
								{
									int count = ldap_count_values_len(values);
									int x = 0;
									while (x < count)
									{
										ret->key[i] = strdup(attributeName);
										ret->val[i] = strdup(values[x]->bv_val);
										//printf("%p:key[%i]:%s.\n",ret->key[i],i,ret->key[i]);
										//printf("%p:val[%i]:%s.\n",ret->val[i],i,ret->val[i]);
										i++;
										x++;
									}
									ldap_value_free_len( values );
								}
							}
						}
					}
					else
						univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "LDAP-Element has 0 attributes!");
				}
			}
			else
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "The LDAP-Result has 0 elements, this should be normal if nothing is found." );
		}
		/*WARNING!!! only free a ldapmessage after you have all you need from, this
		cleans all, also subparts of the message!!!*/
		if (result != NULL)
		{
			ldap_msgfree(result);
			result = NULL;
		}
	}
	return ret;
}
/*eof*/
