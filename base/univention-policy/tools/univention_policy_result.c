/*
 * Univention Policy
 *  C source of the univention policy result tool
 *
 * Like what you see? Join us!
 * https://www.univention.com/about-us/careers/vacancies/
 *
 * Copyright 2003-2024 Univention GmbH
 *
 * https://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <https://www.gnu.org/licenses/>.
 */
#include "../lib/internal.h"

#include <errno.h>
#include <fcntl.h>
#include <getopt.h>
#include <ldap.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <univention/config.h>
#include <univention/debug.h>
#include <univention/ldap.h>

static void usage(void) {
	fprintf(stderr, "Usage: univention_policy_result [-h <host>] [-D <binddn>] [-w <bindpw> | -y <pwfile> | -W] [-p port] [-s | -b] dn\n");
	fprintf(stderr, "  -h host    LDAP server\n");
	fprintf(stderr, "  -D binddn  bind DN\n");
	fprintf(stderr, "  -W         prompt for password on the command line\n");
	fprintf(stderr, "  -w bindpw  bind password\n");
	fprintf(stderr, "  -y pwfile  Read password from file\n");
	fprintf(stderr, "  -p port    port number where the ldap server is listening\n");
	fprintf(stderr, "  -s         Shell output\n");
	fprintf(stderr, "  -b         Basic output\n");
	fprintf(stderr, "  -d         Enable debug\n");
}

#define OUTPUT_VERBOSE 0
#define OUTPUT_SHELL 1
#define OUTPUT_BASECONFIG 2

