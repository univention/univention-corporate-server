#include "internal.h"
/*! @file license.c
	@brief general lib license functions
*/

static lObj* global_license = NULL; /*!< the container for the current selected license*/
static int is_init = 0;/*!< the init-state of the lib*/

/*****************************************************************************/
/*!
	@brief	init the licenselib, is called automatic.
	@retval 1 if all parts are initiated successful
	@retval 0 if an error has occurred
*/
int univention_license_init(void)
{
	if (is_init)
		return 1;
	
	is_init = 1;
	
	/*init debug*/
	univention_debug_init( "stderr", UV_DEBUG_FLUSH, UV_DEBUG_NO_FUNCTION);
	univention_debug_set_level (UV_DEBUG_LDAP, UV_DEBUG_ERROR);
	univention_debug_set_level (UV_DEBUG_LICENSE, UV_DEBUG_ERROR);
	univention_debug_set_level (UV_DEBUG_SSL, UV_DEBUG_ERROR);
	
	/*init ldap*/
	is_init &= univention_license_ldap_init();
	
	/*init public key*/
	is_init &= univention_license_key_init();
	
	return is_init;
}

/*****************************************************************************/
/*!
	@brief	cleanup the license lib
*/
void univention_license_free(void)
{
	univention_license_ldap_free();
	univention_license_key_free();
	if (global_license != NULL)
	{
		univention_licenseObject_free(global_license);
		global_license = NULL;
	}
}

lObj* univention_license_get_global_license(void)
{
	return global_license;
}

/*****************************************************************************/
/*!
	@brief	try to find a license from this type out of the ldap server

	this is the common client function.
	it does the common checks(date,basedn,signature) before returning a license.
	the a license of this type will be searched in all paths defined in univentionLicenseObject
	in 'cn=directory,cn=univention,[basedn]'.

	@param	licensetyp the value of 'univentionLicenseModule' that the wished license must have
	@retval -1 no license object found
	@retval 0 if a valid license of this type has been found
	@retval 1 the signature test has failed
	@retval 2 the date test has failed
	@retval 4 the basedn test has failed 
*/
int univention_license_select(const char* licensetyp)
{
	int ret = -1;
	//check init
	if (univention_license_init())
	{
		char* directoryDN = NULL;
		lStrings* searchPath = NULL;
		char* baseDN = univention_license_ldap_get_basedn();
		int len = 0;
		
		//clean old global_licese
		if (global_license != NULL)
		{
			univention_licenseObject_free(global_license);
			global_license = NULL;
		}
		
		//build directoryDN
		len = strlen(baseDN) + strlen("cn=directory,cn=univention,");
		directoryDN = malloc(sizeof(char) * (len+1));
		sprintf(directoryDN, "cn=directory,cn=univention,%s", baseDN);
        
		//find location of licenses
		if ( (searchPath = univention_license_ldap_get_strings(directoryDN, "univentionLicenseObject") ) == NULL ) {
			free(directoryDN);
			len = strlen(baseDN) + strlen("cn=default containers,cn=univention,");
			directoryDN = malloc(sizeof(char) * (len+1));
			sprintf(directoryDN, "cn=default containers,cn=univention,%s", baseDN);
			directoryDN[len] = 0;
			searchPath = univention_license_ldap_get_strings(directoryDN, "univentionLicenseObject");
		}
		if (searchPath != NULL)
		{
			int i=0;
			if (searchPath->num > 0)
			{
				while (i < searchPath->num && global_license == NULL)
				{
					int licenseNum = 0;
					int license_found = 0;
					//printf("Search:%s.\n",searchPath->line[i]);
					do
					{
						license_found = 0;
						//get the license
						global_license = univention_license_ldap_search_licenseObject(searchPath->line[i], licensetyp, licenseNum);
						if (global_license != NULL)
						{
							int valid = 1;
							license_found = 1;
							licenseNum++; //count the found licenses so they will be skipped the in the next request for this searchpath
							
							ret = 0;
							if (!univention_license_check_signature()) {
								ret += 1;
								valid &= 0;
							}
							if (!univention_license_check_enddate()) {
								ret += 2;
								valid &= 0;
							}
							if (!univention_license_check_basedn()) {
								ret += 4;
								valid &= 0;
							}
							
							if (!valid)
							{
								univention_licenseObject_free(global_license);
								global_license = NULL;
								univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "The license found is invalid!");
							}
						}
					}
					while(license_found && global_license == NULL);
					i++;
				}
				
				//do we finally found a license?
				if (NULL == global_license)
				{
					univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "No license of type '%s' found at:",licensetyp);
					for (i=0; i < searchPath->num; i++)
						univention_debug(UV_DEBUG_LDAP, UV_DEBUG_INFO, "->%s",searchPath->line[i]);
				}
			}
			else
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "The location of licenses %s doesn't contain any paths.",directoryDN);
							
			univention_licenseStrings_free(searchPath);
			searchPath = NULL;
		}
		else
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "Could not retrieve the location of licenses from: %s.",directoryDN);
		
		//cleanup
		free(directoryDN);
	}
	return ret;
}

