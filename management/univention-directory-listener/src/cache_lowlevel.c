/*
 * Univention Directory Listener
 *  cache_lowlevel.c
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

#define _GNU_SOURCE /* for strndup */

#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#include <limits.h>
#include <errno.h>
#include <sys/types.h>

#include <assert.h>
#include <univention/debug.h>

#include "common.h"
#include "cache_lowlevel.h"

enum type {
	TYPE_ATTRIBUTE = 1,
	TYPE_MODULES = 2,
};

struct cache_entry_header {
	u_int16_t type;
	u_int32_t key_size;
	u_int32_t data_size;
};


/*
 * Print buffer as hex-decimal dump.
 * :param level: Debug level.
 * :param data: buffer to dump.
 * :param start: start index.
 * :param size: Count of bytes to dump.
 */
static void hex_dump(int level, const char *data, u_int32_t start, u_int32_t size) {
	int i;
	int pos;
	char hex[80];
	char str[80];
	const int per_line = 10;

	pos = 0;
	memset(hex, 0, 80);
	memset(str, 0, 80);

	for (i = 0, data += start; i < size; i++, data++) {
		snprintf(hex + (pos * 3), 80 - (pos * 3), "%02x ", *data);
		snprintf(str + pos, 80 - pos, "%c", isprint(*data) ? *data : '?');
		pos += 1;
		if ((i + 1) % per_line == 0) {
			univention_debug(UV_DEBUG_LISTENER, level, "%s| %s (%08d)", hex, str, start + i - per_line);
			// fprintf(stderr, "%s| %s (%08d)\n", hex, str, start+i-per_line);
			memset(hex, 0, 80);
			memset(str, 0, 80);
			pos = 0;
		}
	}
	if (pos != 0)
		univention_debug(UV_DEBUG_LISTENER, level, "%s | %s", hex, str);
}

/* assumption: enough memory as been allocated for us */
static void append_buffer(char *data, u_int32_t *pos, void *blob_data, u_int32_t blob_size) {
	if (blob_size > 0) {
		memcpy(data + *pos, blob_data, blob_size);
		LOG(ALL, "position was=%d is=%d", *pos, *pos + blob_size);
		*pos += blob_size;
	}
}

/*
 * Convert in-memory representation of cache attribute to on-disk representation.
 * :param data: Return variable to receive pointer to buffer with allocated on-disk representation.
 * :param size: Return variable to receive buffer size of `data`.
 * :param type: Typ of entry to add.
 * :param key_data: Key name.
 * :param key_size: Size of `key_data` in bytes.
 * :param data_data: Value data.
 * :param data_size: Size of `data_data` in bytes.
 * :return: 0 on success, 1 otherwise.
 *
 * See :c:func:`unparse_entry` for the reverse.
 */
static int write_header(void **data, u_int32_t *size, u_int32_t *pos, enum type type, void *key_data, u_int32_t key_size, void *data_data, u_int32_t data_size) {
	struct cache_entry_header h;
	u_int32_t need_memory;

	LOG(ALL, "write_header key_size=%d data_size=%d", key_size, data_size);

	need_memory = sizeof(struct cache_entry_header) + key_size + data_size;
	if (*size < *pos + need_memory) {
		while (*size < *pos + need_memory)
			*size += BUFSIZ;
		if ((*data = realloc(*data, *size)) == NULL) {
			LOG(ERROR, "realloc() failed");
			return 1;
		}
	}

	h.type = type;
	h.key_size = key_size;
	h.data_size = data_size;

	append_buffer(*data, pos, &h, sizeof(struct cache_entry_header));
	append_buffer(*data, pos, key_data, key_size);
	append_buffer(*data, pos, data_data, data_size);

	return 0;
}

/*
 * Convert in-memory representation of cache entry to on-disk representation.
 * :param data: Return variable to receive pointer to buffer with allocated on-disk representation.
 * :param size: Return variable to receive buffer size of `data`.
 * :param entry: The cache entry to serialize.
 * :return: 0 on success, 1 otherwise.
 *
 * See :c:func:`parse_entry` for the reverse.
 */
