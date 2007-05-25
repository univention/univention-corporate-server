/*! @file license_ldap.c
	@brief the ldap functions for the license lib
*/

#include <univention/license.h>

/* SGO: Besser waere eine struct, und warum sind die Variablen nicht static? */

/*! ldap_connection the global ldap connection*/
LDAP* ldap_connection = NULL; 
/*! ldap_server ldap server ip/host*/
char* ldap_server = NULL;
/*! ldap_port the ldap server port*/
int   ldap_port = 0;
/*! the baseDN of the ldap server*/
char* baseDN = NULL;

/******************************************************************************/
/*!
	@brief initialitze the ldap part of the lib, automatic called if need
	@todo remove the debug functions, in the moment the ldap server is alway testing.
	
	@retval 1 if succeed
	@retval 0 on error
*/
int univention_license_ldap_init(void)
{
	/*get config from univention-baseconfig*/	
	ldap_server= univention_config_get_string("ldap/server/name");
	ldap_port  = univention_config_get_int("ldap/port");
	
	/*open ldap connection*/
	if (ldap_connection == NULL)
	{
		if (!univention_license_ldap_open_connection())
		{
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "Can't open LDAP Connection.");
			return 0;
		}
		univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "Connected to:%s:%i. BaseDN:%s.",ldap_server,ldap_port,univention_license_ldap_get_basedn());
	}
	
	//get the baseDN from LDAPServer
	if (!univention_license_ldap_get_basedn())
		return 0;
	
	return 1;
}

/******************************************************************************/
/*!
	@brief	close the ldap connection and clean up all ldap stuff
	this is called automatic from univention_license_free()
*/
void univention_license_ldap_free(void)
{
	univention_license_ldap_close_connection();
	if (ldap_server != NULL)
		free(ldap_server);
	if (baseDN != NULL)
		free(baseDN);
}

/******************************************************************************/
/*!
	@brief	get the baseDN of the ldap server
	@retval 1 if ok
	@retval 0 on error
*/
char* univention_license_ldap_get_basedn(void)
{
	
	if (baseDN == NULL)
	{
		lStrings* strings = NULL;
		strings = univention_license_ldap_get_strings("", "namingContexts");
		if (strings != NULL)
		{
			if (strings->num > 0)
			{
				baseDN = strdup(strings->line[0]);
			}
			else
				univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "Can't get the BaseDN from LDAP-Server!");
			univention_licenseStrings_free(strings);
			strings = NULL;
		}
		else
			univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "Can't get strings from LDAP-Server!");
	}
	return baseDN;
}

/******************************************************************************/
/*!
	@brief	open a connection to the ldap server, with the connection data recived from univention_baseconfig
	@retval	1	if the connection was already open or was opened successfull
	@retval	0	if an error has occured
*/
int univention_license_ldap_open_connection(void)
{
	if (ldap_connection != NULL)
		return 1;
	else
	{		
		int	version = LDAP_VERSION3;
		int	rc;
	
		if (( ldap_connection = ldap_init( ldap_server, ldap_port )) == NULL )
		{
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "Can't connect to LDAP-Server(%s:%i).",ldap_server,ldap_port);
			return 0;
		}
	
		ldap_set_option(ldap_connection, LDAP_OPT_PROTOCOL_VERSION, &version );
	
        /* Keine Moeglichkeit irgendwie eine Bind DN und ein Pwd mitzugeben? */
		if ( ( rc = ldap_bind_s(ldap_connection, NULL, NULL, LDAP_AUTH_SIMPLE ) ) != LDAP_SUCCESS )
		{
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "Can't bind LDAP Connection. Error:%s|%d.",ldap_err2string(rc),rc);
			ldap_unbind( ldap_connection );
			ldap_connection = NULL;
			return 0;
		}
		return 1;
	}
}

/******************************************************************************/
/*!
	@brief close the possible open connection to the ldap server,
	is automatic called by univention_license_ldap_free().
*/
void univention_license_ldap_close_connection(void)
{
	if (ldap_connection != NULL)
	{
		ldap_unbind( ldap_connection );
		ldap_connection = NULL;
	}
}

