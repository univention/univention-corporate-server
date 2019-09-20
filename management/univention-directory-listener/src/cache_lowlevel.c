/*
 * Univention Directory Listener
 *  cache_lowlevel.c
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

#define _GNU_SOURCE /* for strndup */

#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#include <limits.h>
#include <errno.h>
#include <sys/types.h>

#include <univention/debug.h>

#include "common.h"
#include "cache_lowlevel.h"

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
void hex_dump(int level, void *data, u_int32_t start, u_int32_t size) {
	int i;
	int pos;
	char hex[80];
	char str[80];
	const int per_line = 10;

	pos = 0;
	memset(hex, 0, 80);
	memset(str, 0, 80);

	for (i = 0; i < size; i++) {
		snprintf(hex + (pos * 3), 80 - (pos * 3), "%02x ", ((u_int8_t *)data + start)[i]);
		snprintf(str + pos, 80 - pos, "%c", isprint(((char *)data + start)[i]) ? ((char *)data + start)[i] : '?');
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
static int append_buffer(void **data, u_int32_t *pos, void *blob_data, u_int32_t blob_size) {
	if (blob_size > 0) {
		memcpy((void *)(((char *)*data) + *pos), blob_data, blob_size);
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "position was=%d is=%d", *pos, *pos + blob_size);
		*pos += blob_size;
	}
	return 0;
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
static int write_header(void **data, u_int32_t *size, u_int32_t *pos, u_int16_t type, void *key_data, u_int32_t key_size, void *data_data, u_int32_t data_size) {
	struct cache_entry_header h;
	u_int32_t need_memory;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "write_header key_size=%d data_size=%d", key_size, data_size);

	need_memory = sizeof(struct cache_entry_header) + key_size + data_size;
	if (*size < *pos + need_memory) {
		while (*size < *pos + need_memory)
			*size += BUFSIZ;
		if ((*data = realloc(*data, *size)) == NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to allocate memory");
			return 1;
		}
	}

	h.type = type;
	h.key_size = key_size;
	h.data_size = data_size;

	append_buffer(data, pos, (void *)&h, sizeof(struct cache_entry_header));
	append_buffer(data, pos, key_data, key_size);
	append_buffer(data, pos, data_data, data_size);

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
	int i;
	u_int32_t pos = 0;

	for (attribute = entry->attributes; attribute != NULL && *attribute != NULL; attribute++) {
		for (value = (*attribute)->values, i = 0, length = (*attribute)->length; *value != NULL; value++, i++) {
			write_header(data, size, &pos, 1, (void *)(*attribute)->name, strlen((*attribute)->name) + 1, (void *)*value, length[i]);
		}
	}
	for (module = entry->modules; module != NULL && *module != NULL; module++) {
		write_header(data, size, &pos, 2, (void *)*module, strlen(*module) + 1, NULL, 0);
	}

	/* allocated memory maybe bigger than size, but doesn't matter anyhow... */
	*size = pos;

	return 0;
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
static int read_header(void *data, u_int32_t size, u_int32_t *pos, void **key_data, u_int32_t *key_size, void **data_data, u_int32_t *data_size) {
	struct cache_entry_header *h;

	if (*pos == size) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "end of buffer pos=size=%d", *pos);
		return 0;
	} else if (*pos + sizeof(struct cache_entry_header) > size) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "buffer exceeded pos=%d size=%d", *pos, size);
		return -1;
	}

	h = (struct cache_entry_header *)((char *)data + *pos);

	if ((h->type != 1 && h->type != 2) || h->key_size == 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "read_header pos=%d type=%d key_size=%d data_size=%d", *pos, h->type, h->key_size, h->data_size);
		*key_size = 0;
		*key_data = NULL;
		*data_size = 0;
		*data_data = NULL;
		return -1;
	}
	*pos += sizeof(struct cache_entry_header);
	if (*pos + h->key_size + h->data_size > size) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "buffer exceeded pos=%d size=%d", *pos, size);
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
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "read_header pos=%d type=%d key_size=%d data_size=%d key_data=[%s] data_data=[%s]", *pos, h->type, h->key_size, h->data_size, (char *)*key_data,
	                 (char *)*data_data);

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
	u_int16_t type;
	void *key_data, *data_data;
	u_int32_t key_size, data_size;
	u_int32_t pos = 0;

	entry->attributes = NULL;
	entry->attribute_count = 0;
	entry->modules = NULL;
	entry->module_count = 0;

	while ((type = read_header(data, size, &pos, &key_data, &key_size, &data_data, &data_size)) > 0) {
		if (type == 1) {
			CacheEntryAttribute **attribute, *c_attr;

			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "attribute is \"%s\"", (char *)key_data);

			for (attribute = entry->attributes, c_attr = NULL; attribute != NULL && *attribute != NULL; attribute++) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "current attribute is \"%s\"", (*attribute)->name);
				if (strcmp((*attribute)->name, (char *)key_data) == 0) {
					c_attr = *attribute;
					break;
				}
			}
			if (!c_attr) {
				if (!(entry->attributes = realloc(entry->attributes, (entry->attribute_count + 2) * sizeof(CacheEntryAttribute *)))) {
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "realloc failed");
					abort();  // FIXME
				}
				if (!(c_attr = malloc(sizeof(CacheEntryAttribute)))) {
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "malloc failed");
					abort();  // FIXME
				}
				if (!(c_attr->name = strndup((char *)key_data, key_size))) {
					univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "strndup failed");
					abort();  // FIXME
				}
				c_attr->values = NULL;
				c_attr->length = NULL;
				c_attr->value_count = 0;
				entry->attributes[entry->attribute_count++] = c_attr;
				entry->attributes[entry->attribute_count] = NULL;

				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "%s is at %p", c_attr->name, c_attr);
			}
			if (!(c_attr->values = realloc(c_attr->values, (c_attr->value_count + 2) * sizeof(char *)))) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "realloc failed");
				abort();  // FIXME
			}
			if (!(c_attr->length = realloc(c_attr->length, (c_attr->value_count + 2) * sizeof(int)))) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "realloc failed");
				abort();  // FIXME
			}
			if (!(c_attr->values[c_attr->value_count] = malloc(data_size))) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "malloc() failed");
				abort();  // FIXME
			}
			c_attr->length[c_attr->value_count] = data_size;
			memcpy(c_attr->values[c_attr->value_count], data_data, data_size);
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "value is \"%s\"", c_attr->values[c_attr->value_count]);
			c_attr->values[++c_attr->value_count] = NULL;
		} else if (type == 2) {
			entry->modules = realloc(entry->modules, (entry->module_count + 2) * sizeof(char *));
			if (!(entry->modules[entry->module_count] = strndup((char *)key_data, key_size))) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "strndup failed");
				abort();  // FIXME
			}
			entry->modules[++entry->module_count] = NULL;
		} else {
			char filename[PATH_MAX];
			FILE *file;
			u_int32_t len;
			int rv;

			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "bad data block at position %d:", pos);
			len = pos < 1000 ? pos : 1000;
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "last %d bytes of previous entry:", len);
			hex_dump(UV_DEBUG_ERROR, data, pos < 1000 ? 0 : pos - 1000, len);
			len = pos + 1000 > size ? size - pos : 1000;
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "first %d bytes of current entry:", len);
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

	return 0;
}

/*
 * Abort on I/O error.
 * :param func: The name of the function, which failed.
 * :param filename: The name of the file.
 */
void abort_io(const char *func, const char *filename) {
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Fatal %s(%s): %s", func, filename, strerror(errno));
	abort();
}
