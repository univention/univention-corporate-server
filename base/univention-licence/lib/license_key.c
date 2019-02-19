#include "internal.h"
/*! @file license_key.c
	@brief key handling functions for lib license
*/

/*!the static number of included public key strings. change the number of public keys here*/
#define NUM_PUBLIC_KEYS 3

/*! the number of installed public keys */
static bool public_keys_installed = false;

/*! the array of loaded publicKeys */
static RSA** rsa_public = NULL;
/*! the array of public_key strings */
static char** public_keys = NULL;

/*! the loaded private key*/
static RSA* rsa_private = NULL;

/******************************************************************************/
/*!
	@brief	initalizte the keyhandling part of the lib
	
	this loads and inialitze all publickeys
	to add new public key add here the new publicKey strings.
	change #define NUM_PUBLIC_KEYS to the new number of public_keys
	example - the new keystring:
	public_keys[3] = strdup("the text from the publicKey file\n\
	with `\n\` at every line end. every!\n\
	");

	@retval 1 if successful
	@retval 0 on error
*/
int univention_license_key_init(void)
{
	public_keys = malloc(NUM_PUBLIC_KEYS * sizeof(char*));
	//setup public key strings
	/*add here new publicKeys*/
	/*don't forget to add '\n\' to each line end, and don't reformate the string.*/
	// _MASTER-KEY
	public_keys[0] = strdup("-----BEGIN RSA PUBLIC KEY-----\n\
MIIBCgKCAQEA0jQVFvjqhr2mEUPsG5g2kQA58uq7QMb0gFYOfhAQsQgMuhp2sjXs\n\
dkLG2QSLKhQf9RDZBbgZBffvU3DvRvafWVdX+iAR2AhYGy6pE5Mrj+iXgVcFrlxM\n\
DpVK5PF1N4iGwQpkMS6dgjgfVl+0b4kr99BCU+bZoc/t/KlmGoXVrfPNEZMKa2fQ\n\
bsHkPxTtGq2ylLP2JvGwlEOeUvsbm5H0iOUzDwl35fQYK3um19VKxCIMLvtV95fJ\n\
ZvoZYJYb3sbI0bq3pJxUi/nLi0p1xGYzxSA5nUf5FK53qFN+w9j6OA37URXo19Yj\n\
Ui0mrXNTr7ZiehGobPvKHBdBBtl7LuYLhQIDAQAB\n\
-----END RSA PUBLIC KEY-----\n\
");
	// _MASTER-KEY2
	public_keys[1] = strdup("-----BEGIN RSA PUBLIC KEY-----\n\
MIIBCgKCAQEA06fyc7AmDJg3nzCEB4vPHDBhkTJcMof5fdhWsp049JgQxCcXnbkF\n\
o10RBHT9TxlMjN4ZJ38QkMwh5E0wTc2A/CRqJkVjghTUllPY/MqciftcSyDI0bEf\n\
QEi9rUluomMO615+spmLOWBGcnYH3JJUkHwFOF/TYYkqZeFVbBqVtiGBOUXlSWbG\n\
BGAGVR15TfEuEUt0txjfQReIb+/d7/eiAbX/rgiaq0E1iHOT3Lbqi+sUId31ti6G\n\
3WmuNVln+b5k0YruC9T5IIoOud/lz6A8XaaAIS3eujulP79Xmw6yP+KVIHSFz2KR\n\
VGvSnWgKOyhuFR9/3hAyTeaSGFwRplENCQIDAQAB\n\
-----END RSA PUBLIC KEY-----\n\
");
	// _OXAE-KEY
	public_keys[2] = strdup("-----BEGIN RSA PUBLIC KEY-----\n\
MIICCgKCAgEA5Nq/HNNreRc5L/wj3tP4c0M/QM/6dmHxlUP5CoYu5XP+28gC4X0b\n\
bN9jSznJ9elYR7YSO+286mkYAvQd2yBVfnjr0/zlOp91X/95W2f4AEbF7sniCv32\n\
P8o69QF9vDSP93ACZ2/CS/I0F8w7IYn1o9WQn77G4GmyJMXSP50OXHjH008gIpXw\n\
bQkOdLj8QemuMf9etZNkLR87XFIrR1jdnBJ1MnH3wkKLvPXEGM35PimMrscU5Tdj\n\
Y8ZOJsDohXOIY/32VPpDjp+3biYgj3/3aRh0Sf/rmIWZzNHpn9ux2PoLniAPeMh/\n\
X6edpOaAG2huUSdayt7Do7cTtLql9whX/hUN2qxxIm3k56lOkCxSo6zyC3S3bOZJ\n\
Yma4wGjK1vmfG8yOQ+XqYUddAywNIG9Ntx/l/ggAlOwu/KRFw7cANcqjCd3qPWlu\n\
oYV4QYV0KoMznE4QItvFgYcwOx28xiYmS2r9pQQbIwlKS/ghn9Q4tUm0QRKcD8o/\n\
mPcQtgBDA7SgLM/ZjSOqE51Ik46F8aEEKHOeT31Xe7i7tbUJvbnc/FYU+o0+eGEC\n\
mTp+dauS/6Iy0plubIIljUiN8qsPdRSywmvzQvPNAhXYaRDVTVb6Lp9Gw0whMpN6\n\
1hpXyf/hfsSFYffxeVFcM6JXUSypO8MH0mdwqKlOHNBhPBSfAZtdp4MCAwEAAQ==\n\
-----END RSA PUBLIC KEY-----\n\
");
	
	//setup public key memory
	rsa_public = calloc(NUM_PUBLIC_KEYS, sizeof(RSA*));

	if (!public_keys_installed)
	{	
		if (!univention_license_key_public_key_load())
		{
			univention_debug(UV_DEBUG_SSL, UV_DEBUG_ERROR, "Error can't load PublicKey!\n");
			return 0;
		}
	}
	return 1;
}

