/*
 * Univention Directory Notifier
 *
 * Copyright 2004-2021 Univention GmbH
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

#define __USE_GNU
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdbool.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/stat.h>
#include <time.h>
#include <ldap.h>
#include <sasl/sasl.h>
#include <assert.h>
#include <univention/debug.h>

#include "notify.h"
#include "network.h"
#include "cache.h"
#include "index.h"

#define MAX_PATH_LEN 4096
#define MAX_LINE 4096

extern NotifyId_t notify_last_id;
extern Notify_t notify;
extern long long notifier_lock_count;
extern long long notifier_lock_time;
extern void set_listener_callback(int sig, siginfo_t *si, void *data);
extern void unset_listener_callback ();

extern unsigned long SCHEMA_ID;

static FILE* fopen_lock(const char *name, const char *type)
{
	FILE *file;
	int count = 0;
	int fd;

	if ((file = fopen(name, type)) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "ERROR Could not open file [%s]\n", name);
		return NULL;
	}

	fd = fileno(file);
	for (;;) {
		int rc = lockf(fd, F_TLOCK, 0);
		if (!rc)
			break;
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Could not get lock for file [%s]; count=%d\n", name, count);
		count++;
		if (count > notifier_lock_count) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Could not get lock for file [%s]; exit\n", name);
			exit(0);
		}
		usleep(notifier_lock_time);
	}

	return file;
}

static FILE* fopen_dotlockfile(const char *name)
{
	char buf[MAX_PATH_LEN];
	FILE *file;

	snprintf( buf, sizeof(buf), "%s.lock", name );

	if ((file = fopen_lock(buf, "a")) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "ERROR Could not open lock file [%s]\n", buf);
		return NULL;
	}

	return file;
}


static FILE* fopen_with_lockfile(const char *name, const char *type, FILE **l_file)
{
	FILE *file;

	if ( !(strcmp(name, FILE_NAME_TF)) ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK %s", FILE_NAME_TF);
	} else if ( !(strcmp(name, FILE_NAME_TF_IDX)) ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK %s", FILE_NAME_TF_IDX);
	}

	if ((*l_file = fopen_dotlockfile(name)) == NULL) {
		return NULL;
	}

	if ((file = fopen(name, type)) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "ERROR Could not open file [%s]\n", name);

		int l_fd = fileno(*l_file);
		lockf(l_fd, F_ULOCK, 0);
		fclose(*l_file);
		*l_file = NULL;
	}

	return file;
}

static int fclose_lock(FILE **file)
{
	int rc = 0;
	if (*file != NULL) {
		int fd = fileno(*file);
		rc = lockf(fd, F_ULOCK, 0);
		if (rc)
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "unlockf(): %d", rc);
		rc = fclose(*file);
		*file  = NULL;
	}
	return rc;
}

static int fclose_with_lockfile(const char *name, FILE **file, FILE **l_file)
{
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "FCLOSE start");
	if (*file != NULL) {
		fclose(*file);
		*file = NULL;
	}

	fclose_lock(l_file);

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "FCLOSE end");

	if ( !(strcmp(name, FILE_NAME_TF)) ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "UNLOCK %s", FILE_NAME_TF);
	} else if ( !(strcmp(name, FILE_NAME_TF_IDX)) ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "UNLOCK %s", FILE_NAME_TF_IDX);
	}
	return 0;
}


/* Parse "<id> <dn with blanks> <command>\n" */
static int parse_transaction_line(NotifyEntry_t* entry, char* line)
{
	char *first_space_p = index(line, ' ');
	char *last_space_p = rindex(line, ' ');
	assert(first_space_p && last_space_p && first_space_p < last_space_p);
	size_t size = last_space_p - first_space_p - 1;
	entry->command = last_space_p[1];
	entry->dn = strndup(first_space_p + 1, size);
	return sscanf(line, "%ld", &(entry->notify_id.id));
}

