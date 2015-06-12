/*
 * Univention Directory Listener
 *  main.c
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

#define _GNU_SOURCE /* asprintf */

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>
#include <fcntl.h>
#include <dirent.h>
#include <pwd.h>
#include <sys/types.h>

#include <univention/debug.h>
#include <univention/ldap.h>
#ifdef WITH_KRB5
#include <univention/krb5.h>
#endif
#include <univention/config.h>

#include "common.h"
#include "cache.h"
#include "change.h"
#include "handlers.h"
#include "signals.h"
#include "notifier.h"
#include "network.h"
#include "select_server.h"
#include "transfile.h"

int INIT_ONLY = 0;

int backup_notifier = 0;

char **module_dirs = NULL;
int module_dir_count = 0;
long long listener_lock_count = 100;
char pidfile[PATH_MAX];


static char* read_pwd_from_file(char *filename)
{
	FILE *fp;
	char line[1024];
	int len;

	if ((fp = fopen(filename, "r")) == NULL)
		return NULL;
	if (fgets(line, 1024, fp) == NULL) {
		fclose(fp);
		return NULL;
	}
	fclose(fp);

	len = strlen(line);
	if (!len)
		return NULL;
	if (line[len-1] == '\n')
		line[len-1] = '\0';

	return strdup(line);
}


static int daemonize(void)
{
	pid_t pid;
	int null, log;
	int fd;

	fd = open(pidfile, O_WRONLY|O_CREAT|O_EXCL);
	if (fd < 0) {
		if (errno == EEXIST)
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "pidfile %s exists, aborting...%d %s", pidfile, errno, strerror(errno));
		else
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "Can not create pidfile %s: %s, aborting...", pidfile, strerror(errno));
		return 1;
	}

	pid = fork();
	if (pid == -1)
		return 1;
	else if (pid > 0) {
		char buf[15];
		snprintf(buf, 15, "%d", pid);
		write(fd, buf, strlen(buf));
		close(fd);
		_exit(EXIT_SUCCESS);
	}
	close(fd);

	if ((null=open("/dev/null", O_RDWR)) == -1) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "could not open /dev/null");
		return 1;
	}
	dup2(null, STDIN_FILENO);
	dup2(null, STDOUT_FILENO);
	if ((log=open("/var/log/univention/listener.log", O_WRONLY | O_CREAT | O_APPEND)) == -1)
		log=null;
	dup2(log, STDERR_FILENO);

	setsid();
	return 0;
}


void drop_privileges(void)
{
	struct passwd *listener_user;

	if (geteuid() != 0)
		return;

	if ((listener_user = getpwnam("listener")) == NULL) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to get passwd entry for listener");
		exit(1);
	}

	if (setegid(listener_user->pw_gid) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to change to listener gid");
		exit(1);
	}
	if (seteuid(listener_user->pw_uid) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to change to listener uid");
		exit(1);
	}
}


static void usage(void)
{
	fprintf(stderr, "Usage: univention-directory-listener [options]\n");
	fprintf(stderr, "Options:\n");
	fprintf(stderr, "   -d   debugging\n");
	fprintf(stderr, "   -F   run in foreground (intended for process supervision)\n");
	fprintf(stderr, "   -H   LDAP server URI\n");
	fprintf(stderr, "   -h   LDAP server address\n");
	fprintf(stderr, "   -p   LDAP server port\n");
	fprintf(stderr, "   -b   LDAP base dn\n");
	fprintf(stderr, "   -D   LDAP bind dn\n");
	fprintf(stderr, "   -w   LDAP bind password\n");
	fprintf(stderr, "   -y   read LDAP bind (or Kerberos with -K) password from file\n");
	fprintf(stderr, "   -x   LDAP simple bind\n");
	fprintf(stderr, "   -Z   LDAP start TLS request (-ZZ to require successful response)\n");
	fprintf(stderr, "   -Y   SASL mechanism\n");
	fprintf(stderr, "   -U   SASL/Kerberos username\n");
	fprintf(stderr, "   -R   SASL/Kerberos realm\n");
	fprintf(stderr, "   -K   acquire Kerberos ticket granting ticket (like kinit)\n");
	fprintf(stderr, "   -m   Listener module path (may be specified multiple times)\n");
	fprintf(stderr, "   -B   Only use dc backup notifier\n");
	fprintf(stderr, "   -c   Listener cache path\n");
	fprintf(stderr, "   -l   LDAP schema and transaction path\n");
	fprintf(stderr, "   -g   start from scratch (remove cache)\n");
	fprintf(stderr, "   -i   initialize handlers only\n");
	fprintf(stderr, "   -o   write transaction file\n");
}


