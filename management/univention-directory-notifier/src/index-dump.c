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
#include "index.h"

int main(int argc, char *argv[])
{
	FILE *fp = fopen(argv[1], "r");
	unsigned long magic;
	ssize_t offset, index;
	char valid;

	fread(&magic, sizeof(unsigned long), 1, fp);
	printf("MAGIC: 0x%lx\n", magic);

	while (!feof(fp)) {
		index =(ftell(fp)-sizeof(unsigned long))/(sizeof(char)+sizeof(size_t));
		
		if (fread(&valid, sizeof(char), 1, fp) != 1)
			break;
		if (fread(&offset, sizeof(size_t), 1, fp) != 1)
			break;

		printf("%8d[%c]: %d\n", index,
				valid == 1 ? 'x' : ' ', offset);
	}

	return 0;
}
