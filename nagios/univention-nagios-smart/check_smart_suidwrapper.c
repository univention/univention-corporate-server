#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <getopt.h>

#define COMMAND "/usr/lib/nagios/plugins/check_smart.pl"

static void usage(void) {
	fprintf(stderr, "Usage: check_smart_suidwrapper -i INTERFACE -d DEVICE\n");
}

main(int argc, char ** argv, char ** envp) {

	int i = 0;
	char *device = NULL;
	char *interface = NULL;

	while ((i = getopt(argc, argv, "::hd:i:")) != -1) {
		switch (i) {
			case 'd':
				device = optarg;
				break;
			case 'i':
				interface = optarg;
				break;
			case 'h':
				usage();
				exit(0);
			default:
				fprintf(stderr, "option %c is undefined\n", optopt);
				usage();
				exit(1);	
		}
	}

	if (device == NULL || interface == NULL) {
		usage();
		exit(1);	
	}

	if(setgid(getegid()))
		perror("setgid");
	if(setuid(geteuid()))
		perror("setuid");

	execle(COMMAND, COMMAND, "-d", device, "-i", interface, (char *)0, (char *)0);

	exit(1);
}

