/*
 * Univention Directory Notifier
 *
 * SPDX-FileCopyrightText: 2004-2026 Univention GmbH
 * SPDX-License-Identifier: AGPL-3.0-only
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include "index.h"

FILE* index_open(const char *filename)
{
	FILE* fp;
	struct index_header header;

	if ((fp = fopen(filename, "r+")) != NULL) {
		if (fread(&header, sizeof(header), 1, fp) == 1 && header.magic == MAGIC)
			return fp;
		fclose(fp);
	}
	if ((fp = fopen(filename, "w+")) != NULL) {
		header.magic = MAGIC;
		if (fwrite(&header, sizeof(header), 1, fp) == 1)
			return fp;
		fclose(fp);
	}
	perror("Failed fopen(idx)");
	abort();
}

static unsigned long index_seek(FILE *fp, unsigned long id) {
	unsigned long offset = sizeof(struct index_header) + id * sizeof(struct index_entry);
	fseek(fp, offset, SEEK_SET);
	return offset;
}

size_t index_get(FILE *fp, unsigned long id)
{
	struct index_entry entry;

	index_seek(fp, id);
	if (fread(&entry, sizeof(entry), 1, fp) != 1)
		return -1;
	if (entry.valid != 1)
		return -1;
	return entry.offset;
}

void index_set(FILE *fp, unsigned long id, size_t offset)
{
	struct index_entry entry = {
		.valid = 1, .offset = offset,
	};
	unsigned long index_offset = index_seek(fp, id);
	if (fallocate(fileno(fp), FALLOC_FL_KEEP_SIZE, index_offset, sizeof(entry)) == -1 && (errno != ENOSYS) && (errno != EOPNOTSUPP)) {
		perror("Failed fallocate(idx)");
		abort();
	}
	if (fwrite(&entry, sizeof(entry), 1, fp) != 1) {
		perror("Failed fwrite(idx)");
		abort();
	}
}
