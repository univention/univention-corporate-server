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
#define _GNU_SOURCE
#define __USE_GNU

#include <limits.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <univention/debug.h>

#include "cache.h"
#include "index.h"
#include "network.h"
#include "notify.h"

#define MAX_LINE 4096

extern NotifyId_t notify_last_id;
extern Notify_t notify;
extern long long notifier_lock_count;
extern long long notifier_lock_time;

extern unsigned long SCHEMA_ID;

/*
 * Open file (and its corresponding locking file).
 * :param name: The name of the file to open.
 * :param type: The open mode.
 * :param l_file: Return variable for locking file.
 * :returns: The FILE pointer.
 */
static FILE *fopen_lock(const char *name, const char *type, FILE **l_file) {
	char buf[PATH_MAX];
	FILE *file;
	int count = 0;
	int l_fd;

	if (!(strcmp(name, FILE_NAME_TF))) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK %s", FILE_NAME_TF);
	} else if (!(strcmp(name, FILE_NAME_TF_IDX))) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK %s", FILE_NAME_TF_IDX);
	}

	snprintf(buf, sizeof(buf), "%s.lock", name);

	if ((*l_file = fopen(buf, "a")) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "ERROR Could not open lock file [%s]\n", buf);
		return NULL;
	}

	l_fd = fileno(*l_file);
	for (;;) {
		int rc = lockf(l_fd, F_TLOCK, 0);
		if (!rc)
			break;
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Could not get lock for file [%s]; count=%d\n", buf, count);
		count++;
		if (count > notifier_lock_count) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Could not get lock for file [%s]; exit\n", buf);
			exit(0);
		}
		usleep(notifier_lock_time);
	}

	if ((file = fopen(name, type)) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "ERROR Could not open file [%s]\n", name);

		lockf(l_fd, F_ULOCK, 0);
		fclose(*l_file);
		*l_file = NULL;
	}

	return file;
}

/*
 * Close file (and its corresponding locking file)
 * :param name: The name of the file to close (for debuuging output).
 * :param file: The FILE pointer to close.
 * :param l_file: The FILE pointer of the locking file to close.
 * :returns: 0
 */
static int fclose_lock(const char *name, FILE **file, FILE **l_file) {
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "FCLOSE start");
	if (*file != NULL) {
		fclose(*file);
		*file = NULL;
	}

	if (*l_file != NULL) {
		int l_fd = fileno(*l_file);
		int rc = lockf(l_fd, F_ULOCK, 0);
		if (rc)
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "unlockf(): %d", rc);
		fclose(*l_file);
		*l_file = NULL;
	}

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "FCLOSE end");

	if (!(strcmp(name, FILE_NAME_TF))) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "UNLOCK %s", FILE_NAME_TF);
	} else if (!(strcmp(name, FILE_NAME_TF_IDX))) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "UNLOCK %s", FILE_NAME_TF_IDX);
	}
	return 0;
}

/* Allocate and initialize a new entry.
 * :returns: A newly allocated and initialized transaction entry.
 */
static NotifyEntry_t *notify_entry_alloc() {
	NotifyEntry_t *entry = malloc(sizeof(NotifyEntry_t));
	if (entry)
		notify_entry_init(entry);
	return entry;
}

/*
 * Split character buffer into entries.
 * :param buf: The buffer to split.
 * :param l_buf: The number of charactewrs in the buffer.
 * :returns: Linked list of entries.
 */
static NotifyEntry_t *split_transaction_buffer(char *buf, long l_buf) {
	NotifyEntry_t *head, **tail;
	char *s;
	char *p_tmp1, *p_tmp2;

	tail = &head;
	for (s = strtok(buf, "\n"); s != NULL; s = strtok(NULL, "\n")) {
		NotifyEntry_t *trans = notify_entry_alloc();
		sscanf(s, "%ld", &(trans->notify_id.id));
		trans->command = s[strlen(s) - 1];
		p_tmp1 = index(s, ' ') + 1;
		p_tmp2 = rindex(p_tmp1, ' ');
		trans->dn = strndup(p_tmp1, p_tmp2 - p_tmp1);

		(*tail) = trans;
		tail = &trans->next;
	}

	return head;
}

/*
 * Write entries to files.
 * :param notify: Notifier configuration.
 * :param entry: Linked list of entries to write.
 */