/*****************************************************************************/
/*!
	@brief	try to find a license at the given licenseDN

	it does the common checks(date,basedn,signature) before returning a license.
	if no license is found the global_license won't be touched

	@param	licenseDN the location of the wished licnese
	@retval	1 if nothing is found or an error has occurred
	@retval 0 if a valid license of this type has been found
*/
int univention_license_selectDN(const char* licenseDN)
{
	int ret = 1;
	//check init
	if (univention_license_init())
	{
		lObj* tempLicense = NULL;
		tempLicense = univention_license_ldap_get_licenseObject(licenseDN);
		if (tempLicense != NULL)
		{
			int valid = 1;
			valid &= univention_license_check_signature();
			valid &= univention_license_check_basedn();
			valid &= univention_license_check_enddate();
			
			if (!valid)
			{
				univention_licenseObject_free(tempLicense);
				tempLicense = NULL;
				univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "The license found is invalid!");
			}
			else
			{
				//clean old global_licese
				if (global_license != NULL)
					univention_licenseObject_free(global_license);
				//setup new license
				global_license = tempLicense;
				ret = 0;
			}
		}
		else
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "No license found at '%s'",licenseDN);
	}
	return ret;
}

/*****************************************************************************/
/*!
	@brief check the license at objectDN
	@param objectDN 
	@retval -1 the object can not be found or is no license object
	@retval 0 the license is valid and has passed all tests
	@retval 1 the signature test has failed
	@retval 2 the date test has failed
	@retval 4 the basedn test has failed 
	@retval 8 the object can not be found, it's not in the search path
	
*/
int univention_license_check(const char* objectDN)
{
	int ret = -1;
	if (univention_license_init())
	{
		lObj* backup = global_license;
		global_license = univention_license_ldap_get_licenseObject(objectDN);
		
		if (global_license != NULL)
		{
			ret = 0;
			if (!univention_license_check_signature())
				ret += 1;
			if (!univention_license_check_enddate())
				ret +=2;
			if (!univention_license_check_basedn())
				ret +=4;
			if (!univention_license_check_searchpath(objectDN))
				ret +=8;
			univention_licenseObject_free(global_license);
			global_license = NULL;
		}
		global_license = backup;
	}
	return ret;
}
/*****************************************************************************/
/*!
	@brief	check the licence baseDN against the local baseDN

	this function use the global_license Object
	@retval 0 if an error has occurred
	@retval 1 if everything is fine
*/
int univention_license_check_basedn()
{
	int ret = 0;
	if (global_license != NULL)
	{
		char* baseDN = univention_license_ldap_get_basedn();
		lStrings* licenseBaseDN = univention_license_get_value("univentionLicenseBaseDN");
		
		if (licenseBaseDN != NULL && baseDN != NULL)
		{
			/* check for UCS Core edition */
			if ((strlen(licenseBaseDN->line[0]) == strlen("UCS Core Edition"))) {
				if (strcmp(licenseBaseDN->line[0], "UCS Core Edition") == 0) {
					ret = 1;
				}
			}

			/* check for free for personal use edition */
			if ((strlen(licenseBaseDN->line[0]) == strlen("Free for personal use edition"))) {
				if (strcmp(licenseBaseDN->line[0], "Free for personal use edition") == 0) {
					ret = 1;
				}
			}

			if ((strlen(licenseBaseDN->line[0]) == strlen(baseDN))) {
				if (strcasecmp(licenseBaseDN->line[0], baseDN) == 0) {
					ret = 1;
				}
			}
			
			if (ret == 0) {
				univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "This License is limited to the Base DN '%s' but the Base DN of your system is '%s'.",licenseBaseDN->line[0],baseDN);
			}
		}
		else {
			univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "Value Error: baseDN:%s, LicenseBaseDN:%s.",baseDN,licenseBaseDN->line[0]);
		}
		
		univention_licenseStrings_free(licenseBaseDN);
		licenseBaseDN = NULL;
	}
	else
		univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "No license selected.");
		
	return ret;
}