static void convert_cookie(void)
{
#ifndef WITH_DB42
	char *f;
	struct stat stbuf;

	asprintf(&f, "%s/notifier_id", cache_dir);
	if (stat(f, &stbuf) != 0) {
		free(f);
		asprintf(&f, "%s/cookie", cache_dir);
		FILE *fp = fopen(f, "r");
		if (fp != NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "converting cookie file");
			char buf[1024];
			int  i;
			fgets(buf, 1024, fp);
			fgets(buf, 1024, fp);
			i = atoi(buf);
			if (i > 0)
				cache_set_int("notifier_id", i);
			fclose(fp);
		}
	}
	free(f);
#else
	char *filename;
	FILE *fp;
	CacheMasterEntry master_entry;
	int rv;

	if ((rv=cache_get_master_entry(&master_entry)) == 0)
		return; /* nothing to be done */
	else if (rv != DB_NOTFOUND)
		exit(1); /* XXX */

	asprintf(&filename, "%s/notifier_id", cache_dir);
	if ((fp = fopen(filename, "r")) != NULL) {
		fscanf(fp, "%ld", &master_entry.id);
		fclose(fp);
	} else
		master_entry.id = 0;
	free(filename);

	if (master_entry.id == 0) {
		asprintf(&filename, "%s/cookie", cache_dir);
		if ((fp = fopen(filename, "r")) != NULL) {
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "converting cookie file");
			char buf[1024];
			fgets(buf, 1024, fp);
			fgets(buf, 1024, fp);
			master_entry.id = atoi(buf);
			fclose(fp);
		}
		free(filename);
	}

	if (asprintf(&filename, "%s/schema/id/id", ldap_dir) < 0) abort();
	if ((fp = fopen(filename, "r")) != NULL) {
		fscanf(fp, "%ld", &master_entry.schema_id);
		fclose(fp);
	} else
		master_entry.schema_id = 0;
	free(filename);

	if ((rv=cache_update_master_entry(&master_entry, NULL)) != 0)
		exit(1); /* XXX */
#endif
}


static void purge_cache(const char *cache_dir)
{
	DIR* dir;
	struct dirent *dirent;
	char *dirname;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "purging cache");
	if ((dir = opendir(cache_dir)) != NULL) {
		while ((dirent = readdir(dir))) {
			char path[PATH_MAX];
			snprintf(path, PATH_MAX, "%s/%s", cache_dir, dirent->d_name);
			unlink(path);
		}
		closedir(dir);
	}
	handlers_clean_all();

	asprintf(&dirname, "%s/handlers", cache_dir);
	if ((dir = opendir(dirname)) != NULL) {
		while ((dirent = readdir(dir))) {
			char path[PATH_MAX];
			snprintf(path, PATH_MAX, "%s/%s", dirname, dirent->d_name);
			unlink(path);
		}
		closedir(dir);
	}
	free(dirname);
}


static void prepare_cache(const char *cache_dir)
{
	char *dirname;
	struct stat stbuf;

	asprintf(&dirname, "%s/handlers", cache_dir);
	if (stat(dirname, &stbuf) != 0) {
		mkdir(dirname, 0700);
	}
	free(dirname);
}


/* Open LDAP and Notifier connection.
 * @return 0 on success, 1 on error.
 */
static int do_connection(univention_ldap_parameters_t *lp)
{
	LDAPMessage *res;
	int rc;
	struct timeval timeout = {
		.tv_sec = 10,
		.tv_usec = 0,
	};

	if (univention_ldap_open(lp) != LDAP_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "can not connect to LDAP server %s:%d", lp->host, lp->port);
		goto fail;
	}
	if (notifier_client_new(NULL, lp->host, 1) != 0)
		goto fail;

	/* check if we are connected to an OpenLDAP */
	rc = ldap_search_ext_s(lp->ld, lp->base, LDAP_SCOPE_BASE, "objectClass=univentionBase",
			NULL, 0, NULL, NULL, &timeout, 0, &res);
	ldap_msgfree(res);
	switch (rc) {
		case LDAP_SUCCESS:
			return 0;
		case LDAP_NO_SUCH_OBJECT:
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR,
					"Failed to find \"(objectClass=univentionBase)\" on LDAP server %s:%d", lp->host, lp->port);
			break;
		default:
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR,
					"Failed to search for \"(objectClass=univentionBase)\" on LDAP server %s:%d with message %s", lp->host, lp->port, ldap_err2string(rc));
			break;
	}
