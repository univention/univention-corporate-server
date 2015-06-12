/*
 * Univention Directory Notifier
 *
 * Copyright 2004-2015 Univention GmbH
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

#define MAGIC 0x3395e0d4

FILE* index_open(const char *filename)
{
	FILE* fp;
	unsigned long magic;

	if ((fp = fopen(filename, "r+")) != NULL) {
		if (fread(&magic, sizeof(unsigned long), 1, fp) == 1 && magic == MAGIC)
			return fp;
	}
	if ((fp = fopen(filename, "w+")) != NULL) {
		magic = MAGIC;
		if (fwrite(&magic, sizeof(unsigned long), 1, fp) == 1)
			return fp;
	}
	return NULL;
}

void index_invalidate(FILE *fp)
{
	unsigned long magic = MAGIC;
	
	fseek(fp, 0, SEEK_SET);
	ftruncate(fileno(fp), 0);
	fseek(fp, 0, SEEK_SET);

	fwrite(&magic, sizeof(unsigned long), 1, fp);
}

ssize_t index_get(FILE *fp, unsigned long id)
{
	char valid;
	size_t result;
	
	fseek(fp, sizeof(unsigned long)+id*(sizeof(char)+sizeof(size_t)), SEEK_SET);
	if (fread(&valid, sizeof(char), 1, fp) != 1)
		return -1;
	if (valid != 1)
		return -1;
	if (fread(&result, sizeof(size_t), 1, fp) != 1)
		return -1;

	return result;
}

void index_set(FILE *fp, unsigned long id, size_t offset)
{
	char valid = 1;
	fseek(fp, sizeof(unsigned long)+id*(sizeof(char)+sizeof(size_t)), SEEK_SET);
	if (fwrite(&valid, sizeof(char), 1, fp) != 1)
		return;
	if (fwrite(&offset, sizeof(size_t), 1, fp) != 1)
		return;
}