int unparse_entry(void **data, u_int32_t *size, CacheEntry *entry) {
	CacheEntryAttribute **attribute;
	char **value;
	char **module;
	int *length;
	int i, rv = -1;
	u_int32_t pos = 0;

	for (attribute = entry->attributes; attribute != NULL && *attribute != NULL; attribute++) {
		for (value = (*attribute)->values, i = 0, length = (*attribute)->length; *value != NULL; value++, i++) {
			rv = write_header(data, size, &pos, TYPE_ATTRIBUTE, (*attribute)->name, strlen((*attribute)->name) + 1, *value, length[i]);
			if (rv)
				goto out;
		}
	}
	for (module = entry->modules; module != NULL && *module != NULL; module++) {
		rv = write_header(data, size, &pos, TYPE_MODULES, *module, strlen(*module) + 1, NULL, 0);
		if (rv)
			goto out;
	}

	/* allocated memory maybe bigger than size, but doesn't matter anyhow... */
	*size = pos;
	rv = 0;

out:
	return rv;
}

/*
 * De-serialize entry from buffer.
 * :param data: Pointer to the buffer containing the on-disk representation.
 * :param size: Buffer size of `data`.
 * :param pos: Pointer to offset into buffer, which is updated for each parsed entry.
 * :param key_data: Return variable to receive parsed key.
 * :param key_size: Return variable to receive size of allocated `key_data`.
 * :param data_data: Return variable to receive parsed value.
 * :param data_size: Return variable to receive size of allocated `data_data`.
 * :returns: 0 or the entry type on success, -1 on errors.
 */
static enum type read_header(void *data, u_int32_t size, u_int32_t *pos, void **key_data, u_int32_t *key_size, void **data_data, u_int32_t *data_size) {
	struct cache_entry_header *h;

	if (*pos == size) {
		LOG(ALL, "end of buffer pos=size=%d", *pos);
		return 0;
	} else if (*pos + sizeof(struct cache_entry_header) > size) {
		LOG(ERROR, "buffer exceeded pos=%d size=%d", *pos, size);
		return -1;
	}

	h = (struct cache_entry_header *)((char *)data + *pos);

	if ((h->type != TYPE_ATTRIBUTE && h->type != TYPE_MODULES) || h->key_size == 0) {
		LOG(ALL, "read_header pos=%d type=%d key_size=%d data_size=%d", *pos, h->type, h->key_size, h->data_size);
		*key_size = 0;
		*key_data = NULL;
		*data_size = 0;
		*data_data = NULL;
		return -1;
	}
	*pos += sizeof(struct cache_entry_header);
	if (*pos + h->key_size + h->data_size > size) {
		LOG(ERROR, "buffer exceeded pos=%d size=%d", *pos, size);
		return -1;
	}

	*key_size = h->key_size;
	*key_data = (void *)((char *)data + *pos);
	*pos += *key_size;

	if (h->data_size > 0) {
		*data_size = h->data_size;
		*data_data = (void *)((char *)data + *pos);
		*pos += *data_size;
	} else {
		*data_size = 0;
		*data_data = NULL;
	}
	LOG(ALL, "read_header pos=%d type=%d key_size=%d data_size=%d key_data=[%s] data_data=[%s]", *pos, h->type, h->key_size, h->data_size, (char *)*key_data, (char *)*data_data);

	return h->type;
}

/*
 * Convert on-disk representation of cache entry to in-memory representation.
 * :param data: Pointer to the buffer containing the on-disk representation.
 * :param size: Buffer size of `data`.
 * :param entry: Return variable to receive parsed cache entry.
 * :returns: 0 on success, 1 otherwise.
 *
 * :See :c:func:`unparse_entry` for the reverse.
 */