fail:
	notifier_client_destroy(NULL);
	if (lp->ld)
		ldap_unbind_ext(lp->ld, NULL, NULL);
	lp->ld = NULL;
	return 1;
}


int main(int argc, char* argv[])
{
	univention_ldap_parameters_t	*lp;
	univention_ldap_parameters_t	*lp_local;
	char *server_role;
#ifdef WITH_KRB5
	univention_krb5_parameters_t	*kp = NULL;
	bool do_kinit = false;
#else
	void				*kp = NULL ;
#endif
	int debugging = 0;
	bool from_scratch = false;
	bool foreground = false;
	bool initialize_only = false;
	bool write_transaction_file = false;
	int				 rv;
	NotifierID			 id = -1;
#ifndef WITH_DB42
	NotifierID			 old_id = -1;
#else
	CacheMasterEntry		 master_entry;
#endif
	struct stat			 stbuf;
	char *f = NULL;

	univention_debug_init("stderr", 1, 1);

	if ((lp = univention_ldap_new()) == NULL)
		exit(1);
	lp->authmethod = LDAP_AUTH_SASL;

	if ((lp_local = univention_ldap_new()) == NULL)
		exit(1);

#if WITH_KRB5
	if ((kp=univention_krb5_new()) == NULL)
		exit(1);
#endif

	/* parse arguments */
	for (;;) {
		int c;

		c = getopt(argc, argv, "d:FH:h:p:b:D:w:y:xZY:U:R:Km:Bc:giol:");
		if (c < 0)
			break;
		switch (c) {
		case 'd':
			debugging=atoi(optarg);
			break;
		case 'F':
			foreground = true;
			break;
		case 'H':
			lp->uri=strdup(optarg);
			break;
		case 'h':
			lp->host=strdup(optarg);
			break;
		case 'p':
			lp->port=atoi(optarg);
			break;
		case 'b':
			lp->base=strdup(optarg);
			break;
		case 'm':
			if ((module_dirs = realloc(module_dirs, (module_dir_count+2)*sizeof(char*))) == NULL) {
				return 1;
			}
			module_dirs[module_dir_count] = strdup(optarg);
			module_dirs[module_dir_count+1] = NULL;
			module_dir_count++;
			break;
		case 'c':
			cache_dir=strdup(optarg);
			break;
		case 'l':
			ldap_dir = strdup(optarg);
			if (asprintf(&transaction_file, "%s/listener/listener", ldap_dir) < 0) abort();
			break;
		case 'D':
			lp->binddn=strdup(optarg);
			break;
		case 'w':
			lp->bindpw=strdup(optarg);
#ifdef WITH_KRB5
			kp->password=strdup(optarg);
#endif
			/* remove password from process list */
			memset(optarg, 'X', strlen(optarg));
			break;
		case 'Z':
			lp->start_tls++;
			break;
		case 'x':
			lp->authmethod = LDAP_AUTH_SIMPLE;
			break;
		case 'y':
			lp->bindpw=read_pwd_from_file(optarg);
#ifdef WITH_KRB5
			kp->password=strdup(lp->bindpw);
#endif
			break;
		case 'Y':
			lp->sasl_mech=strdup(optarg);
			break;
		case 'U':
			asprintf(&lp->sasl_authzid, "u:%s", optarg);
			/* kp->username=strdup(optarg); */
		case 'R':
			lp->sasl_realm=strdup(optarg);
#ifdef WITH_KRB5
			kp->realm=strdup(optarg);
#endif
			break;
#ifdef WITH_KRB5
		case 'K':
			do_kinit = true;
			break;
#endif
		case 'g':
			from_scratch = true;
			break;
		case 'i':
			initialize_only = true;
			from_scratch = true;
			foreground = true;
			break;
		case 'o':
			write_transaction_file = true;
			break;
		case 'B':
			backup_notifier = 1;
			break;
		default:
			usage();
			exit(1);
		}
	}

	if (asprintf(&f, "%s/bad_cache", cache_dir) < 0) abort();
	if (stat(f, &stbuf) == 0) {
		exit(3);
	}
	free(f);

	univention_debug_set_level(UV_DEBUG_LISTENER, debugging);
	univention_debug_set_level(UV_DEBUG_LDAP, debugging);
	univention_debug_set_level(UV_DEBUG_KERBEROS, debugging);

	snprintf(pidfile, PATH_MAX, "%s/pid", cache_dir);
	signals_init();

	if (!foreground && daemonize() != 0)
		exit(EXIT_FAILURE);

	drop_privileges();

	if (from_scratch)
		purge_cache(cache_dir);

	prepare_cache(cache_dir);

	/* choose server to connect to */
	if (lp->host == NULL && lp->uri == NULL) {
		select_server(lp);
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
				"no server given, choosing one by myself (%s)",
				lp->host);
	}