static void notify_dump_to_files(Notify_t *notify, NotifyEntry_t *entry) {
	NotifyEntry_t *trans;
	FILE *index = NULL;

	if (entry == NULL)
		return;

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK from dump_to_files");
	if ((notify->tf = fopen_lock(FILE_NAME_TF, "a", &(notify->l_tf))) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "ERROR on open tf\n");
		goto error;
	}
	if ((index = index_open(FILE_NAME_TF_IDX)) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "unable to open index\n");
		goto error;
	}

	for (trans = entry; trans != NULL; trans = trans->next) {
		if (trans->dn != NULL && trans->notify_id.id >= 0) {
			index_set(index, trans->notify_id.id, ftell(notify->tf));
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "want to write to transaction file; id=%ld", trans->notify_id.id);
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "wrote to transaction file; id=%ld; dn=%s, cmd=%c", trans->notify_id.id, trans->dn, trans->command);
			fprintf(notify->tf, "%ld %s %c\n", trans->notify_id.id, trans->dn, trans->command);
		} else {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "trans->dn == NULL; id=%ld", trans->notify_id.id);
		}
	}
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "wrote to transaction file; close");

error:
	if (index)
		fclose(index);
	fclose_lock(FILE_NAME_TF, &notify->tf, &notify->l_tf);
}

/*
 * Initialize Notifier configuration.
 * :param notify: Notifier configuration.
 */
void notify_init(Notify_t *notify) {
	notify->tf = NULL;
	notify->l_tf = NULL;
}

/*
 * Initialize entry object.
 * :param entry: The entry object.
 */
void notify_entry_init(NotifyEntry_t *entry) {
	memset(entry, 0, sizeof(NotifyEntry_t));
}

/*
 * Return last notifiert ID.
 * :param notify: Notifier configuration.
 * :param notify_id: Notifier ID.
 * :returns: -1 on errors, 0 on success.
 * FIXME: this reads characters from the end of the file by seeking and reading N characters until a complete line is found.
 */
int notify_transaction_get_last_notify_id(Notify_t *notify, NotifyId_t *notify_id) {
	int i = 2;
	char c;

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK from notify_transaction_get_last_notify_id");
	if ((notify->tf = fopen_lock(FILE_NAME_TF, "r", &(notify->l_tf))) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "unable to lock notify_id\n");
		notify_id->id = 0;
		return -1;
	}

	do {
		i++;
		fseek(notify->tf, -i, SEEK_END);
		c = fgetc(notify->tf);
	} while (c != '\n' && c != -1 && c != 255 && ftell(notify->tf) != 1);

	if (c == -1 || c == 255) {
		/* empty file */
		notify_id->id = 0;
	} else if (ftell(notify->tf) == 1) {
		/* only one entry */
		fseek(notify->tf, 0, SEEK_SET);
		fscanf(notify->tf, "%ld", &(notify_id->id));
	} else {
		fscanf(notify->tf, "%ld", &(notify_id->id));
	}

	fclose_lock(FILE_NAME_TF, &notify->tf, &notify->l_tf);

	return 0;
}

/*
 * Free linked list of entry objects.
 * :param entry: The first entry object.
 */
void notify_entry_free(NotifyEntry_t *entry) {
	while (entry != NULL) {
		NotifyEntry_t *trans = entry;
		entry = entry->next;
		free(trans->dn);
		free(trans);
	}
}

/*
 * Return single transaction.
 * :param last_known_id: The transaction ID to lookup.
 * :returns: A string with transactions ID, DN and command separated by one blank.
 */