static void notify_dump_to_files( Notify_t *notify, NotifyEntry_t *entry)
{
	char buffer[2048];
	FILE *index = NULL;

	if (entry == NULL)
		return;


	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK from dump_to_files");
	if ((notify->tf = fopen_with_lockfile(FILE_NAME_TF, "a", &(notify->l_tf))) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "ERROR on open tf\n");
		goto error;
	}
	if ((index = index_open(FILE_NAME_TF_IDX)) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "unable to open index\n");
		goto error;
	}

	if (entry->dn != NULL && entry->notify_id.id >= 0) {
		long offset = ftell(notify->tf);
		int len = snprintf(buffer, sizeof(buffer), "%ld %s %c\n", entry->notify_id.id, entry->dn, entry->command);
		if (len >= sizeof(buffer)) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "buffer too small");
			abort();
		}

		index_set(index, entry->notify_id.id, offset);
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "want to write to transaction file; id=%ld", entry->notify_id.id);
		if (fallocate(fileno(notify->tf), FALLOC_FL_KEEP_SIZE, offset, len) == -1 && (errno != ENOSYS) && (errno != EOPNOTSUPP)) {
			perror("Failed fallocate(tf)");
			abort();
		}
		if (fprintf(notify->tf, "%s", buffer) != len) {
			perror("Failed fprintf(tf)");
			abort();
		}
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "wrote to transaction file; id=%ld; dn=%s, cmd=%c", entry->notify_id.id, entry->dn, entry->command);
	} else {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "entry->dn == NULL; id=%ld", entry->notify_id.id);
	}

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "wrote to transaction file; close");

error:
	if (index)
		fclose(index);
	fclose_with_lockfile(FILE_NAME_TF, &notify->tf, &notify->l_tf);
}

/*
 * Callback for interactive SASL bind for mechanism "EXTERNAL".
 * :param ld: The LDAP connection.
 * :param flags: SASL flags.
 * :param default: Opaque object for defaults.
 * :param in: SASL interaction structure.
 * :returns: error status.
 * <https://adam.younglogic.com/2012/02/exteranl-sasl/>
 */
static int sasl_proc(LDAP *ld, unsigned flags, void *defaults, void *in) {
	sasl_interact_t *interact = in;
	const char *dflt = interact->defresult;
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "SASL: id=%ld chal=%s prom=%s def=%s", interact->id, interact->challenge, interact->prompt, interact->defresult);
	switch (interact->id) {
	case SASL_CB_USER:
		interact->result = "";
		interact->len = 0;
		return LDAP_SUCCESS;
	default:
		interact->result = (dflt && *dflt) ? dflt : "";
		interact->len = strlen(interact->result);
		return LDAP_INAPPROPRIATE_AUTH;
	}
}

/*
 * Write entries to cn=translog.
 * :param trans: Linked list of entries to write.
 */