/******************************************************************************/
/*! @brief search a licenseObject with a specific type in the searchBaseDN ldap path
	
	@param searchBaseDN	the ldap path where a licenseObject is searched
	@param licensetyp	the requested license type (the ldap attribute univentionLicenseModule have this value)
	@param num	the number of found objects to skip at first, so you can get the 2nd or 3rd one.
	
	@return Pointer to a lObj if found, or NULL if an error has occured.
*/
lObj* univention_license_ldap_search_licenseObject(char* searchBaseDN, char* licensetyp, int num)
{
	lObj* ret=NULL;
	char* filter;
	int filter_len;
	char* attr[] = {NULL};
	int scope    = LDAP_SCOPE_ONELEVEL;
	
	//build searchfilter
	filter_len = strlen("univentionLicenseModule=") + strlen(licensetyp);
	filter = malloc(sizeof(char) * filter_len + 1);
	filter[filter_len] = 0;
	sprintf(filter,"univentionLicenseModule=%s", licensetyp);
	
	ret = univention_license_ldap_get(searchBaseDN, scope, filter, attr, "univentionLicense", num);
	
	free(filter);
	return ret;
}

/******************************************************************************/
/*!
	@brief try to get the licenseObject from the ldap object referenced by licenseDN
	@param licenseDN the ldap Object you want to get
	
	@return Pointer to a lObj if found, or NULL if an error has occured.
*/
lObj* univention_license_ldap_get_licenseObject(char* licenseDN)
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
lStrings* univention_license_ldap_get_strings(char* objectDN, char* attribute)
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
	
	attr[0] = attribute;
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
				//count entrys
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
	@brief make a ldap search with the given parametes and convert a possible
	found ldap-licenseObject to a lObj.

	The ldap attributes must begin with 'univentionLicense' to get converted to c.
	The keys of the lObj will be sorted alphanumeric before return, so the
	data of a lObj will be alway is the same order, this is nesseary for the 
	signature stuff.
	To be able to get a 2nd or 3rd Object the number of Objects to skip can be set.
	If you want to get the first Object set num to 0.
	
	@param search_base	the ldapsearch base
	@param scope		the ldapsearch scope level
	@param filter		the ldapsearch filter
	@param attr			the ldapsearch attribute filter
	@param attrFilter	filter all attributes that not begin with this
	@param num			the number of result objects to skip

	@return Pointer to a lObj if found, or NULL if an error has occured.
*/
lObj* univention_license_ldap_get(char* search_base, int scope, char* filter, char** attr, char* attrFilter, int num)
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
		
		//univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "LDAPSearch: searchBaseDN '%s', scope '%i' filter '%s' attr[0] '%s'",search_base, scope, filter, attr[0]);
		if ((rc = ldap_search_st(ldap_connection, search_base, scope, filter, attr, 0, &timeout, &result)) != LDAP_SUCCESS)
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
			count = ldap_count_entries(ldap_connection, result);
			if ( count > 0 )
			{
				int valuecount = 0;
				char* attributeName = NULL;
				BerElement* ber_walker;
				
				if (count > 1)
				{
					univention_debug(UV_DEBUG_LDAP, UV_DEBUG_WARN, "Found %d entrys expected only 1 use the 1st.",count);
				}
				element = ldap_first_entry(ldap_connection, result);
				
				if (num > 0)
				{
					if (count > num)
					{
						//skip num elements first
						while (element != NULL && num > 0)
						{
							element = ldap_next_entry(ldap_connection, element);
							num--;
						}
					}
					else
					{
						element = NULL; //someone has skiped all elements
					}
				}
				
				if (element != NULL) //is there a element anymore?
				{
					/* count values*/
					for (attributeName = ldap_first_attribute(ldap_connection, element, &ber_walker);
						 attributeName != NULL;
						 attributeName = ldap_next_attribute(ldap_connection, element, ber_walker))
					{
						if (strncmp(attrFilter,attributeName,strlen(attrFilter)) == 0)
						{
							char** values=NULL;
							values = ldap_get_values(ldap_connection, element, attributeName);
							
							if ( values != NULL)
							{
								valuecount+= ldap_count_values(values);
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
						for (attributeName = ldap_first_attribute(ldap_connection, element, &ber_walker);
							 attributeName != NULL;
							 attributeName = ldap_next_attribute(ldap_connection, element, ber_walker))
						{
							if (strncmp(attrFilter,attributeName,strlen(attrFilter)) == 0)
							{
								char** values=NULL;
								values = ldap_get_values(ldap_connection, element, attributeName);
								if ( values != NULL)
								{
									int count = ldap_count_values(values);
									int x = 0;
									while (x < count)
									{
										ret->key[i] = strdup(attributeName);
										ret->val[i] = strdup(values[x]);
										//printf("%p:key[%i]:%s.\n",ret->key[i],i,ret->key[i]);
										//printf("%p:val[%i]:%s.\n",ret->val[i],i,ret->val[i]);
										i++;
										x++;
									}
									ldap_value_free( values );
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
