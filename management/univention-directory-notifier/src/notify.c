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

#define __USE_GNU
#include <sys/file.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdbool.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <pthread.h>

#include <univention/debug.h>
#include "notify.h"
#include "network.h"
#include "cache.h"
#include "index.h"
#include "sem.h"

#define MAX_PATH_LEN 4096
#define MAX_LINE 4096

extern int sem_id;

extern NotifyId_t notify_last_id;
extern Notify_t notify;
extern int ONLY_NOTIFY;
extern int WRITE_SAVE_REPLOG;
extern int WRITE_REPLOG;
extern long long replog_sleep;
extern long long notifier_lock_count;
extern long long notifier_lock_time;

extern char *strndup (__const char *__string, size_t __n);

extern unsigned long SCHEMA_ID;

static pthread_mutex_t mut_replog = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t mut_orf = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t mut_tf = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t mut_tf_idx = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t mut_save = PTHREAD_MUTEX_INITIALIZER;


void notify_id_get_next(NotifyId_t *next_notify);



static FILE* fopen_lock(const char *name, const char *type, FILE **l_file)
{
	char buf[MAX_PATH_LEN];
	FILE *file;
	int count = 0;
	int l_fd;

	if ( !(strcmp(name, FILE_NAME_ORF)) ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK %s", FILE_NAME_ORF);
		pthread_mutex_lock(&mut_orf);
	} else if ( !(strcmp(name, FILE_NAME_TF)) ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK %s", FILE_NAME_TF);
		pthread_mutex_lock(&mut_tf);
	} else if ( !(strcmp(name, FILE_NAME_TF_IDX)) ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK %s", FILE_NAME_TF_IDX);
		pthread_mutex_lock(&mut_tf_idx);
	} else if ( !(strcmp(name, FILE_NAME_SAVE)) ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK %s", FILE_NAME_SAVE);
		pthread_mutex_lock(&mut_save);
	}

	snprintf( buf, sizeof(buf), "%s.lock", name );

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

static int fclose_lock(const char *name, FILE **file, FILE **l_file)
{
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
		*l_file  = NULL;
	}

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "FCLOSE end");

	if ( !(strcmp(name, FILE_NAME_ORF)) ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "UNLOCK %s", FILE_NAME_ORF);
		pthread_mutex_unlock(&mut_orf);
	} else if ( !(strcmp(name, FILE_NAME_TF)) ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "UNLOCK %s", FILE_NAME_TF);
		pthread_mutex_unlock(&mut_tf);
	} else if ( !(strcmp(name, FILE_NAME_TF_IDX)) ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "UNLOCK %s", FILE_NAME_TF_IDX);
		pthread_mutex_unlock(&mut_tf_idx);
	} else if ( !(strcmp(name, FILE_NAME_SAVE)) ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "UNLOCK %s", FILE_NAME_SAVE);
		pthread_mutex_unlock(&mut_save);
	}
	return 0;
}

/* Allocate and initialize a new entry. */
static NotifyEntry_t *notify_entry_alloc()
{
	NotifyEntry_t *entry = malloc(sizeof(NotifyEntry_t));
	if (entry)
		notify_entry_init(entry);
	return entry;
}