#ifdef WITH_KRB5
	if (!do_kinit)
		kp = NULL;
	if (kp != NULL && univention_krb5_init(kp) != 0) {
		univention_debug(UV_DEBUG_KERBEROS, UV_DEBUG_ERROR, "kinit failed");
		exit(1);
	}
#endif

	while (do_connection(lp) != 0) {
		if (suspend_connect()) {
			if (initialize_only) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR,
					"can not connect any server, exit");
				exit(1);
			}
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN,
				"can not connect any server, retrying in 30 seconds");
			sleep(30);
		}

		select_server(lp);
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "chosen server: %s:%d", lp->host, lp->port);
	}

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO, "connection okay to host %s:%d", lp->host, lp->port);

	/* connect to local LDAP server */
	server_role = univention_config_get_string("server/role");
	if ( server_role != NULL ) {
		if (!strcmp(server_role, "domaincontroller_backup") || !strcmp(server_role, "domaincontroller_slave")) {	// if not master
			lp_local->host = strdup("localhost"); // or fqdn e.g. from univention_config_get_string("ldap/server/name");
			lp_local->base = strdup(lp->base);
			lp_local->binddn = strdup(lp->binddn);
			lp_local->bindpw = strdup(lp->bindpw);
		}
		free(server_role);
	}

	/* XXX: we shouldn't block all signals for so long */
	signals_block();
	cache_init();
	handlers_init();

	/* pass data to handlers */
	if (lp->base != NULL)
		handlers_set_data_all("basedn", lp->base);
	if (lp->binddn != NULL)
		handlers_set_data_all("binddn", lp->binddn);
	if (lp->bindpw != NULL)
		handlers_set_data_all("bindpw", lp->bindpw);
	if (lp->host != NULL)
		handlers_set_data_all("ldapserver", lp->host);

	convert_cookie();

	if (notifier_get_id_s(NULL, &id) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "failed to receive current ID");
		return 1;
	}

	if (initialize_only) {
		INIT_ONLY=1;
	}

	/* update schema */
	if ((rv=change_update_schema(lp)) != LDAP_SUCCESS)
		return rv;

	/* do initial import of entries */
	if ((rv=change_new_modules(lp)) != LDAP_SUCCESS) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "change_new_modules: %s", ldap_err2string(rv));
		return rv;
	}
	signals_unblock();

	/* if no ID is set, assume the database has just been initialized */
#ifdef WITH_DB42
	if ((rv=cache_get_master_entry(&master_entry)) == DB_NOTFOUND) {
		master_entry.id = id;
		if ((rv=cache_update_master_entry(&master_entry, NULL)) != 0)
			exit(1);
	} else if (rv != 0)
		exit(1);

#else
	cache_get_int("notifier_id", &old_id, -1);
	if ((long)old_id == -1) {
		cache_set_int("notifier_id", id);
	}
#endif

	if (!initialize_only) {
		rv = notifier_listen(lp, kp, write_transaction_file, lp_local);
	}

	if (rv != 0)
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "listener: %d", rv);

	univention_ldap_close(lp);
	univention_ldap_close(lp_local);

	exit_handler(0);
}