int main(int argc, char *argv[]) {
	int rc = 1;
	bool use_default_ldap_servers = true;
	char *dn;
	univention_ldap_parameters_t *ldap_parameters;
	univention_policy_handle_t *handle;
	char opt_debug = 0;
	char output = OUTPUT_VERBOSE;
	LDAPMessage *res;
	struct timeval timeout;

	if ((ldap_parameters = univention_ldap_new()) == NULL)
		return 1;

	int c;
	while ((c = getopt(argc, argv, ":h:p:D:w:Wdsby:")) != -1) {
		switch (c) {
		case 'h':
			FREE(ldap_parameters->host);
			ldap_parameters->host = strdup(optarg);
			use_default_ldap_servers = false;
			break;
		case 'D':
			FREE(ldap_parameters->binddn);
			ldap_parameters->binddn = strdup(optarg);
			break;
		case 'W':
			FREE(ldap_parameters->bindpw);
			ldap_parameters->bindpw = getpass("Enter LDAP Password: ");
			if (ldap_parameters->bindpw == NULL) {
				perror("getpass: reading password failed");
				goto err2;
			}
			ldap_parameters->bindpw = strdup(ldap_parameters->bindpw);
			break;
		case 'w':
			FREE(ldap_parameters->bindpw);
			ldap_parameters->bindpw = strdup(optarg);
			break;
		case 'd':
			opt_debug = 1;
			break;
		case 'p':
			if (sscanf(optarg, "%d", &ldap_parameters->port) != 1) {
				fprintf(stderr, "the given port number '%s' is unusable", optarg);
				goto err2;
			}
			break;
		case 's':
			output = OUTPUT_SHELL;
			break;
		case 'b':
			output = OUTPUT_BASECONFIG;
			break;
		case 'y':
			FREE(ldap_parameters->bindpw);
			ldap_parameters->bindpw = univention_ldap_read_secret(optarg);
			if (ldap_parameters->bindpw == NULL) {
				return 1;
			}
			break;
		case ':':
			fprintf(stderr, "missing argument for option %c\n", optopt);
			goto err2;
		default:
			univention_ldap_close(ldap_parameters);
			usage();
			fprintf(stderr, "option %c is undefined\n", optopt);
			goto err1;
		}
	}

	if (optind + 1 != argc) {
		univention_ldap_close(ldap_parameters);
		usage();
		goto err1;
	}

	if (opt_debug) {
		univention_debug_init("stderr", UV_DEBUG_FLUSH, UV_DEBUG_FUNCTION);
		univention_debug_set_level(UV_DEBUG_POLICY, UV_DEBUG_ALL);
		univention_debug_set_level(UV_DEBUG_LDAP, UV_DEBUG_ALL);
	} else {
		univention_debug_init("/dev/null", 0, 0);
	}

	dn = argv[argc - 1];

	/* if no host/uri is set in ldap_parameters univention_ldap_open uses
	ldap/server/name. We try ldap/server/addition too, if no host/uri
	is set */
	if ((rc = univention_ldap_open(ldap_parameters)) != 0) {
		bool gotConnection = false;
		if (use_default_ldap_servers) {
			char *addition = univention_config_get_string("ldap/server/addition");
			/* try ldap/server/addition */
			if (addition) {
				char *saveptr, *splitPointer = strtok_r(addition, " ", &saveptr);
				while (splitPointer != NULL) {
					ldap_parameters->host = strdup(splitPointer);
					if ((rc = univention_ldap_open(ldap_parameters)) == 0) {
						gotConnection = true;
						break;
					}
					FREE(ldap_parameters->host);
					splitPointer = strtok_r(NULL, " ", &saveptr);
				}
			}
			free(addition);
		}
		if (!gotConnection) {
			fprintf(stderr, "could not open policy for %s\n\n", dn);
			goto err2;
		}
	}

	timeout.tv_sec = 10;
	timeout.tv_usec = 0;

	if ((rc = ldap_search_ext_s(ldap_parameters->ld, dn, LDAP_SCOPE_BASE, "(objectClass=*)", NULL, 0, NULL, NULL, &timeout, 0, &res)) != LDAP_SUCCESS) {
		fprintf(stderr, "LDAP Error: %s\n", ldap_err2string(rc));
		ldap_msgfree(res);
		goto err2;
	}
	ldap_msgfree(res);

	if (output == OUTPUT_VERBOSE) {
		printf("DN: %s\n\n", dn);
	}

	if (output == OUTPUT_VERBOSE) {
		printf("POLICY %s\n\n", dn);
	}
	if ((handle = univention_policy_open(ldap_parameters->ld, ldap_parameters->base, dn)) != NULL) {
		struct univention_policy_list_s *policy;
		struct univention_policy_attribute_list_s *attribute;

		for (policy = handle->policies; policy != NULL; policy = policy->next) {
			if (output == OUTPUT_BASECONFIG && policy != handle->policies)
				printf(" ");
			for (attribute = policy->attributes; attribute != NULL; attribute = attribute->next) {
				int i, j;
				if (attribute->values == NULL)
					continue;
				if (output == OUTPUT_VERBOSE) {
					printf("Policy: %s\n", attribute->values->policy_dn);
					printf("Attribute: %s\n", attribute->name);
					for (i = 0; attribute->values->values[i] != NULL; i++)
						printf("Value: %s\n", attribute->values->values[i]);
					printf("\n");
				} else if (output == OUTPUT_SHELL) {
					for (i = 0; attribute->values->values[i] != NULL; i++) {
						for (j = 0; j < strlen(attribute->name); j++) {
							if (attribute->name[j] == ';' || attribute->name[j] == '-') {
								printf("_");
							} else {
								printf("%c", attribute->name[j]);
							}
						}
						char *c;
						printf("=\"");
						for (c = attribute->values->values[i]; *c; c++) {
							switch (*c) {
							case '"':
							case '$':
							case '\\':
							case '`':
								putchar('\\');
							default:
								putchar(*c);
							}
						}
						printf("\"\n");
					}
				} else { /* output == OUTPUT_BASECONFIG */
					if (attribute != policy->attributes)
						printf(" ");
					for (i = 0; attribute->values->values[i] != NULL; i++) {
						if (i > 0)
							printf(" ");
						printf("%s=\"%s\"", attribute->name, attribute->values->values[i]);
					}
				}
			}
		}
		univention_policy_close(handle);
		rc = 0;
	} else {
		rc = 1;
		fprintf(stderr, "could not open policy\n");
	}
err2:
	univention_ldap_close(ldap_parameters);
err1:
	univention_debug_exit();
	return rc;
}