static long split_transaction_buffer ( NotifyEntry_t *entry, char *buf, long l_buf)
{
	NotifyEntry_t *tmp=NULL;
	NotifyEntry_t *tmp2=NULL;

	int size;

	int start=1;

	char *p, *p1;

	char *s;

	char *p_tmp1, *p_tmp2;

	tmp2=entry;

	p1=strndup(buf, l_buf);
	p=p1;

	for ( s=strtok(p,"\n"); s!= NULL; s=strtok(NULL,"\n") ) {
		if ( start ) {
			tmp2->buf = NULL;
			tmp2->l_buf = 0;
			tmp2->used=1;

			sscanf(s, "%ld", &(tmp2->notify_id.id));
			tmp2->command=s[strlen(s)-1];
			p_tmp1=index(s, ' ');
			p_tmp2=rindex(s, ' ');
			size=p_tmp2-p_tmp1;
			tmp2->dn=malloc((size)*sizeof(char));
			memcpy( tmp2->dn, p_tmp1+1, p_tmp2-p_tmp1);
			tmp2->dn[size-1]='\0';

			tmp2->next=NULL;
		} else {
			tmp = notify_entry_alloc();

			sscanf(s, "%ld", &(tmp->notify_id.id));
			tmp->command=s[strlen(s)-1];
			p_tmp1=index(s, ' ');
			p_tmp2=rindex(s, ' ');
			size=p_tmp2-p_tmp1;
			tmp->dn=malloc((size)*sizeof(char));
			memcpy( tmp->dn, p_tmp1+1, p_tmp2-p_tmp1);
			tmp->dn[size-1]='\0';

			tmp->buf = NULL;
			tmp->l_buf = 0;
			tmp->used=1;

			tmp->next=NULL;
			tmp2->next=tmp;
			tmp2=tmp;
		}

		start=0;
	}

	free(p1);
	return 0;
}

void notify_dump_to_files( Notify_t *notify, NotifyEntry_t *entry)
{
	NotifyEntry_t *tmp;
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
	if (WRITE_REPLOG) {
		if ((notify->orf = fopen_lock(FILE_NAME_ORF, "a", &(notify->l_orf))) == NULL) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "ERROR on open orf\n");
			goto error;
		}
	}
	if (WRITE_SAVE_REPLOG) {
		if ((notify->save = fopen_lock(FILE_NAME_SAVE, "a", &(notify->l_save))) == NULL) {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "ERROR on open orf\n");
			goto error;
		}
	}

	for (tmp = entry; tmp != NULL; tmp = tmp->next) {
		if (tmp->dn != NULL && tmp->notify_id.id >= 0) {
			index_set(index, tmp->notify_id.id, ftell(notify->tf));
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "want to write to transaction file; id=%ld", tmp->notify_id.id);
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "wrote to transaction file; id=%ld; dn=%s, cmd=%c", tmp->notify_id.id, tmp->dn, tmp->command);
			fprintf(notify->tf, "%ld %s %c\n", tmp->notify_id.id, tmp->dn, tmp->command);
			if (tmp->buf != NULL) {
				if (WRITE_REPLOG)
					fprintf(notify->orf, "%s", tmp->buf);
				if (WRITE_SAVE_REPLOG)
					fprintf(notify->save, "%s", tmp->buf);
			}
			if (WRITE_REPLOG)
				fprintf(notify->orf, "\n");
		} else {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "tmp->dn == NULL; id=%ld", tmp->notify_id.id);
		}
	}
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "wrote to transaction file; close");

error:
	if (index)
		fclose(index);
	fclose_lock(FILE_NAME_TF, &notify->tf, &notify->l_tf);
	fclose_lock(FILE_NAME_ORF, &notify->orf, &notify->l_orf);
	fclose_lock(FILE_NAME_SAVE, &notify->save, &notify->l_save);
}

void notify_init ( Notify_t *notify )
{
	notify->irf   = NULL;
	notify->l_irf = NULL;

	notify->orf   = NULL;
	notify->l_orf = NULL;

	notify->tf    = NULL;
	notify->l_tf  = NULL;

	notify->save    = NULL;
	notify->l_save  = NULL;
}

void notify_entry_init(NotifyEntry_t *entry)
{
	memset(entry, 0, sizeof(NotifyEntry_t));
}

void notify_id_get_next(NotifyId_t *next_notify)
{
	notify_last_id.id += 1;
	next_notify->id = notify_last_id.id;
}

int notify_transaction_get_last_notify_id ( Notify_t *notify, NotifyId_t *notify_id )
{
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
		fseek( notify->tf, -i, SEEK_END);
		c = fgetc ( notify->tf ) ;
	} while ( c != '\n' && c != -1 && c != 255 && ftell(notify->tf) != 1);

	if ( c == -1 || c == 255 ) {
		/* emty file */
		notify_id->id = 0;

	} else if ( ftell(notify->tf) == 1) {

		/* only one entry */
		fseek( notify->tf, 0, SEEK_SET);
		fscanf(notify->tf, "%ld",& (notify_id->id));

	} else {
		fscanf(notify->tf, "%ld",& (notify_id->id));
	}

	fclose_lock(FILE_NAME_TF, &notify->tf, &notify->l_tf);

	return 0;
}