char *notify_transcation_get_one_dn(unsigned long last_known_id) {
	char buffer[2048];
	int i;
	char c;
	unsigned long id;
	bool found = false;
	FILE *index = NULL;
	ssize_t pos;

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK from notify_transcation_get_one_dn");
	if ((notify.tf = fopen_lock(FILE_NAME_TF, "r", &(notify.l_tf))) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "unable to lock tf\n");
		return NULL;
	}
	if ((index = index_open(FILE_NAME_TF_IDX)) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "unable to open index\n");
		goto error;
	}

	i = 0;
	memset(buffer, 0, sizeof(buffer));

	if ((pos = index_get(index, last_known_id)) >= 0) {
		fseek(notify.tf, pos, SEEK_SET);
		if (fgets(buffer, sizeof(buffer), notify.tf) != NULL) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "BUFFER=%s", buffer);
			if (buffer[strlen(buffer) - 1] == '\n') {
				buffer[strlen(buffer) - 1] = '\0';
			}
			if (sscanf(buffer, "%ld", &id) != 1) {
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Failed to parse %s", buffer);
			}
			if (id == last_known_id) {
				found = true;
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Found (get_one_dn, index) %ld", id);
			}
		}
	}

	fseek(notify.tf, 0, SEEK_SET);
	pos = 0;
	while (!found && (c = fgetc(notify.tf)) != EOF) {
		if (c == 255) {
			break;
		}

		if (c == '\n') {
			if (sscanf(buffer, "%ld", &id) != 1) {
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Failed to parse %s", buffer);
				break;
			}

			index_set(index, id, pos);

			if (id == last_known_id) {
				found = true;
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Found (get_one_dn) %ld", id);
				break;
			}

			i = 0;
			pos = ftell(notify.tf);
			memset(buffer, 0, 2048);
		} else {
			buffer[i] = c;
			i++;
		}
	}

error:
	if (index)
		fclose(index);
	fclose_lock(FILE_NAME_TF, &notify.tf, &notify.l_tf);

	if (found && strlen(buffer) > 0) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Return str [%s]", buffer);
		return strdup(buffer);
	} else {
		return NULL;
	}
}

/*
 * Convert entry to string.
 * :returns: A string with transactions ID, DN and command separated by one blank.
 */
static char *notify_entry_to_string(NotifyEntry_t entry) {
	char *str;

	if (entry.dn == NULL)
		return NULL;

	if (asprintf(&str, "%ld %s %c\n", entry.notify_id.id, entry.dn, entry.command) < 0)
		return NULL;

	return str;
}

/*
 * Handle update of LDAP schema.
 * :param sig: signal number.
 * :param si: signal information.
 * :param data: Opaque data.
 */
void notify_schema_change_callback(int sig, siginfo_t *si, void *data) {
	FILE *file;

	if ((file = fopen("/var/lib/univention-ldap/schema/id/id", "r")) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "E: failed to open /var/lib/univention-ldap/schema/id");
		return;
	}

	fscanf(file, "%ld", &SCHEMA_ID);

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "NEW Schema ID = %ld", SCHEMA_ID);

	fclose(file);
}

/*
 * Handle transactions from slapd transaction log overlay.
 * :param sig: signal number.
 * :param si: signal information.
 * :param data: Opaque data.
 */
void notify_listener_change_callback(int sig, siginfo_t *si, void *data) {
	NotifyEntry_t *entry = NULL;
	FILE *file, *l_file;
	struct stat stat_buf;
	char *buf = NULL;
	int nread;

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "NOTIFY Listener");
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "... go");

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK from notify_listener_change_callback");
	if ((file = fopen_lock(FILE_NAME_LISTENER, "r+", &(l_file))) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Could not open %s\n", FILE_NAME_LISTENER);
	}

	if (stat(FILE_NAME_LISTENER, &stat_buf) != 0) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "stat error\n");
		goto error;
	}

	if (stat_buf.st_size == 0) {
		goto error;
	}

	if ((buf = calloc(stat_buf.st_size + 1, sizeof(char))) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "malloc error\n");
		goto error;
	}

	if ((nread = fread(buf, sizeof(char), stat_buf.st_size, file)) != 0) {
		entry = split_transaction_buffer(buf, nread);
		notify_dump_to_files(&notify, entry);
		fseek(file, 0, SEEK_SET);
		ftruncate(fileno(file), 0);

		{
			NotifyEntry_t *trans;
			char *dn_string = NULL;

			for (trans = entry; trans != NULL; trans = trans->next) {
				notifier_cache_add(trans->notify_id.id, trans->dn, trans->command);
				notify_last_id.id = trans->notify_id.id;
				dn_string = notify_entry_to_string(*trans);
				if (dn_string != NULL) {
					network_client_all_write(trans->notify_id.id, dn_string, strlen(dn_string));
					free(dn_string);
				}
			}
		}
	}

	notify_entry_free(entry);

	free(buf);

error:
	fclose_lock(FILE_NAME_LISTENER, &file, &l_file);

	return;
}