/*****************************************************************************/
/*!
	@brief	check the licence end date against the current date
	
	this function use the global_license Object
	@retval 0 if an error has occurred
	@retval 1 if everything is fine
*/
int univention_license_check_enddate()
{
	if (global_license != NULL)
	{
		lStrings* licensedate = univention_license_get_value("univentionLicenseEndDate");
		
		if (licensedate != NULL)
		{
			if (strcmp(licensedate->line[0],"unlimited") == 0)
			{
				return 1;
			}
			else
			{
				int endDay = 0, endMonth = 0, endYear = 0;
				time_t cur_time;
				struct tm tim;
				char *s;
				char* date = strdup(licensedate->line[0]); //must be done because strtok modifies

				if ( (s = strtok(date, ".")) == NULL ) {
					free(date);
					return 0;
				} else {
					endDay  = atoi(s);
					univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_INFO, "EndDay %d",endDay);
				}
				if ( (s = strtok(NULL,".")) == NULL ) {
					free(date);
					return 0;
				} else {
					endMonth= atoi(s);
					univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_INFO, "EndMonth %d",endMonth);
				}
				if ( (s = strtok(NULL,".")) == NULL ) {
					free(date);
					return 0;
				} else {
					endYear = atoi(s);
					univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_INFO, "EndYear %d",endYear);
				}

				free(date);
				
				cur_time = time(NULL);
				localtime_r(&cur_time, &tim);
			
				if ( (endYear-1900) >  tim.tm_year ) {
					return 1;
				} else if ( (endYear-1900)  < tim.tm_year ) {
					univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_INFO, "This License expired on '%s'. Current date is '%i.%i.%i'.(year)",licensedate->line[0],tim.tm_mday,tim.tm_mon+1,tim.tm_year+1900);
					return 0;
				} else {
					/* same year */
					if (endMonth > (tim.tm_mon+1)) {
						return 1;
					} else if ( endMonth <  (tim.tm_mon+1) ) {
						univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_INFO, "This License expired on '%s'. Current date is '%i.%i.%i'.(month)",licensedate->line[0],tim.tm_mday,tim.tm_mon+1,tim.tm_year+1900);
						return 0;
					} else {
						/* same month */
						if (endDay > tim.tm_mday) {
							return 1;
						} else if ( endDay < tim.tm_mday) {
							univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_INFO, "This License expired on '%s'. Current date is '%i.%i.%i'.(day)",licensedate->line[0],tim.tm_mday,tim.tm_mon+1,tim.tm_year+1900);
							return 0;
						} else {
							/* same day */
							return 1;
						}

					}
				}

			}	
		}
		univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "This License is invalid because it lacks the attribute EndDate!");
		univention_licenseStrings_free(licensedate);
		licensedate = NULL;
	}
	else
		univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "No license selected.");
	return 0;
}

