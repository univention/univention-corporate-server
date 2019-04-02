/*
 * Univention Directory Notifier
 *
 * Copyright 2004-2019 Univention GmbH
 *
 * http://www.univention.de/
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
 * <http://www.gnu.org/licenses/>.
 */

#include <stdio.h>
#include <unistd.h>
#include "index.h"

FILE* index_open(const char *filename)
{
	FILE* fp;
	struct index_header header;

	if ((fp = fopen(filename, "r+")) != NULL) {
		if (fread(&header, sizeof(header), 1, fp) == 1 && header.magic == MAGIC)
			return fp;
	}
	if ((fp = fopen(filename, "w+")) != NULL) {
		header.magic = MAGIC;
		if (fwrite(&header, sizeof(header), 1, fp) == 1)
			return fp;
	}
	return NULL;
}

void index_invalidate(FILE *fp)
{
	struct index_header header = { .magic = MAGIC };

	fseek(fp, 0, SEEK_SET);
	ftruncate(fileno(fp), 0);
	fseek(fp, 0, SEEK_SET);

	fwrite(&header, sizeof(header), 1, fp);
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
	index_seek(fp, id);
	if (fwrite(&entry, sizeof(entry), 1, fp) != 1)
		return;
}
