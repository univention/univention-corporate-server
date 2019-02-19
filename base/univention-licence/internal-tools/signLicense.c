#include <stdlib.h>
#include <stdio.h>
#include <univention/license.h>
#include <getopt.h>

/*! @file signLicense.c
	@brief A admin tool to generate a signature for a already existing licenseObject.
	
	usage: univentionLicenseCreateSignature (-d|--dn) LicenseDN (-k|--key) PrivateKeyFile [-p|--password password] [-h|--help]
*/

int main(int argc, char** argv)
{
	int help_flag = 0;
	char* objectDN = NULL;
	char* privateKeyFile = NULL;
	char* password = NULL;
	
	//read args
	int c;
	while (1) {
		int option_index = 0;
		static struct option long_options[] = {
			{"help",		no_argument,		0, 'h'},
			{"dn" ,			required_argument,	0, 'd'},
			{"key",			required_argument,	0, 'k'},
			{"password",	required_argument,	0, 'p'},
			{0, 0, 0, 0}
		};

		c = getopt_long (argc, argv, "hd:k:p:", long_options, &option_index);
		if (c == -1)
			break;
		switch(c)
		{
			case 'h':
				help_flag = 1;
			break;
			
			case 'd':
				if (optarg)
					objectDN = optarg;
			break;
			
			case 'k':
				if (optarg)
					privateKeyFile = optarg;
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
	printf("usage:	%s PARAMETER [OPTIONS]\n\
	PARAMETER\n\
	-d, --dn       the DN of the license object\n\
	-k, --key      the private key file for creating the signature\n\
	\n\
	OPTIONS\n\
	-p, --password the password to open the private key file\n\
	-h, --help     displays this page\n",argv[0]);
	return -1;
	}
	else
	{
		if (objectDN != NULL)
		{
			if (privateKeyFile != NULL)
			{
				if (univention_license_key_private_key_load_file(privateKeyFile, password))
				{
					char* signature = NULL;
					signature = univention_license_sign_license(objectDN);
					
					if (signature != NULL)
					{
						//ldap modify format
						printf("dn: %s\n",objectDN);
						printf("univentionLicenseSignature: %s\n",signature);
						free(signature);
						univention_license_free();
						return 0;
					}
					else
						printf("Sign failed!");
				}
				else
					printf("Error: Can't install the privateKey!\n");
				
			}
			else
				printf("Error: No privateKeyFile given!\n");
		}
		else
			printf("Error: No LicenseDN given!\n");
	}
	univention_license_free();
	return -1;
}
