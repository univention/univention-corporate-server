/*
 * Univention Directory Notifier
 *
 * Copyright (C) 2004-2009 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Binary versions of this file provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
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