void notify_entry_free(NotifyEntry_t *entry )
{
	NotifyEntry_t *tmp = entry;
	NotifyEntry_t *tmp2;

	while ( tmp != NULL ) {
		if ( tmp->dn) free(tmp->dn);
		if ( tmp->buf) free(tmp->buf);
		if ( tmp->newrdn) free(tmp->newrdn);
		if ( tmp->newsuperior) free(tmp->newsuperior);
		tmp2=tmp;
		tmp=tmp->next;
		free(tmp2);
	}
}

NotifyEntry_t* notify_entry_reverse ( NotifyEntry_t *entry )
{
	NotifyEntry_t *tmp;
	NotifyEntry_t *tmp2;
	NotifyEntry_t *tmp3 = NULL;

	tmp=entry;

	while ( tmp!=NULL ) {
		tmp2=tmp3;

		tmp3=tmp;

		tmp=tmp->next;

		/* first */
		tmp3->next=tmp2;

	}

	return tmp3;
}

char* notify_transcation_get_one_dn ( unsigned long last_known_id )
{
	char buffer[2048];
	int i, size;
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
	if ( ( index = index_open(FILE_NAME_TF_IDX) ) == NULL ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_WARN, "unable to open index\n");
		goto error;
	}

	i=0;
	memset(buffer, 0, sizeof(buffer));

	if ((pos = index_get(index, last_known_id)) >= 0) {
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
			size = sscanf(buffer, "%ld", &id) ;

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
	fclose_lock(FILE_NAME_TF, &notify.tf, &notify.l_tf);

	if (found && strlen(buffer) > 0) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_INFO, "Return str [%s]", buffer);
		return strdup(buffer);
	} else {
		return NULL;
	}
}

char* notify_entry_to_string(NotifyEntry_t entry )
{
	int len = 0;
	char *str, *p;
	char buffer[32];
	int rc;

	if ( entry.dn == NULL ) {
		return NULL;
	}

	if ( entry.used ) {
		len += 4; /* space + space + newline */
		len += strlen(entry.dn);
		len += snprintf(buffer,32, "%ld",entry.notify_id.id);
	}

	len+=1;
	if ( (str = malloc(len*sizeof(char) ) ) == NULL ) {
		return NULL;
	}

	memset(str, 0, len);
	p=str;

		if ( entry.used ) {
			rc = sprintf(p, "%ld %s %c\n", entry.notify_id.id, entry.dn, entry.command);
			p+=rc;
		} else {
			univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "Entry unused");
		}

	return str;

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

static char* modrdn(char *dn, char *newrdn, char *newsuperior )
{
	char *new_string;

	if ( newsuperior != NULL ) {
		new_string=malloc(strlen(newsuperior) + strlen(newrdn) +2 );
		memset ( new_string, 0, strlen(newsuperior) + strlen(newrdn) );

		strcpy(new_string, newrdn);

		strcat(new_string, ",");
		strcat(new_string, newsuperior);
	} else {
		new_string=malloc(strlen(dn) + strlen(newrdn) +1 );
		memset ( new_string, 0, strlen(dn) + strlen(newrdn) );

		strcpy(new_string, newrdn);

		strcat(new_string, index(dn, ','));
	}

	return new_string;
}

int sig_block_count = 0;
sigset_t block_mask;