/*****************************************************************************/
/*!
	@brief check if a objectDN is inside the directory searchpath
	@param objectDN the DN to check
	@retval 1 if ok
	@retval 0 on error
*/
int univention_license_check_searchpath(const char* objectDN)
{
	int found = 0;

	/* FIXME: the reinvented strcmp below is of course not suitable 
	 * to check if the objectDN is in the search path
	 *
	 * disabled for now
	 */
	return 1;
	
	if (univention_license_init())
	{
		char* directoryDN = NULL;
		int len = 0;
		lStrings* searchPath = NULL;
		char* baseDN = univention_license_ldap_get_basedn();
		
		//build directoryDN
		len = strlen(baseDN) + strlen("cn=directory,cn=univention,");
		directoryDN = malloc(sizeof(char) * (len+1));
		sprintf(directoryDN, "cn=directory,cn=univention,%s", baseDN);
		directoryDN[len] = 0;
		
		//find location of licenses
		if ( (searchPath = univention_license_ldap_get_strings(directoryDN, "univentionLicenseObject") ) == NULL ) {
			free(directoryDN);
			len = strlen(baseDN) + strlen("cn=default containers,cn=univention,");
			directoryDN = malloc(sizeof(char) * (len+1));
			sprintf(directoryDN, "cn=default containers,cn=univention,%s", baseDN);
			directoryDN[len] = 0;
			searchPath = univention_license_ldap_get_strings(directoryDN, "univentionLicenseObject");
		}

		if (searchPath != NULL)
		{
			int i=0;
			if (searchPath->num > 0)
			{
				while (i < searchPath->num && !found)
				{
					if (strlen(searchPath->line[i]) < strlen(objectDN))
					{
						//compare the objectDN with the searchpath,  beginning at the end of the strings
						int x = 0;
						int sLen = strlen(searchPath->line[i]);
						int oLen = strlen(objectDN);
						
						found = 1;
						while ((oLen - x) >= 0 && (sLen - x ) >= 0 && found)
						{
							x++;
							if ((searchPath->line[i][sLen-x] != objectDN[oLen-x]))
								found = 0;
						}
					}
					i++;
				}
				if (!found)
					univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "The ObjectDN(%s) is not inside the searchPaths of licenses.",objectDN);
			}
			else
				univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "The location of licenses %s doesn't contain any paths.",directoryDN);
			univention_licenseStrings_free(searchPath);
			searchPath = NULL;
		}
		else
			univention_debug(UV_DEBUG_LDAP, UV_DEBUG_ERROR, "Could not retrieve the location of licenses from: %s.",directoryDN);
		free(directoryDN);
	}
	return found;
}


/*****************************************************************************/
/*!
	@brief	the sort function for qsort

	the license is sorted primary with the key and if this makes not
	clean answer value is compared too.

	@param	a	the 1st sortElement
	@param	b	the 2nd sortElement
	
	@retval	1	if a is 'smaller' than b
	@retval	0	if both strings are equal
	@retval	-1	if a is 'greater' then b
*/
int univention_license_qsort_hook(sortElement* a, sortElement* b)
{
	int ret = 0;
	ret = univention_license_compare_string(a->key,b->key);
	if (ret == 0)
		ret = univention_license_compare_string(a->val,b->val);
	return ret;
}

/*****************************************************************************/
/*!
	@brief	compare two strings and return qsort compatible results
	
	in the first step the strings are compared direct
	if no difference is found the strlen will be compared
	
	@param	a	the 1st string
	@param	b	the 2nd string

	@retval	1	if a is 'smaller' than b
	@retval	0	if both strings are equal
	@retval	-1	if a is 'greater' then b
*/
int univention_license_compare_string(const char* a, const char* b)
{
	int i = 0;
	while (i < strlen(a) && i < strlen(b))
	{
		if (a[i] < b[i])
			return -1;
		else
			if (a[i] > b[i])
				return 1;
			else
				i++;
	}
	if (strlen(a) < strlen(b))
		return -1;
	else
		if (strlen(a) > strlen(b))
			return 1;
	return 0;
}

/*****************************************************************************/
/*!
	@brief	sort the key, value pairs of a license

	this is used to get the license in always the same order,
	so the data for a signature task will be always the same
	there is no data move/copy inside, only pointer transfer,
	so if you clean the unsorted license, the sorted will get invalid too.

	@param	license object to sort
	@retval	ptr the sorted license
*/
lObj* univention_license_sort(lObj* license)
{
	int size = license->size;
	if (size > 1)
	{
		int i;
		sortElement* sortarray = NULL;
		//printf("DEBUG:do a sort with %i elements.\n",size);
		
		sortarray = malloc(sizeof(sortElement) * size);
		for (i=0; i < size; i++)
		{
			sortarray[i].key = license->key[i];
			sortarray[i].val = license->val[i];
		}
		//do the sort
		qsort(&sortarray[0], size, sizeof(sortElement), (void*)univention_license_qsort_hook);

		for(i=0; i < license->size; i++)
		{
			license->key[i] = sortarray[i].key;
			license->val[i] = sortarray[i].val;
		}
		
		free(sortarray);
	}
	return license;
}

