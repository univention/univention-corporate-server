#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <getopt.h>

#include <openssl/rsa.h>
#include <openssl/err.h>
#include <openssl/pem.h>
#include <openssl/rand.h>

/*!
	@file genkey.c
	@brief RSA Key generation tool for the lib license.

	generate a new pair of keys and store this in the given files.
	usage: generateKey publicKeyFile privateKeyFile [keylenght=1024]
*/

/******************************************************************************/
/*!
	@todo initialize the rand pool
*/
int main(int argc, char** argv)
{
	FILE* f = NULL;
	int ret;
	
	char* pubkeyFileName = NULL;
	char* prikeyFileName = NULL;
	char* password = NULL;
	int bits=1024;
	int help_flag = 0;
	RSA* rsa = RSA_new();

	
	//read args
	int c;
	while (1) {
		int option_index = 0;
		static struct option long_options[] = {
			{"help",		no_argument,		0, 'h'},
			{"private" ,	required_argument,	0, 'r'},
			{"public",		required_argument,	0, 'u'},
			{"password",	required_argument,	0, 'p'},
			{"keylenght",	required_argument,	0, 'k'},
			{0, 0, 0, 0}
		};

		c = getopt_long (argc, argv, "hr:u:p:k:", long_options, &option_index);
		if (c == -1)
			break;
		switch(c)
		{
			case 'h':
				help_flag = 1;
			break;
			
			case 'r':
				if (optarg)
					prikeyFileName = optarg;
			break;
			
			case 'u':
				if (optarg)
					pubkeyFileName = optarg;
			break;
			
			case 'k':
				if (optarg)
					bits = atoi(optarg);
			break;
				
			case 'p':
				if (optarg)
					password = optarg;
				break;
			
			default:
				printf("Unknown option '%c'.\n", c);
		}
	}
	
	if (help_flag)
	{
		printf ("Usage:%s PARAMETER [OPTIONS]\n\
	PARAMETER\n\
	-u, --public    the filename to store the public key\n\
	-r, --private   the filename to store the private key\n\
	\n\
	OPTIONS\n\
	-k, --keylenght the bit length of the key\n\
	-p, --password  the password to encrypt the private key\n\
	-h, --help      displays this page\n",argv[0]);
		return -1;
	}
	else
	{
		if(pubkeyFileName != NULL)
		{
			if (prikeyFileName != NULL)
			{
				//init randpool
				RAND_load_file("/dev/urand",128);
				
				//generate RSA key
				printf("Generate RASKey with %i bits length...\n",bits);
				rsa = RSA_generate_key(bits, 65537, NULL, NULL);
				if (rsa == NULL)
				{
					fprintf(stderr, "Keygeneration failed!");
					return -2;
				}
			
				//save public key to file
				printf("Save publickey to:%s.\n",pubkeyFileName);
				f = fopen(pubkeyFileName,"w+");
				if (f == NULL)
				{
					fprintf(stderr, "Can't open or create file!");
					return -3;
				}
				ret = PEM_write_RSAPublicKey(f, rsa);
				
				if (ret != 1)
				{
					fprintf(stderr, "PEM_write_RSAPublicKey failed!\n");
					fclose(f);
					return -4;
				}
				fclose(f);
				
				//save private key to file
				printf("Save privatekey to:%s.\n",prikeyFileName);
				f = fopen(prikeyFileName,"w+");
				if (f == NULL)
				{
					fprintf(stderr, "Can't open or create file!");
					return -3;
				}
				
				if (password != NULL)
					ret = PEM_write_RSAPrivateKey(f, rsa, EVP_des_ede3_cbc(),(unsigned char *)password,strlen(password),NULL,NULL);//use given password
				else
					ret = PEM_write_RSAPrivateKey(f, rsa, EVP_des_ede3_cbc(),NULL,0,NULL,NULL);//use default passwd callback
				
				if (ret != 1)
				{
					fprintf(stderr, "PEM_write_RSAPublicKey failed!");
					fclose(f);
					return -4;
				}
				fclose(f);
				printf("Done.\n");
				return 0;
			}
			else
				fprintf(stderr, "ERROR: private key filename is required.\n");
		}
		else
			fprintf(stderr, "ERROR: public key filename is required.\n");
	}
	return -1;
}
