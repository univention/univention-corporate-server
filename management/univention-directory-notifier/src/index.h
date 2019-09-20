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
#ifndef __NOTIFIER_INDEX_H__
#define __NOTIFIER_INDEX_H__

#include <stdio.h>

static const unsigned long MAGIC = 0x3395e0d4;

struct index_header {
    unsigned long magic;
} __attribute__((__packed__));
struct index_entry {
    char valid;
    size_t offset;  // BUG: should have been off_t as size_t is 32 bit even with _FILE_OFFSET_BITS=64 on i386
} __attribute__((__packed__));

FILE* index_open(const char *filename);
size_t index_get(FILE *fp, unsigned long id);
void index_set(FILE *fp, unsigned long id, size_t offset);

#endif /* __NOTIFIER_INDEX_H__ */