/*****************************************************************************/
/*!
	@brief	allocate the memory for a new lObj and initialize all ptrs to NULL
	@param	size	the number of parameters that should be stored in this object
	@retval	ptr the new allocated lObj structure
	@todo	do malloc error handling
*/
lObj* univention_licenseObject_malloc(int size)
{
	lObj* license = NULL;
	license = malloc(sizeof(lObj));
	//printf("LicenseMalloc:%i,%p.\n",size,license);
	
	license->size = size;
	license->key  = calloc(size, sizeof(char*));
	license->val  = calloc(size, sizeof(char*));
	return license;
}


/*****************************************************************************/
/*!
	@brief	allocate the memory for a new lStrings Object and initialize all ptrs to NULL
	@param	num	the number of lines the shoulb be stored later inside.
	@retval	ptr the new allocated lStrings structure
	@todo	do malloc error handling
*/
lStrings* univention_licenseStrings_malloc(int num)
{
	lStrings* ret = NULL;
	if (num > 0)
	{
		ret = malloc(sizeof(lStrings));
		ret->num = num;
		ret->line = calloc(ret->num, sizeof(char*));
	}
	
	return ret;
}

/*****************************************************************************/
/*!
	@brief	cleanup a lStrings Object, please use this for all lStrings* you get from the lib
	@param	strings the lStrings Object to cleanup
*/
void univention_licenseStrings_free(lStrings* strings)
{
	if (strings != NULL)
	{
		int i=0;
		for (i=0; i < strings->num; i++)
		{
			if (strings->line[i] != NULL)
			{
				free(strings->line[i]);
				strings->line[i] = NULL;
			}	
		}
		free(strings->line);
		free(strings);
	}
}

/*****************************************************************************/
/*!
	@brief	cleanup a lObj, please use this for all lObj* you get from the lib
	@param	license the lObj to clean up
*/
void univention_licenseObject_free(lObj* license)
{
	//printf("LicenseFree:%i,%p,%s,%s.\n",license->size,license,license->key[0],license->val[0]);
	if (license != NULL)
	{
		int i;
		int size = license->size;
		for(i=0; i < size; i++)
		{	
			//key
			if (license->key[i] != NULL)
			{
				//printf("free(%p)license->key[%i]:%s\n",license->key[i],i,license->key[i]);
				free(license->key[i]);
				license->key[i] = NULL;
			}
			//value
			if (license->val[i] != NULL)
			{
				//printf("free(%p)license->val[%i]:%s\n",license->val[i],i,license->val[i]);
				free(license->val[i]);
				license->val[i] = NULL;
			}
		}
		free(license->key);
		free(license->val);
		//printf("free(%p)license.\n",license);
		free(license);
	}
}
/*****************************************************************************/
/*!
	@brief	extract the value of this attribute from the license
	
	this function use the global_license Object	
	@param	attribute	attributeName of the value that should be returned
		the attributeName is the same like the ldapAttributeName
	@retval	NULL	if attribute is not found
	@return lStrings a struct with num as the size of the line[] array of char*
*/
lStrings* univention_license_get_value(const char* attribute)
{
	lStrings* value = NULL;
	if (global_license != NULL)
	{
		int i=0;
		int count=0;
		//count elements
		while (i < global_license->size)
		{
			if (strcmp((global_license->key[i]),attribute) == 0)
				count++;
			i++;
		}
		
		if (count > 0)
		{
			//allocate mem
			value = univention_licenseStrings_malloc(count);
			
			//copy value
			count = 0;
			i = 0;
			while (i < global_license->size && count < value->num)
			{
				if (strcmp((global_license->key[i]),attribute) == 0)
				{
					value->line[count++] = strdup(global_license->val[i]);
				}
				i++;
			}
		}
		else
			univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_WARN, "Key \"%s\" not found in license object.",attribute);
	}
	else
		univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "No license selected. Can't get Values..");
	return value;
}
/*eof*/