void signals_block(void)
{
	static int init_done = 0;

	if ((++sig_block_count) != 1)
		return;

	if (init_done == 0) {
		sigemptyset(&block_mask);
		sigaddset(&block_mask, SIGPIPE);
		sigaddset(&block_mask, SIGHUP);
		sigaddset(&block_mask, SIGINT);
		sigaddset(&block_mask, SIGQUIT);
		sigaddset(&block_mask, SIGTERM);
		sigaddset(&block_mask, SIGABRT);
		sigaddset(&block_mask, SIGCHLD);
		sigaddset(&block_mask, SIGUSR1);
		init_done = 1;
	}

	sigprocmask(SIG_BLOCK, &block_mask, NULL);
}

void signals_unblock(void)
{
	if ((--sig_block_count) != 0)
		return;
	sigprocmask(SIG_UNBLOCK, &block_mask, NULL);
}

void notify_replog_change_callback(int sig, siginfo_t *si, void *data)
{
	NotifyEntry_t *entry;

	FILE *file, *l_file;

	char line[MAX_LINE];

	bool first = true;

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "notify_replog_change_callback");

	/* wir muessen uns merken, ob wir etwas gefunden haben in der replog Datei,
	 * falls wir keinen Eintrag haben, aber die Datei spaeter mit ftruncate
	 * loeschen, dann wuerden diese Funktion wieder aufgerufen werden und wir
	 * haetten eine Endlosschleife
	 */
	bool found = false;

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "P_SEM .. ");
	pthread_mutex_lock(&mut_replog);
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "P_SEM");

	entry = notify_entry_alloc();

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK from notify_replog_change_callback");
	if ( ( file = fopen_lock ( FILE_NAME_IRF, "r+", &(l_file) ) ) == NULL ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Could not open %s\n",FILE_NAME_IRF);
	}
	 /*
	  * to be sure the modification is already in the ldap tree
	  *
	signals_block();
	int rc = 1;
	while ( rc != 0 ) {
		rc=usleep(replog_sleep);
	}
	signals_unblock();
	 * we don't need to sleep anymore
	 */



	while ( (fgets(line, MAX_LINE, file)) != NULL ) {

		if ( (strlen(line) == 1 && line[0] == '\n') || first ) {

			if (!first) {
				found = true;
				if ( entry->dn != NULL ) {
					notify_id_get_next(& (entry->notify_id) );

					entry->used=1;

					notifier_cache_add(entry->notify_id.id, entry->dn, entry->command);
					notify_dump_to_files(&notify, entry);

					if ( entry->command == 'r' ) {
							char *tmp;

							entry->command = 'a';

							/* change dn to newrdn */
							tmp=strdup(entry->dn);
							free(entry->dn);
							entry->dn=modrdn(tmp, entry->newrdn, entry->newsuperior);

							notify_id_get_next(& (entry->notify_id) );
							notifier_cache_add(entry->notify_id.id, entry->dn, entry->command);

							notify_dump_to_files(&notify, entry);

					}
				} else {
					univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Failed to read block from replog");
					if ( entry->buf != NULL ) {
						univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "%s", entry->buf);
					}
				}
				notify_entry_free(entry);
			}

			first = false;

			entry = notify_entry_alloc();
		}
		if ( !strncmp(line, "dn: ", strlen("dn: ")) ) {
			entry->dn = malloc (strlen(line)-4);
			memset(entry->dn, 0, strlen(line)-4);
			strncpy(entry->dn,line+4,strlen(line)-5);
		}
		if ( !strncmp(line, "changetype: ", strlen("changetype: ")) ) {

			if (!strncmp(&(line[strlen("changetype: ")]), "modify", strlen("modify"))) {
				entry->command='m';
			}
			else if (!strncmp(&(line[strlen("changetype: ")]), "add", strlen("add"))) {
				entry->command='a';
			}
			else if (!strncmp(&(line[strlen("changetype: ")]), "delete", strlen("delete"))) {
				entry->command='d';
			}
			else if (!strncmp(&(line[strlen("changetype: ")]), "modrdn", strlen("modrdn"))) {
				entry->command='r';
			}
			else {
				entry->command='z';
			}
		}
		if ( !strncmp(line, "newrdn: ", strlen("newrdn: ")) ) {
			entry->newrdn = malloc ( strlen(line)-8);
			memset(entry->newrdn, 0, strlen(line)-8);
			strncpy(entry->newrdn, line+8, strlen(line)-9);
		}
		if ( !strncmp(line, "newsuperior: ", strlen("newsuperior: ")) ) {
			entry->newsuperior = malloc ( strlen(line)-13);
			memset(entry->newsuperior, 0, strlen(line)-13);
			strncpy(entry->newsuperior, line+13, strlen(line)-14);
		}
		if ( !strncmp(line, "deleteoldrdn: 0", strlen("deleteoldrdn: 0")) ) {
			entry->deletemodrdn = 0;
		}
		if ( !strncmp(line, "deleteoldrdn: 1", strlen("deleteoldrdn: 1")) ) {
			entry->deletemodrdn = 1;
		}

		if ( line[0] != '\n') {
			entry->buf=realloc(entry->buf, (strlen(line)+entry->l_buf+1)*sizeof(char));

			strncpy(&(entry->buf[entry->l_buf]), line, strlen(line)+1);

			entry->l_buf+=strlen(line);
		}
	}

	notify_entry_free(entry);
	if ( found ) {
		fseek(file, 0, SEEK_SET);
		ftruncate(fileno(file), 0);
	}

	fclose_lock(FILE_NAME_IRF, &file, &l_file);
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "V_SEM");
	pthread_mutex_unlock(&mut_replog);

	network_client_check_clients ( notify_last_id.id ) ;

	return;
}

