#include "internal.h"
/*! @file license_signature.c
	@brief functions for sign and verify license objects
*/

/******************************************************************************/
/*!
	@brief	builds a data string from a license,
	used for the sign and verify mechanism, to generate the data for the hashing
	@param	license	the license object where the data to build from
	@retval NULL pointer if the licenseObject is empty
	@retval pointer to the data string if succeed
*/
char* univention_license_build_data(lObj* license)
{
	int len = 0;
	int pos = 0;
	int i;
	char* data = NULL;
	
	//sort entries
	license = univention_license_sort(license);
	
	for (i=0; i < license->size; i++)
	{
		if (!(strcmp(license->key[i],"univentionLicenseSignature") == 0))
			len += strlen(license->val[i])+1;
	}
	
	if (len > 0)
	{
		data = malloc(sizeof(char)*len+1);
		memset(data,0,sizeof(char)*len+1);
		
		for (i=0; i < license->size; i++)
		{
			if (!(strcmp(license->key[i],"univentionLicenseSignature") == 0))
			{
				//debug
				//printf("%i,%i:%s.\n",i,strlen(license[i]),license[i]);
				
				sprintf(&(data[pos]),"%s\n", license->val[i]);
				pos += (strlen(license->val[i]) + 1);				
			}
		}
		data[pos] = 0;
	}
	else
	{
		univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_WARN, "License is empty! Can't create data.");
	}
	return data;
}

/******************************************************************************/
/*!
	@brief	check the siganture of the global_license

	the data to hash of this license will be generated, also the
	signature is taken from this license.
	for the real signature check univention_license_verify() is called
	
	@retval	0 if license is not valid, or a error has occurred
	@retval 1 if license signature is valid
*/
int univention_license_check_signature()
{
	lObj* global_license = univention_license_get_global_license();
	if (global_license != NULL)
	{
		char* data = univention_license_build_data(global_license);
		int valid = 0;
		
		if (data != NULL)
		{
			lStrings* sign = univention_license_get_value("univentionLicenseSignature");
			if (sign != NULL)
			{
				valid = univention_license_verify(data, sign->line[0]);
				
				univention_licenseStrings_free(sign);
				sign = NULL;
			}
			else
				univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "License-Signature: can't get signature!");
			free(data);
		}
		else
			univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "License-Signature: can't get data!");
		
		if (valid)
			return 1;
	}
	univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "License-Signature test failed.");
	return 0;
}

/******************************************************************************/
/*!
	@brief	A ADMIN function! Try to generate the signature for the LDAP object at licenseDN
	@param	licenseDN	the path of the ldapLicenseObject that should be signed
	@retval	NULL if an error has occurred
	@retval char the base64 encoded signature
*/
char* univention_license_sign_license(const char* licenseDN)
{
	char* ret = NULL;
	lObj* license = NULL;
	license = univention_license_ldap_get_licenseObject(licenseDN);
	if (license != NULL)
	{
		char* data = NULL;
		data = univention_license_build_data(license);
		if (data != NULL)
		{
			ret = univention_license_sign(data);
			free(data);
		}
		univention_licenseObject_free(license);
	}
	else
		univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "Can't get licenseObject to sign from this dn:%s!",licenseDN);
	return ret;
}

/******************************************************************************/
/*!
	@brief	convert a base64 encoded string back to rawdata
	@param	base64data the string that should be converted
	@param	rawdata	the address to where the begin of the converted rawdata begins
	@retval	0	if an error has occurred
	@retval len	the amount of chars in returned rawdata
*/
unsigned int univention_license_base64_to_raw(const char* base64data, unsigned char** rawdata)
{
	unsigned int rawlen;
	char* temp=NULL;
	int templen;
	BIO* b64;
	BIO* mem;
	
	b64 = BIO_new(BIO_f_base64());//base64 encode BIO
	BIO_set_flags(b64, BIO_FLAGS_BASE64_NO_NL); //no newline
	
	mem = BIO_new_mem_buf((char *)base64data, -1);// BIO to read from mem
	BIO_set_close(mem, BIO_NOCLOSE);// So BIO_free() leaves BUF_MEM alone
	
	b64 = BIO_push(b64,mem); //connect b64 with mem, so b64 will read from mem
	
	//create temp memory
	templen = strlen(base64data);
	temp = malloc((templen+1)*sizeof(char));
		
	//convert from base64
	rawlen = BIO_read(b64, (void*)temp, templen);
	
	//allocate signature data buffer
	if (*rawdata != NULL)
	{
		univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_WARN, "RawData is not NULL! I free it.");
		free(*rawdata);
	}
	*rawdata = malloc(rawlen*sizeof(char));
	
	//copy data to return string
	memcpy(*rawdata, temp, rawlen*sizeof(char));
	
	//clean temp data
	free(temp);
	
	//cleanup BIOs
	BIO_free(mem);
	BIO_free(b64);
	return rawlen;
}

/******************************************************************************/
char* univention_license_raw_to_base64(const unsigned char* data, unsigned int datalen)
/*!
	@brief	convert raw data to base64
	@param	data	the char array that holds the data
	@param	datalen	the number of char that should be read from data
	@retval	pointer to base64 encoded data
*/
{
	long retlen=0;
	char* ret = NULL;
	BIO* b64;
	BIO* mem;
	
	b64 = BIO_new(BIO_f_base64());//base64 encode BIO
	BIO_set_flags(b64, BIO_FLAGS_BASE64_NO_NL); //no newline
	mem = BIO_new(BIO_s_mem());// memstorage BIO
	b64 = BIO_push(b64,mem); //connect b64 with mem, so write to b64 will write to mem
	
	//convert to base64
	BIO_write(b64, (void*)data, datalen);
	BIO_flush(b64);
	
	//calculate base64 data length, and allocate
	retlen = BIO_get_mem_data(mem, &ret);
	ret = malloc(sizeof(char)*(retlen+1));
	
	//get base64 encoded data
	BIO_read(mem,ret,retlen);
	
	//0 terminating
	ret[retlen] = 0;

	//cleanup BIOs
	BIO_free(mem);
	BIO_free(b64);
	return ret;
}
/*eof*/
