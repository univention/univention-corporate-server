/*
 * Univention Updater
 *  Set updater/identify from volume set identifier
 *
 * Copyright 2016-2019 Univention GmbH
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

#include <fcntl.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sysexits.h>
#include <unistd.h>

static const int OPEN_FAILED = -1;
static const off_t LSEEK_FAILED = (off_t) -1;

static const uint8_t *open_disk(const char *path)
{
	const int fileno = open(path, O_RDONLY);
	if (fileno == OPEN_FAILED) {
		perror("Could not open file");
		exit(EX_OSERR);
	}
	const off_t size = lseek(fileno, 0, SEEK_END);
	if (size == LSEEK_FAILED || size < 0) {
		perror("Could not find end of file");
		exit(EX_OSERR);
	}
	const void *disk = mmap(NULL, (size_t)size, PROT_READ, MAP_SHARED, fileno, 0);
	if (disk == MAP_FAILED) {
		perror("Could not MMAP disk!");
		exit(EX_OSERR);
	}
	return disk;
}

static const size_t SECTOR_SIZE = 2048; // 2 KiB
static const size_t VOLUME_DESCRIPTORS_START_SECTOR = 0x10;

static uint8_t int8(const uint8_t *disk, const size_t offset)
{
	return disk[offset];
}

static const char *strD(const uint8_t *disk, const size_t offset, const size_t length)
{
	char *str = malloc(length);
	if (str == NULL) {
		perror("Could not allocate memory for string");
		exit(EX_OSERR);
	}
	size_t i;
	for (i = length; i-- > 0; ) {  // i ← length - 1 … 0
		if (disk[offset + i] == '\0' || disk[offset + i] == ' ') {  // rstrip ' '
			str[i] = '\0';
		} else {  // copy the rest verbatim
			for (i++; i-- > 0; ) {  // i ← i … 0
				str[i] = (char)disk[offset + i];
			}
			break;
		}
	}
	return str;
}

static const uint8_t VOLUME_DESCRIPTOR_TYPE_BOOT_RECORD = 0;
static const uint8_t VOLUME_DESCRIPTOR_TYPE_PRIMARY = 1;
static const uint8_t VOLUME_DESCRIPTOR_TYPE_SUPPLEMENTARY = 2;
static const uint8_t VOLUME_DESCRIPTOR_TYPE_PARTITION = 3;
static const uint8_t VOLUME_DESCRIPTOR_TYPE_SET_TERMINATOR = 255;

static const char *read_volume_descriptor_primary(const uint8_t *disk, const size_t position)
{
	const char *volume_set_identifier = strD(disk, position + 183, 128);
	return volume_set_identifier;
}

static const uint8_t MAX_VOLUME_DESCRIPTORS = 100; // TODO what does the standard say?

static const char *IDENTIFIER_STRING = "CD001";

static const char *read_volume_descriptors(const uint8_t *disk)
{
	for (uint8_t number = 0; number < MAX_VOLUME_DESCRIPTORS; number++) {
		const size_t sector = VOLUME_DESCRIPTORS_START_SECTOR + number;
		const size_t position = sector * SECTOR_SIZE;
		const uint8_t type = int8(disk, position + 0);
		const char *identifier = strD(disk, position + 1, 5);
		if (strncmp(identifier, IDENTIFIER_STRING, strlen(IDENTIFIER_STRING)) != 0) {
			perror("Invalid identifier");
			exit(EX_DATAERR);
		}
		const uint8_t version = int8(disk, position + 6);
		if (version != 0x01) {
			perror("Invalid version");
			exit(EX_DATAERR);
		}
		if (type == VOLUME_DESCRIPTOR_TYPE_BOOT_RECORD) {
			;
		} else if (type == VOLUME_DESCRIPTOR_TYPE_PRIMARY) {
			return read_volume_descriptor_primary(disk, position + 7);
		} else if (type == VOLUME_DESCRIPTOR_TYPE_SUPPLEMENTARY) {
			;
		} else if (type == VOLUME_DESCRIPTOR_TYPE_PARTITION) {
			;
		} else if (type == VOLUME_DESCRIPTOR_TYPE_SET_TERMINATOR) {
			return NULL;
		} else {
			perror("Invalid type");
			exit(EX_DATAERR);
		}
	}
	perror("Too many volume descriptors");
	exit(EX_DATAERR);
}

int main(int argc, char *argv[])
{
	if (argc <= 1) {
		perror("Required argument missing: device");
		return EX_USAGE;
	}
	if (argc > 2) {
		perror("Too many arguments");
		return EX_USAGE;
	}
	const char *device = argv[1];
	const uint8_t *disk = open_disk(device);
	const char *volume_set_identifier = read_volume_descriptors(disk);
	if (volume_set_identifier == NULL) {
		return EX_DATAERR;
	}
	printf("%s", volume_set_identifier);
	return EX_OK;
}