/******************************************************************************/
/*!
	@brief	cleanup all public and possible private keys
*/
void univention_license_key_free(void)
{
	if (rsa_public != NULL)
	{
		int i;
		for(i=0; i < NUM_PUBLIC_KEYS; i++)
		{
			if (rsa_public[i] != NULL)
			{
				RSA_free(rsa_public[i]);
				rsa_public[i] = NULL;
			}
		}
		free(rsa_public);
		rsa_public = NULL;
	}
	
	if(public_keys != NULL)
	{
		int i;
		for(i=0; i < NUM_PUBLIC_KEYS; i++)
		{
			if (public_keys[i] != NULL)
			{			
				free(public_keys[i]);
				public_keys[i] = NULL;
			}
		}
		free(public_keys);
		public_keys = NULL;
	}

	if (rsa_private != NULL)
	{
		RSA_free(rsa_private);
		rsa_private = NULL;
		EVP_cleanup(); //cleans the encryption chiper of the private key
	}
	
}

/******************************************************************************/
/*!
	@brief	checks if a privateKey is installed
	@retval	1 if a valid privateKey is installed
	@retval	0 on error
*/
int univention_license_key_private_key_installed(void)
{
	if (rsa_private != NULL)
	{	
		if (RSA_check_key(rsa_private))
		{
			return 1;
		}
		univention_debug(UV_DEBUG_SSL, UV_DEBUG_ERROR, "PrivateKey not valid!");
	}
	univention_debug(UV_DEBUG_SSL, UV_DEBUG_ERROR, "PrivateKey not installed!");
	return 0;
}

/******************************************************************************/
/*!
	@brief	checks if the public_keys are installed
	@retval	1 if publicKeys are installed
	@retval	0 on error
*/
int univention_license_key_public_key_installed(void)
{
	if (public_keys_installed)
	{
		return 1;
	}
	else
		univention_debug(UV_DEBUG_SSL, UV_DEBUG_ERROR, "PublicKey not installed!");
	
	return 0;
}

/******************************************************************************/
/*!
	@brief load the defined number(NUM_PUBLIC_KEYS) of publicKeys
	@retval	1 if all publicKey could be installed
	@retval	0 on error
*/
int	univention_license_key_public_key_load(void)
{
	int i;
	public_keys_installed = true;
	for(i=0; ((i < NUM_PUBLIC_KEYS) && public_keys_installed); i++)
	{
		BIO *memReadBIO = NULL;
		if (rsa_public[i] != NULL)
		{
			RSA_free(rsa_public[i]);
		}

		memReadBIO = BIO_new_mem_buf(public_keys[i], -1);
		if (memReadBIO != NULL)
		{
			BIO_set_close(memReadBIO, BIO_NOCLOSE);// So BIO_free() leaves BUF_MEM alone
			PEM_read_bio_RSAPublicKey(memReadBIO, &rsa_public[i], 0, NULL);
	
			BIO_free(memReadBIO);
	
			if (rsa_public[i] == NULL)
			{
				public_keys_installed = false;
				univention_debug(UV_DEBUG_SSL, UV_DEBUG_ERROR, "Can't read PublicKey Nr. %i from memory.",i);
			}
		}
		else
		{
			public_keys_installed = false;
			univention_debug(UV_DEBUG_SSL, UV_DEBUG_ERROR, "Can't create a 'read from memory' BIO.");
		}
	}	
	return public_keys_installed ? 1 : 0;
}