static void notify_dump_to_ldap(NotifyEntry_t *trans) {
	static LDAP *ld = NULL;
	LDAPControl **serverctrls = NULL;
	LDAPControl **clientctrls = NULL;
	int rc;
	struct sigaction oldact, act = {
		.sa_handler = SIG_IGN,
		.sa_flags = 0,
	};

	if (trans == NULL)
		return;

	// libldap uses liblber uses write() on the SOCKET to slapd, which raises SIGPIPE when slapd closes the socket due to a timeout.
	sigaction(SIGPIPE, &act, &oldact);

reopen:
	if (!ld) {
		if ((rc = ldap_initialize(&ld, "ldapi:///")) != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "ldap_initialize(): %s", ldap_err2string(rc));
			abort();
		}

		unsigned long version = LDAP_VERSION3;
		if ((rc = ldap_set_option(ld, LDAP_OPT_PROTOCOL_VERSION, &version)) != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "ldap_set_option(): %s", ldap_err2string(rc));
			abort();
		}

		const char *who = NULL;
		const char mechanism[] = "EXTERNAL";
		unsigned flags = LDAP_SASL_QUIET;
		void *defaults = NULL;
		if ((rc = ldap_sasl_interactive_bind_s(ld, who, mechanism, serverctrls, clientctrls, flags, sasl_proc, defaults)) != LDAP_SUCCESS) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "ldap_sasl_interactive_bind_s(): %s", ldap_err2string(rc));
			abort();
		}
	}

	if (!trans->dn) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "Not writing entry with no DN to LDAP");
		return;
	}
	if (!trans->notify_id.id){
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "Not writing entry with no ID to LDAP");
		return;
	}

	char dn[44]; // strlen("reqSession=%ld,cn=translog") + strlen(ULONG_MAX)
	snprintf(dn, sizeof(dn), "reqSession=%ld,cn=translog", trans->notify_id.id);

	char *oc_values[] = { "auditObject", NULL };
	LDAPMod oc_mod = {
		.mod_op = LDAP_MOD_ADD,
		.mod_type = "objectClass",
		.mod_values = oc_values,
	};

	char start[16]; // strlen('YYYYmmddHHMMSSZ')
	time_t t = time(NULL);
	struct tm tm ;
	gmtime_r(&t, &tm);
	strftime(start, sizeof(start), "%Y%m%d%H%M%SZ", &tm);
	char *start_values[] = { start, NULL };
	LDAPMod time_mod = {
		.mod_op = LDAP_MOD_ADD,
		.mod_type = "reqStart",
		.mod_values = start_values,
	};

	char id[21];  // strlen(ULONG_MAX)
	snprintf(id, sizeof(id), "%ld", trans->notify_id.id);
	char *index_values[] = { id, NULL };
	LDAPMod index_mod = {
		.mod_op = LDAP_MOD_ADD,
		.mod_type = "reqSession",
		.mod_values = index_values,
	};

	char *dn_values[] = { trans->dn, NULL };
	LDAPMod dn_mod = {
		.mod_op = LDAP_MOD_ADD,
		.mod_type = "reqDN",
		.mod_values = dn_values,
	};

	char cmd[2];
	cmd[0] = trans->command;
	cmd[1] = '\0';
	char *cmd_values[] = { cmd, NULL };
	LDAPMod cmd_mod = {
		.mod_op = LDAP_MOD_ADD,
		.mod_type = "reqType",
		.mod_values = cmd_values,
	};

	LDAPMod *attrs[] = {
		&oc_mod,
		&time_mod,
		&index_mod,
		&dn_mod,
		&cmd_mod,
		NULL
	};

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LDIF dn: %s", dn);
	for (rc = 0; attrs[rc]; rc++)
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LDIF %s: %s", attrs[rc]->mod_type, attrs[rc]->mod_values[0]);

	rc = ldap_add_ext_s(ld, dn, attrs, serverctrls, clientctrls);
	switch (rc) {
		case LDAP_SUCCESS:
			break;
		case LDAP_SERVER_DOWN:
			if ((rc = ldap_unbind_ext_s(ld, serverctrls, clientctrls)) != LDAP_SUCCESS)
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "%ld ldap_unbind_ext_s(): %s", trans->notify_id.id, ldap_err2string(rc));
			ld = NULL;
			goto reopen;
		case LDAP_ALREADY_EXISTS:
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "%ld ldap_add() already exists", trans->notify_id.id);
			break;
		default:
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "%ld ldap_add(): %s", trans->notify_id.id, ldap_err2string(rc));
			abort();
	}

	sigaction(SIGPIPE, &oldact, NULL);
}

void notify_init ( Notify_t *notify )
{
	notify->tf    = NULL;
	notify->l_tf  = NULL;
}


int notify_transaction_get_last_notify_id ( Notify_t *notify, NotifyId_t *notify_id )
{
	int i = 2;
	char c;

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK from notify_transaction_get_last_notify_id");
	if ((notify->tf = fopen_with_lockfile(FILE_NAME_TF, "r", &(notify->l_tf))) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "unable to lock notify_id\n");
		notify_id->id = 0;
		return -1;
	}

	do {
		i++;
		fseek( notify->tf, -i, SEEK_END);
		c = fgetc ( notify->tf ) ;
	} while ( c != '\n' && c != -1 && c != 255 && ftell(notify->tf) != 1);

	if ( c == -1 || c == 255 ) {
		/* empty file */
		notify_id->id = 0;

	} else if ( ftell(notify->tf) == 1) {

		/* only one entry */
		fseek( notify->tf, 0, SEEK_SET);
		fscanf(notify->tf, "%ld",& (notify_id->id));

	} else {
		fscanf(notify->tf, "%ld",& (notify_id->id));
	}

	fclose_with_lockfile(FILE_NAME_TF, &notify->tf, &notify->l_tf);

	return 0;
}