void notify_initialize ()
{
	pthread_mutex_unlock(&mut_replog);
	pthread_mutex_unlock(&mut_orf);
	pthread_mutex_unlock(&mut_tf);
	pthread_mutex_unlock(&mut_tf_idx);
	pthread_mutex_unlock(&mut_save);
}

void notify_listener_change_callback(int sig, siginfo_t *si, void *data)
{
	NotifyEntry_t *entry = NULL;

	FILE *file, *l_file;

	struct stat stat_buf;

	char *buf = NULL;

	int nread;


	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "NOTIFY Listener" );
	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "... go");

	entry = notify_entry_alloc();

	univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ALL, "LOCK from notify_listener_change_callback");
	if ( ( file = fopen_lock ( FILE_NAME_LISTENER, "r+", &(l_file) ) ) == NULL ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "Could not open %s\n",FILE_NAME_LISTENER);
	}

	/*
	 * why what are we waiting here
	signals_block();
	int rc = 1;
	while ( rc != 0 ) {
		rc=usleep(replog_sleep);
	}
	signals_unblock();
	 *
	 */


	if( (stat(FILE_NAME_LISTENER, &stat_buf)) != 0 ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "stat error\n");
		goto error;
	}

	if (stat_buf.st_size == 0) {
		goto error;
	}

	if ( (buf = malloc( (stat_buf.st_size + 1 ) * sizeof(char))) == NULL ) {
		univention_debug(UV_DEBUG_TRANSFILE, UV_DEBUG_ERROR, "malloc error\n");
		goto error;
	}

	memset(buf, 0, stat_buf.st_size + 1);

	if ( (nread = fread( buf, sizeof(char), stat_buf.st_size, file)) != 0 ) {
		split_transaction_buffer ( entry, buf, nread);
		notify_dump_to_files(&notify, entry);
		fseek(file, 0, SEEK_SET);
		ftruncate(fileno(file), 0);

		{
			NotifyEntry_t *tmp;
			char *dn_string = NULL;

			tmp = entry;

			while ( tmp != NULL ) {
				notifier_cache_add(tmp->notify_id.id, tmp->dn, tmp->command);
				notify_last_id.id=tmp->notify_id.id;
				dn_string = notify_entry_to_string( *tmp );
				if ( dn_string != NULL ) {
					network_client_all_write(tmp->notify_id.id, dn_string, strlen(dn_string) );
					;
				}
				tmp=tmp->next;
			}
			free(dn_string);
		}
	}

	notify_entry_free(entry);

	free(buf);

error:
	fclose_lock(FILE_NAME_LISTENER, &file, &l_file);

	return;
}
