#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <getopt.h>

#define COMMAND "/usr/lib/nagios/plugins/check_smart.pl"
#define SIZE 4096

static void usage(void) {
	fprintf(stderr, "Usage: check_smart_suidwrapper -i INTERFACE -d DEVICE\n");
}

main(int argc, char ** argv, char ** envp) {

	int i = 0;
	uid_t uid = getuid();
	char device[SIZE];
	char interface[SIZE];

	while ((i = getopt(argc, argv, "::hd:i:")) != -1) {
		switch (i) {
			case 'd':
				strncpy(device, optarg, sizeof(device));
				device[sizeof(device) -1] = '\0';
				break;
			case 'i':
				strncpy(interface, optarg, sizeof(interface));
				device[sizeof(interface) -1] = '\0';
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

	if (strlen(device) == 0 || strlen(interface) == 0) {
		usage();
		exit(1);	
	}

	if(setgid(getegid()))
		perror("setgid");
	if(setuid(geteuid()))
		perror("setuid");
	execle(COMMAND, COMMAND, "-d", device, "-i", interface, (char *)0, (char *)0);
	setuid(uid);

	exit(1);
}