/******************************************************************************/
/*!
	@brief	try load a private key from file
	@param	filename	the file that should be loaded
	@param	passwd		the password to decode the privatekey
		if NULL the pem password question is used automatic
	@retval	1 if the privateKey could be installed
	@retval	0 on error
*/
int univention_license_key_private_key_load_file(const char* filename, const char* passwd)
{
	if (univention_license_init())
	{
		if (rsa_private == NULL)
		{
			FILE* fp = fopen(filename,"r");
			if (fp != NULL)
			{
				/*setup chiper for private key loading*/
				EVP_add_cipher(EVP_des_ede3_cbc());
			
				/*read from file*/
				PEM_read_RSAPrivateKey(fp, &rsa_private, NULL, (char *)passwd);
				
				fclose(fp);
		
				if (rsa_private != NULL)
				{
					if (RSA_check_key(rsa_private) == 1)
					{
						return 1;
					}
					else
					{
						univention_debug(UV_DEBUG_SSL, 0, "Can't valide PrivateKey.");
						RSA_free(rsa_private);
						rsa_private = NULL;
					}
				}
				else
					univention_debug(UV_DEBUG_SSL, 0, "Can't read PrivateKey from file.");
			}
			else
				univention_debug(UV_DEBUG_LICENSE, 0, "Can't open file '%s'.",filename);
		}
		else
			univention_debug(UV_DEBUG_SSL, UV_DEBUG_ERROR, "PublicKey already installed!");	
	}
	return 0;
}

/******************************************************************************/
/*!
	@brief verify data with signature
	verification with all publicKeys is tried.

	@param	data		the data to verify
	@param	signature	the base64 encoded signature for this data
	@retval	1 if successful verified the data
	@retval	0 on error
*/
int univention_license_verify (const char* data, const char* signature)
{
	int ret = 0;
	if (univention_license_key_public_key_installed())
	{
		if (signature != NULL && data != NULL)
		{
			unsigned char hash[SHA_DIGEST_LENGTH];
			int signaturelen = 0;
			unsigned char* rawsignature = NULL;
			int i=0;
			
			//hash
			SHA1((const unsigned char *)data, strlen(data), hash);

			//convert base64signature to rawsignature
			signaturelen = univention_license_base64_to_raw(signature, &rawsignature);
			
			//verify
			while (i < NUM_PUBLIC_KEYS && !ret)
			{
				ret = RSA_verify(NID_sha1, hash, SHA_DIGEST_LENGTH, rawsignature, signaturelen, rsa_public[i]);
				i++;
			}			
			free(rawsignature);
		}
		else
			univention_debug(UV_DEBUG_LICENSE, UV_DEBUG_ERROR, "Can't veriy Data(%s) with Signature(%s).",data,signature);
	}
	return ret;
}

/******************************************************************************/
/*!
	@brief	sign data with the current installed privateKey 
	@param	data the data that should be signed
	@retval	char the base64 encoded signature
	@retval	NULL on error
*/
char* univention_license_sign(const char* data)
{
	char* ret = NULL;
	if (univention_license_init())
	{
		if (univention_license_key_private_key_installed())
		{
			unsigned char hash[SHA_DIGEST_LENGTH];
			unsigned char* temp = NULL;
			unsigned int templen = 0;
			
			temp = malloc(RSA_size(rsa_private));
			if (temp != NULL)
			{
				//hash
				SHA1((const unsigned char *)data, strlen(data), hash);

				//sign
				if (RSA_sign(NID_sha1, hash, SHA_DIGEST_LENGTH, temp, &templen, rsa_private))
				{
					//convert to base64
					ret = univention_license_raw_to_base64(temp, templen);
				}
				else
					univention_debug(UV_DEBUG_SSL, UV_DEBUG_ERROR, "Signing failed!");		

				free(temp);
			}
			else
				univention_debug(UV_DEBUG_SSL, UV_DEBUG_ERROR, "Can't get memory.");
		}
		else
			univention_debug(UV_DEBUG_SSL, UV_DEBUG_ERROR, "No PrivateKey installed!");
	}
	return ret;
}
/*eof*/
