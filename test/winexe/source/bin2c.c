/*
  Copyright (C) Andrzej Hajda 2009-2013
  Contact: andrzej.hajda@wp.pl
  License: GNU General Public License version 3
*/

#include <stdio.h>
#include <string.h>
#include <stdlib.h>

int main(int argc, char **argv)
{
	char buf[256], s[100];
	int c;
	FILE *fp;
	if (argc != 3) {
		fprintf(stderr, "Usage: %s varname file\n", *argv);
		return 1;
	}
	if (!(fp = fopen(argv[2], "rb"))) {
		fputs("Cannot open ", stderr);
		perror(argv[2]);
		return 1;
	}
	fseek(fp, 0, SEEK_END);
	long len = ftell(fp);
	fseek(fp, 0, SEEK_SET);
	printf("unsigned int %s_len = %lu;\nunsigned char %s[] = {\n", argv[1], len, argv[1]);
	strcpy(buf, "  ");
	while ((c = getc(fp)) != EOF) {
		sprintf(s, "%u,", (unsigned char) c);
		if (strlen(s) + strlen(buf) >= 80)
			puts(buf), strcpy(buf, "  ");
		strcat(buf, s);
	}
	if (*buf)
		strcat(buf, "\n");
	printf("%s};\n", buf);
	fprintf(stderr, "%s_len = %lu\n", argv[1], len);
	return 0;
}
