/*
 * Univention Directory Notifier
 *
 * SPDX-FileCopyrightText: 2004-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */
#include <stdio.h>
#include "index.h"
#include "notify.h"

int main(int argc, char *argv[])
{
	char *filename = argc > 1 ? argv[1] : FILE_NAME_TF_IDX;
	printf("FILE: %s\n", filename);

	FILE *fp = fopen(filename, "r");
	if (!fp) {
		perror("Failed fopen()");
		return 1;
	}
	struct index_header header;
	int index;

	if (fread(&header, sizeof(header), 1, fp) != 1)
		perror("Failed fread()");
	printf("MAGIC: 0x%lx %s\n", header.magic, header.magic == MAGIC ? "VALID" : "INVALID");

	for (index = 0; !feof(fp); index++) {
		struct index_entry entry;
		if (fread(&entry, sizeof(entry), 1, fp) != 1) {
			if (!feof(fp))
				perror("Failed fread()");
			break;
		}

		printf("%8d[%c]: %zd\n", index, entry.valid == 1 ? 'x' : ' ', entry.offset);
	}

	fclose(fp);

	return 0;
}