char* notify_transcation_get_one_dn ( unsigned long last_known_id )
{
	char buffer[2048];
	int i;
	char c;
	unsigned long id;
	bool found = false;
	FILE *index = NULL;
	size_t pos;


	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK from notify_transcation_get_one_dn");
	if ((notify.tf = fopen_with_lockfile(FILE_NAME_TF, "r", &(notify.l_tf))) == NULL) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "unable to lock tf\n");
		return NULL;
	}
	if ( ( index = index_open(FILE_NAME_TF_IDX) ) == NULL ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "unable to open index\n");
		goto error;
	}

	i=0;
	memset(buffer, 0, sizeof(buffer));

	if ((pos = index_get(index, last_known_id)) != -1) {
		fseek(notify.tf, pos, SEEK_SET);
		if (fgets(buffer, sizeof(buffer), notify.tf) != NULL) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "BUFFER=%s", buffer);
			if ( buffer[strlen(buffer)-1] == '\n' ) {
				buffer[strlen(buffer)-1] = '\0';
			}
			sscanf(buffer, "%ld", &id);
			if (id == last_known_id) {
				found = true;
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Found (get_one_dn, index) %ld",id);
			}
		}
	}

	fseek(notify.tf, 0, SEEK_SET);
	pos = 0;
	while (!found && (c=fgetc(notify.tf)) != EOF ) {
		if ( c == 255 ) {
			break;
		}

		if ( c == '\n' ) {
			sscanf(buffer, "%ld", &id) ;

			index_set(index, id, pos);

			if ( id == last_known_id ) {
				found = true;
				univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Found (get_one_dn) %ld",id);
				break;
			}

			i=0;
			pos=ftell(notify.tf);
			memset(buffer, 0, 2048);
		} else {
			buffer[i] = c;
			i++;
		}
	}

error:
	if (index)
		fclose(index);
	fclose_with_lockfile(FILE_NAME_TF, &notify.tf, &notify.l_tf);

	if (found && strlen(buffer) > 0) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Return str [%s]", buffer);
		return strdup(buffer);
	} else {
		return NULL;
	}
}

void notify_schema_change_callback(int sig, siginfo_t *si, void *data)
{
	FILE *file;

	if ( (file = fopen("/var/lib/univention-ldap/schema/id/id", "r" )) == NULL ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "E: failed to open /var/lib/univention-ldap/schema/id");
		return;
	}

	fscanf(file, "%ld", &SCHEMA_ID);

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "NEW Schema ID = %ld", SCHEMA_ID);

	fclose(file);

}

void notify_listener_change_callback(int sig, siginfo_t *si, void *data)
{
	NotifyEntry_t entry = {0,};
	FILE *file, *l_file;
	int fd;
	int rc;
	struct stat stat_buf;

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "NOTIFY Listener" );
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "... go");

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK from notify_listener_change_callback");
	rc = stat(FILE_NAME_NOTIFIER_PRIV, &stat_buf);
	if ( (rc == -1) || (stat_buf.st_size == 0) ) {
		rc = stat(FILE_NAME_LISTENER, &stat_buf);
		if ( (rc == -1) || (stat_buf.st_size == 0) ) {
			return;
		}

		if ( ( l_file = fopen_dotlockfile ( FILE_NAME_LISTENER ) ) == NULL ) {
			exit(0);
		}

		rename(FILE_NAME_LISTENER, FILE_NAME_NOTIFIER_PRIV);

		// Some tools expect the file to exist
		fd = open(FILE_NAME_LISTENER, O_RDWR | O_CREAT, stat_buf.st_mode);
		if (fd != -1) {
			fchown(fd, stat_buf.st_uid, stat_buf.st_gid);
			close(fd);
		}

		unset_listener_callback();
		fclose_lock(&l_file);
	} else {
		set_listener_callback(0, NULL, NULL);
	}

	if ( ( file = fopen_lock (FILE_NAME_NOTIFIER_PRIV, "r+") ) == NULL ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Could not open %s\n", FILE_NAME_NOTIFIER_PRIV);
	}

	char *line = NULL;
	size_t len = 0;
	int parse_results;
	while (getline(&line, &len, file) != -1) {
		parse_results = parse_transaction_line(&entry, line);
		if (parse_results!=1) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "ABORTING EXECUTION: Invalid transaction ID for line %s of file %s", line, FILE_NAME_NOTIFIER_PRIV);
			free(line);
			fclose_lock(&file);
			abort();
		}
		if (entry.notify_id.id <= notify_last_id.id) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_PROCESS, "Skipping old Transaction ID %ld before %ld from %s", entry.notify_id.id, notify_last_id.id, FILE_NAME_NOTIFIER_PRIV);
			continue;
		}
		notify_dump_to_ldap(&entry);
		notify_dump_to_files(&notify, &entry);
		notifier_cache_add(entry.notify_id.id, entry.dn, entry.command);
		notify_last_id.id = entry.notify_id.id;
		network_client_all_write(entry.notify_id.id, line, strlen(line));
		free(entry.dn);
		entry.dn = NULL;
	}

	unlink(FILE_NAME_NOTIFIER_PRIV);
	free(line);
	fclose_lock(&file);
}
