#include <unistd.h>
#include <stdio.h>
#include <stdlib.h>

static char COMMAND[] = "/usr/bin/univention-radius-ntlm-auth";

int main(int argc, char *argv[])
{
	int i;
	char* args[10];
	char* envp[1];
	if (setgid(getegid())) {
		perror("setgid");
	}
	if (setuid(geteuid())) {
		perror("setuid");
	}
	args[0] = COMMAND;
	for (i = 0; i < 10; i++) {
		args[i] = NULL;
	}
	if (argc > 9) {
		argc = 9;
	}
	for (i = 0; i < argc; i++) {
		args[i] = argv[i];
	}
	envp[0] = NULL;
	execve(COMMAND, args, envp);
	exit(EXIT_FAILURE);
}
