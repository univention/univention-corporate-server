#include <getopt.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <ldap.h>

#include <univention/debug.h>
#include <univention/ldap.h>
#include <univention/policy.h>

void usage(void)
{
	fprintf(stderr, "Usage: univention_policy_result [-h -D -w -s] dn\n");
	fprintf(stderr, "\t-h\thost\n");
	fprintf(stderr, "\t-D\tbinddn\n");
	fprintf(stderr, "\t-w\tbindpw\n");
	
	fprintf(stderr, "\t-s\tShell output\n");
	fprintf(stderr, "\t-b\tBaseconfig output\n");
	exit(1);
}

#define OUTPUT_VERBOSE 0
#define OUTPUT_SHELL 1
#define OUTPUT_BASECONFIG 2

int main(int argc, char* argv[])
{
	LDAP* ld;
	int rc;
	char *dn;
	univention_ldap_parameters_t* ldap_parameters;
	univention_policy_handle_t* handle;
	char opt_debug = 0;
    char output = OUTPUT_VERBOSE;
	LDAPMessage	*res;
	struct  timeval	timeout;

	if ((ldap_parameters=univention_ldap_new()) == NULL)
		return 1;
	
	for (;;) {
		int c;
		c=getopt(argc, argv, "h:p:D:w:Wdsb");
		if (c == -1)
			break;
		switch (c) {
		case 'h':	ldap_parameters->host=strdup(optarg);
				break;
		case 'D':	ldap_parameters->binddn=strdup(optarg);
				break;
		case 'w':	ldap_parameters->bindpw=strdup(optarg);
				break;
		case 'd':	opt_debug=1;
				break;
		case 's':	output=OUTPUT_SHELL;
				break;
		case 'b':	output=OUTPUT_BASECONFIG;
				break;
		default:	usage();
				break;
		}
	}

	if (optind+1 != argc)
		usage();

	if (opt_debug) {
		univention_debug_init("stderr", UV_DEBUG_FLUSH, UV_DEBUG_FUNCTION);
		univention_debug_set_level(UV_DEBUG_POLICY, UV_DEBUG_ALL);
		univention_debug_set_level(UV_DEBUG_LDAP, UV_DEBUG_ALL);
	} else {
		univention_debug_init("/dev/null", 0, 0);
	}
	
	dn=argv[argc-1];

	if (univention_ldap_open(ldap_parameters) != 0) {
        	if (output == OUTPUT_VERBOSE) {
			printf("Return 1 %s\n\n", dn);
		}
		return 1;
	}

	timeout.tv_sec=10;
	timeout.tv_usec=0;

	if ( (rc=ldap_search_st( ldap_parameters->ld, dn, LDAP_SCOPE_BASE, "(objectClass=*)",  NULL, 0, &timeout, &res )) != LDAP_SUCCESS) {
			printf("LDAP Error: %s\n", ldap_err2string(rc));
			exit(1);
	}

	if (output == OUTPUT_VERBOSE) {
		printf("DN: %s\n\n", dn);
	}

	if (output == OUTPUT_VERBOSE) {
		printf("POLICY %s\n\n", dn);
	}
	if ((handle=univention_policy_open(ldap_parameters->ld, ldap_parameters->base, dn)) != NULL) {
		struct univention_policy_list_s* policy;
		struct univention_policy_attribute_list_s* attribute;
		univention_policy_result_t* result;

		for (policy=handle->policies; policy != NULL; policy=policy->next) {
			if (output == OUTPUT_BASECONFIG && policy != handle->policies)
				printf(" ");
			for (attribute=policy->attributes; attribute != NULL; attribute=attribute->next) {
				int i;
				if (attribute->values == NULL)
					continue;
				if (output == OUTPUT_VERBOSE) {
					printf("Policy: %s\n", attribute->values->policy_dn);
					printf("Attribute: %s\n", attribute->name);
					for (i=0; attribute->values->values[i] != NULL; i++)
						printf("Value: %s\n", attribute->values->values[i]);
					printf("\n");
				} else if (output == OUTPUT_SHELL) {
					for (i=0; attribute->values->values[i] != NULL; i++) {
						for (j=0; j<len(attribute->name); j++) {
							if (attribute->name[j] == ';' || attribute->name[j] == '-') {
								printf("_");
							} else {
								printf("%c", attribute->name[j]);
							}
						}
						printf("=\"%s\"\n", attribute->values->values[i]);
						}
					}
				} else { /* output == OUTPUT_BASECONFIG */
					if (attribute != policy->attributes)
						printf(" ");
					for (i=0; attribute->values->values[i] != NULL; i++) {
						if (i>0)
							printf(" ");
						printf("%s=\"%s\"", attribute->name, attribute->values->values[i]);
					}
				}
			}
		}

		univention_policy_close(handle);
	} else return 1;
	return 0;
}