int parse_entry(void *data, u_int32_t size, CacheEntry *entry) {
	enum type type;
	void *key_data, *data_data;
	u_int32_t key_size, data_size;
	u_int32_t pos = 0;

	entry->attributes = NULL;
	entry->attribute_count = 0;
	entry->modules = NULL;
	entry->module_count = 0;

	while ((type = read_header(data, size, &pos, &key_data, &key_size, &data_data, &data_size)) > 0) {
		switch (type) {
		case TYPE_ATTRIBUTE: {
			CacheEntryAttribute **attribute, *c_attr;

			LOG(ALL, "attribute is \"%s\"", (char *)key_data);
			/* key name including '\0' */
			assert(key_size >= 1);
			assert('\0' == ((char *)key_data)[key_size - 1]);
			/* value including '\0' */
			assert(data_size >= 1);
			assert('\0' == ((char *)data_data)[data_size - 1]);

			for (attribute = entry->attributes, c_attr = NULL; attribute != NULL && *attribute != NULL; attribute++) {
				LOG(ALL, "current attribute is \"%s\"", (*attribute)->name);
				if (strcmp((*attribute)->name, key_data) == 0) {
					c_attr = *attribute;
					break;
				}
			}
			if (!c_attr) {
				if (!(entry->attributes = realloc(entry->attributes, (entry->attribute_count + 2) * sizeof(CacheEntryAttribute *)))) {
					LOG(ERROR, "realloc() failed");
					abort();  // FIXME
				}
				if (!(c_attr = malloc(sizeof(CacheEntryAttribute)))) {
					LOG(ERROR, "malloc() failed");
					abort();  // FIXME
				}
				if (!(c_attr->name = strndup(key_data, key_size))) {
					LOG(ERROR, "strndup() failed");
					abort();  // FIXME
				}
				c_attr->values = NULL;
				c_attr->length = NULL;
				c_attr->value_count = 0;
				entry->attributes[entry->attribute_count++] = c_attr;
				entry->attributes[entry->attribute_count] = NULL;

				LOG(ALL, "%s is at %p", c_attr->name, c_attr);
			}
			if (!(c_attr->values = realloc(c_attr->values, (c_attr->value_count + 2) * sizeof(char *)))) {
				LOG(ERROR, "realloc() failed");
				abort();  // FIXME
			}
			if (!(c_attr->length = realloc(c_attr->length, (c_attr->value_count + 2) * sizeof(int)))) {
				LOG(ERROR, "realloc() failed");
				abort();  // FIXME
			}
			if (!(c_attr->values[c_attr->value_count] = malloc(data_size))) {
				LOG(ERROR, "malloc() failed");
				abort();  // FIXME
			}
			c_attr->length[c_attr->value_count] = data_size;
			memcpy(c_attr->values[c_attr->value_count], data_data, data_size);
			LOG(ALL, "value is \"%s\"", c_attr->values[c_attr->value_count]);
			c_attr->values[++c_attr->value_count] = NULL;
			break;
		}

		case TYPE_MODULES:
			entry->modules = realloc(entry->modules, (entry->module_count + 2) * sizeof(char *));
			if (!(entry->modules[entry->module_count] = strndup((char *)key_data, key_size))) {
				LOG(ERROR, "strndup() failed");
				abort();  // FIXME
			}
			entry->modules[++entry->module_count] = NULL;
			break;

		default: {
			char filename[PATH_MAX];
			FILE *file;
			u_int32_t len;
			int rv;

			LOG(ERROR, "bad data block at position %d:", pos);
			len = pos < 1000 ? pos : 1000;
			LOG(ERROR, "last %d bytes of previous entry:", len);
			hex_dump(UV_DEBUG_ERROR, data, pos < 1000 ? 0 : pos - 1000, len);
			len = pos + 1000 > size ? size - pos : 1000;
			LOG(ERROR, "first %d bytes of current entry:", len);
			hex_dump(UV_DEBUG_ERROR, data, pos, len);

			rv = snprintf(filename, PATH_MAX, "%s/bad_cache", cache_dir);
			if (rv < 0 || rv >= PATH_MAX)
				abort();
			if ((file = fopen(filename, "w")) == NULL)
				abort_io("open", filename);
			fprintf(file, "Check log file");
			rv = fclose(file);
			if (rv != 0)
				abort_io("close", filename);

			return -1;
		}
		}
	}

	return 0;
}

/*
 * Abort on I/O error.
 * :param func: The name of the function, which failed.
 * :param filename: The name of the file.
 */
void abort_io(const char *func, const char *filename) {
	LOG(ERROR, "Fatal %s(%s): %s", func, filename, strerror(errno));
	abort();
}
