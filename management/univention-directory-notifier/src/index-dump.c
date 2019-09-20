/*
 * Univention Directory Notifier
 *
 * Copyright 2004-2019 Univention GmbH
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
