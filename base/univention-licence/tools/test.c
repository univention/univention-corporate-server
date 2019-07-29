#include <stdio.h>
#include <univention/license.h>

/*! @file test.c
	@brief a tool to test the liblicense client functions.
	
	this tool try to get a license of the give licensetype, and displays
	the received license data.
	
	usage: univentionLicenseTest licensetype
*/

int main(int argv, char** argc)
{
	if (argv != 2)
	{
		printf("usage: %s licensetype\n",argc[0]);
	}
	else
	{
		if (!univention_license_select(argc[1]))
		{
			lObj* license = univention_license_get_global_license();
			int i;
			for (i = 0; i < license->size; i++)
			{
				printf("%s :%s\n",(license->key[i]), (license->val[i]));
			}
		}
		else
		{
			printf("ERROR:Don't got a license of the requested type:%s.\n",argc[1]);
		}
	}
	
	//cleanup
	univention_license_free();
	return 0;
}


/*
void print_val(char* attr)
{
	lStrings* string = univention_license_get_value(attr);
	if (string != NULL)
	{
		int i = 0;
		printf("%s:\n",attr);
		for (i=0; i < string->num; i++)
		{
			printf("%s\n",string->line[i]);
		}
		univention_licenseStrings_free(string);
		string = NULL;
	}
}
	

int main(void)
{
	printf("2ndkey:\n");
	univention_license_select("2ndkey");
		print_val("univentionLicenseEndDate");
		print_val("univentionLicenseModule");
	univention_license_select("multimod");
		print_val("univentionLicenseEndDate");
		print_val("univentionLicenseModule");
	printf("2ndpath:\n");
	univention_license_select("2ndpath");
		print_val("univentionLicenseEndDate");
		print_val("univentionLicenseModule");
	//cleanup
	univention_license_free();
	return 0;
}
*/
