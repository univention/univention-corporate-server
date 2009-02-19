/*
 * Univention Directory Listener
 *  main.c
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

#define _GNU_SOURCE /* asprintf */

#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <stdlib.h>
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

int INIT_ONLY=0;

char *current_server_list = NULL;
struct server_list *server_list = NULL;
int server_list_entries = 0;
int backup_notifier=0;

char *cache_dir = "/var/lib/univention-directory-listener";
char **module_dirs = NULL;
int module_dir_count = 0;
char pidfile[PATH_MAX];
extern maxnbackups;

static char* read_pwd_from_file(char *filename)
{
	FILE *fp;
	char line[1024];
	int len;

	if ((fp = fopen(filename, "r")) == NULL)
		return NULL;
	if (fgets(line, 1024, fp) == NULL)
		return NULL;

	len = strlen(line);
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
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "pidfile %s exists, aborting...", pidfile);
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

	if ((fp = fopen("/var/lib/univention-ldap/schema/id/id", "r")) != NULL) {
		fscanf(fp, "%ld", &master_entry.schema_id);
		fclose(fp);
	} else
		master_entry.schema_id = 0;
	free(filename);

	if ((rv=cache_update_master_entry(&master_entry, NULL)) != 0)
		exit(1); /* XXX */
#endif
}

void purge_cache(const char *cache_dir)
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

void prepare_cache(const char *cache_dir)
{
	char *dirname;
	struct stat stbuf;
	
	asprintf(&dirname, "%s/handlers", cache_dir);
	if (stat(dirname, &stbuf) != 0) {
		mkdir(dirname, 0700);
	}
	free(dirname);
}


int main(int argc, char* argv[])
{
	univention_ldap_parameters_t	*lp;
#ifdef WITH_KRB5
	univention_krb5_parameters_t	*kp;
	int				 do_kinit = 0;
#else
	void				*kp;
#endif
	int 				 debugging = 0,
					 from_scratch = 0,
					 foreground = 0,
					 initialize_only = 0,
					 write_transaction_file = 0;
	int				 rv;
	NotifierID			 id = -1;
#ifndef WITH_DB42
	NotifierID			 old_id = -1;
#else
	CacheMasterEntry		 master_entry;
#endif
	struct stat			 stbuf;

	if (stat("/var/lib/univention-directory-listener/bad_cache", &stbuf) == 0) {
		exit(3);
	}

	univention_debug_init("stderr", 1, 1);

	if ((lp=univention_ldap_new()) == NULL)
		exit(1);
	lp->authmethod = LDAP_AUTH_SASL;

#if WITH_KRB5
	if ((kp=univention_krb5_new()) == NULL)
		exit(1);
#endif

	/* parse arguments */
	for (;;) {
		int c;

		c = getopt(argc, argv, "d:FH:h:b:p:D:w:m:c:Zxy:Y:U:R:KgiBof:");
		if (c < 0)
			break;
		switch (c) {
		case 'd':
			debugging=atoi(optarg);
			break;
		case 'F':
			foreground = 1;
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
			do_kinit = 1;
			break;
#endif
		case 'g':
			from_scratch = 1;
			break;
		case 'i':
			initialize_only = 1;
			from_scratch = 1;
			foreground = 1;
			break;
		case 'o':
			write_transaction_file = 1;
			break;
		case 'B':
			backup_notifier = 1;
			break;
		default:
			usage();
			exit(1);
		}
	}

	univention_debug_set_level(UV_DEBUG_LISTENER, debugging);
	univention_debug_set_level(UV_DEBUG_LDAP, debugging);
	univention_debug_set_level(UV_DEBUG_KERBEROS, debugging);

	snprintf(pidfile, PATH_MAX, "%s/pid", cache_dir);
	signals_init();

	if (foreground == 0 && daemonize() != 0)
		exit(EXIT_FAILURE);

	drop_privileges();

	if (from_scratch)
		purge_cache(cache_dir);

	prepare_cache(cache_dir);

	server_list = malloc(sizeof(struct server_list[maxnbackups+1]));

	/* choose server to connect to */
	if (lp->host == 0) {
		free(lp->host);
		lp->ld = NULL;
		lp->host=select_server();
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_INFO,
				"no server given, choose one by myself (%s)",
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

	while (univention_ldap_open(lp) != 0 || notifier_client_new(NULL, lp->host, 1) != 0) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "can not connect to ldap server (%s)", lp->host);
		free(lp->host);
		if ( lp->ld != NULL ) {
			ldap_unbind(lp->ld);
		}
		lp->ld = NULL;

		if (suspend_connect(server_list, server_list_entries)) {
			if ( initialize_only ) {
				univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR,
					"can not connect to any ldap server, exit");
				exit(1);
			}
			univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN,
				"can not connect to any ldap server, retrying in 30 seconds");
			sleep(30);
		}

		lp->host=select_server();
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "choose as server: %s", lp->host);
	}


	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "connection okay to host %s", lp->host);

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
		rv=notifier_listen(lp, kp, write_transaction_file);
	}

	if (rv != 0)
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ERROR, "listener: %d", rv);

	exit_handler(2);
	exit(rv);
	return rv;
}
