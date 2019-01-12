/*
 * Univention Directory Listener
 *  main.c
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


static char *read_pwd_from_file(char *filename) {
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
	if (line[len - 1] == '\n')
		line[len - 1] = '\0';

	return strdup(line);
}


static void daemonize(int lock_fd) {
	pid_t pid;
	int null, log;
	int fd, rv;

	rv = snprintf(pidfile, PATH_MAX, "%s/pid", cache_dir);
	if (rv < 0 || rv >= PATH_MAX)
		abort();

	fd = open(pidfile, O_WRONLY | O_CREAT | O_EXCL, 0644);
	if (fd < 0) {
		if (errno == EEXIST)
			LOG(ERROR, "pidfile %s exists, aborting...%d %s", pidfile, errno, strerror(errno));
		else
			LOG(ERROR, "Can not create pidfile %s: %s, aborting...", pidfile, strerror(errno));
		exit(EXIT_FAILURE);
	}

	// fork off the parent process
	pid = fork();

	// An error occurred
	if (pid < 0)
		exit(EXIT_FAILURE);

	// Success: Let the parent terminate
	if (pid > 0)
		exit(EXIT_SUCCESS);

	// On success: The child process becomes session leader
	if (setsid() < 0)
		exit(EXIT_FAILURE);

	// Catch, ignore and handle signals
	signals_init();

	// Fork off for the second time
	pid = fork();

	// An error occurred
	if (pid < 0)
		exit(EXIT_FAILURE);

	// Success: Let the parent terminate
	if (pid > 0)
		exit(EXIT_SUCCESS);

	// write pid file
	{
		char buf[15];

		pid = getpid();
		rv = snprintf(buf, sizeof buf, "%d", pid);
		if (rv < 0 || rv >= sizeof buf)
			abort();
		rv = write(fd, buf, rv);
		if (rv)
			LOG(WARN, "Failed to write %s: %s", pidfile, strerror(errno));
	}
	rv = close(fd);
	if (rv)
		LOG(WARN, "Failed to close %s: %s", pidfile, strerror(errno));

	// Set new file permissions
	umask(0);

	// Change the working directory to the root directory
	rv = chdir("/");
	if (rv)
		LOG(WARN, "Failed to change directory: %s", strerror(errno));

	if ((null = open("/dev/null", O_RDWR)) == -1) {
		LOG(ERROR, "could not open /dev/null: %s", strerror(errno));
		exit(EXIT_FAILURE);
	}
	dup2(null, STDIN_FILENO);
	dup2(null, STDOUT_FILENO);
	if ((log = open("/var/log/univention/listener.log", O_WRONLY | O_CREAT | O_APPEND, 0640)) >= 0) {
		dup2(log, STDERR_FILENO);
		rv = close(log);
		if (rv)
			LOG(WARN, "Failed to close /var/log/univention/listener.log: %s", strerror(errno));
	} else {
		dup2(null, STDERR_FILENO);
	}
	rv = close(null);
	if (rv)
		LOG(WARN, "Failed to close /dev/null: %s", strerror(errno));

	// Close all open file descriptors
	for (fd = sysconf(_SC_OPEN_MAX); fd > STDERR_FILENO; fd--)
		if (fd != lock_fd)
			close(fd);
}


void drop_privileges(void) {
	struct passwd *listener_user;

	if (geteuid() != 0)
		return;

	if ((listener_user = getpwnam("listener")) == NULL) {
		LOG(ERROR, "failed to get passwd entry for listener");
		exit(1);
	}

	if (setegid(listener_user->pw_gid) != 0) {
		LOG(ERROR, "failed to change to listener gid");
		exit(1);
	}
	if (seteuid(listener_user->pw_uid) != 0) {
		LOG(ERROR, "failed to change to listener uid");
		exit(1);
	}
}


/*
 * Print usage information.
 */
static void usage(void) {
	fprintf(stderr, "Usage: univention-directory-listener [options]\n");
	fprintf(stderr, "Options:\n");
	fprintf(stderr, "   -d <level>  debugging\n");
	fprintf(stderr, "   -F          run in foreground (intended for process supervision)\n");
	fprintf(stderr, "   -H <uri>    LDAP server URI\n");
	fprintf(stderr, "   -h <addr>   LDAP server address\n");
	fprintf(stderr, "   -p <port>   LDAP server port\n");
	fprintf(stderr, "   -b <base>   LDAP base dn\n");
	fprintf(stderr, "   -D <dn>     LDAP bind dn\n");
	fprintf(stderr, "   -w <pwd>    LDAP bind password\n");
	fprintf(stderr, "   -y <file>   read LDAP bind password from file\n");
	fprintf(stderr, "   -x          LDAP simple bind\n");
	fprintf(stderr, "   -Z          LDAP start TLS request (-ZZ to require successful response)\n");
	fprintf(stderr, "   -Y <mech>   SASL mechanism\n");
	fprintf(stderr, "   -U <name>   SASL username\n");
	fprintf(stderr, "   -R <realm>  SASL realm\n");
	fprintf(stderr, "   -m <path>   Listener module path (may be specified multiple times)\n");
	fprintf(stderr, "   -B          Only use dc backup notifier\n");
	fprintf(stderr, "   -c <path>   Listener cache path\n");
	fprintf(stderr, "   -l <path>   LDAP schema and transaction path\n");
	fprintf(stderr, "   -g          start from scratch (remove cache)\n");
	fprintf(stderr, "   -i          initialize handlers only\n");
	fprintf(stderr, "   -o          write transaction file\n");
	fprintf(stderr, "   -P          initialize handlers only, but not from scratch\n");
}


static void purge_cache(const char *cache_dir) {
	DIR *dir;
	struct dirent *dirent;
	char dirname[PATH_MAX];
	int rv;

	LOG(INFO, "purging cache");
	if ((dir = opendir(cache_dir)) != NULL) {
		while ((dirent = readdir(dir))) {
			char path[PATH_MAX];
			rv = snprintf(path, PATH_MAX, "%s/%s", cache_dir, dirent->d_name);
			if (rv < 0 || rv >= PATH_MAX)
				abort();
			unlink(path);
		}
		closedir(dir);
	}
	handlers_clean_all();

	rv = snprintf(dirname, PATH_MAX, "%s/handlers", cache_dir);
	if (rv < 0 || rv >= PATH_MAX)
		abort();
	if ((dir = opendir(dirname)) != NULL) {
		while ((dirent = readdir(dir))) {
			char path[PATH_MAX];
			snprintf(path, PATH_MAX, "%s/%s", dirname, dirent->d_name);
			unlink(path);
		}
		closedir(dir);
	}

	rv = snprintf(dirname, PATH_MAX, "%s/cache", cache_dir);
	if (rv < 0 || rv >= PATH_MAX)
		abort();
	if ((dir = opendir(dirname)) != NULL) {
		while ((dirent = readdir(dir))) {
			char path[PATH_MAX];
			snprintf(path, PATH_MAX, "%s/%s", dirname, dirent->d_name);
			unlink(path);
		}
		closedir(dir);
	}
}


static void prepare_cache(const char *cache_dir) {
	char dirname[PATH_MAX];
	struct stat stbuf;
	int rv;

	rv = snprintf(dirname, PATH_MAX, "%s/handlers", cache_dir);
	if (rv < 0 || rv >= PATH_MAX)
		abort();
	if (stat(dirname, &stbuf) != 0) {
		mkdir(dirname, 0700);
	}

	rv = snprintf(dirname, PATH_MAX, "%s/cache", cache_dir);
	if (rv < 0 || rv >= PATH_MAX)
		abort();
	if (stat(dirname, &stbuf) != 0) {
		mkdir(dirname, 0700);
	}
}


/* Open LDAP and Notifier connection.
 * @return 0 on success, 1 on error.
 */
static int do_connection(univention_ldap_parameters_t *lp) {
	LDAPMessage *res;
	int rc;
	char **_attrs = NULL;
	int attrsonly0 = 0;
	LDAPControl **serverctrls = NULL;
	LDAPControl **clientctrls = NULL;
	struct timeval timeout = {
	    .tv_sec = 5 * 60, .tv_usec = 0,
	};
	int sizelimit0 = 0;

	if (univention_ldap_open(lp) != LDAP_SUCCESS) {
		LOG(WARN, "can not connect to LDAP server %s:%d", lp->uri ? lp->uri : lp->host ? lp->host : "NULL", lp->port);
		goto fail;
	}
	if (notifier_client_new(NULL, lp->host, 1) != 0)
		goto fail;

	/* check if we are connected to an OpenLDAP */
	rc = ldap_search_ext_s(lp->ld, lp->base, LDAP_SCOPE_BASE, "objectClass=univentionBase", _attrs, attrsonly0, serverctrls, clientctrls, &timeout, sizelimit0, &res);
	ldap_msgfree(res);
	switch (rc) {
	case LDAP_SUCCESS:
		return 0;
	case LDAP_NO_SUCH_OBJECT:
		LOG(ERROR, "Failed to find \"(objectClass=univentionBase)\" on LDAP server %s:%d", lp->uri ? lp->uri : lp->host ? lp->host : "NULL", lp->port);
		break;
	default:
		LOG(ERROR, "Failed to search for \"(objectClass=univentionBase)\" on LDAP server %s:%d with message %s", lp->uri ? lp->uri : lp->host ? lp->host : "NULL", lp->port, ldap_err2string(rc));
		break;
	}
fail:
	notifier_client_destroy(NULL);
	if (lp->ld)
		ldap_unbind_ext(lp->ld, NULL, NULL);
	lp->ld = NULL;
	return 1;
}


int main(int argc, char *argv[]) {
	univention_ldap_parameters_t *lp;
	univention_ldap_parameters_t *lp_local;
	char *server_role;
	int debugging = 0;
	bool from_scratch = false;
	bool foreground = false;
	bool initialize_only = false;
	bool write_transaction_file = false;
	int rv;
	NotifierID id = -1;
	struct stat stbuf;
	char cache_mdb_dir[PATH_MAX];

	univention_debug_init("stderr", 1, 1);

	{
		struct timeval timeout = {
		    .tv_sec = 5 * 60, .tv_usec = 0,
		};
		int ret;
		ret = ldap_set_option(NULL, LDAP_OPT_NETWORK_TIMEOUT, &timeout);
		if (ret != LDAP_OPT_SUCCESS)
			fprintf(stderr, "Failed to set LDAP connection timeout: %s\n", ldap_err2string(ret));
		ret = ldap_set_option(NULL, LDAP_OPT_TIMEOUT, &timeout);
		if (ret != LDAP_OPT_SUCCESS)
			fprintf(stderr, "Failed to set LDAP synchronous API timeout: %s\n", ldap_err2string(ret));

		const int idle = 60;
		ret = ldap_set_option(NULL, LDAP_OPT_X_KEEPALIVE_IDLE, &idle);
		if (ret != LDAP_OPT_SUCCESS)
			fprintf(stderr, "Failed to set TCP KA idle: %s\n", ldap_err2string(ret));
		const int probes = 12;
		ret = ldap_set_option(NULL, LDAP_OPT_X_KEEPALIVE_PROBES, &probes);
		if (ret != LDAP_OPT_SUCCESS)
			fprintf(stderr, "Failed to set TCP KA probes: %s\n", ldap_err2string(ret));
		const int interval = 5;
		ret = ldap_set_option(NULL, LDAP_OPT_X_KEEPALIVE_INTERVAL, &interval);
		if (ret != LDAP_OPT_SUCCESS)
			fprintf(stderr, "Failed to set TCP KA interval: %s\n", ldap_err2string(ret));
	}

	if ((lp = univention_ldap_new()) == NULL)
		exit(1);
	lp->authmethod = LDAP_AUTH_SASL;

	if ((lp_local = univention_ldap_new()) == NULL)
		exit(1);

	/* parse arguments */
	for (;;) {
		int c;

		c = getopt(argc, argv, "d:FH:h:p:b:D:w:y:xZY:U:R:Km:Bc:giol:P");
		if (c < 0)
			break;
		switch (c) {
		case 'd':
			debugging = atoi(optarg);
			break;
		case 'F':
			foreground = true;
			break;
		case 'H':
			lp->uri = strdup(optarg);
			break;
		case 'h':
			lp->host = strdup(optarg);
			break;
		case 'p':
			lp->port = atoi(optarg);
			break;
		case 'b':
			lp->base = strdup(optarg);
			break;
		case 'm':
			if ((module_dirs = realloc(module_dirs, (module_dir_count + 2) * sizeof(char *))) == NULL) {
				return 1;
			}
			module_dirs[module_dir_count] = strdup(optarg);
			module_dirs[module_dir_count + 1] = NULL;
			module_dir_count++;
			break;
		case 'c':
			cache_dir = strdup(optarg);
			break;
		case 'l':
			ldap_dir = strdup(optarg);
			if (asprintf(&transaction_file, "%s/listener/listener", ldap_dir) < 0)
				abort();
			break;
		case 'D':
			lp->binddn = strdup(optarg);
			break;
		case 'w':
			lp->bindpw = strdup(optarg);
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
			lp->bindpw = read_pwd_from_file(optarg);
			break;
		case 'Y':
			lp->sasl_mech = strdup(optarg);
			break;
		case 'U':
			if (asprintf(&lp->sasl_authzid, "u:%s", optarg) < 0)
				abort();
			break;
		case 'R':
			lp->sasl_realm = strdup(optarg);
			break;
		case 'g':
			from_scratch = true;
			break;
		case 'i':
			from_scratch = true;
			/* fallthrough */
		case 'P':
			initialize_only = true;
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

	univention_debug_set_level(UV_DEBUG_LISTENER, debugging);
	univention_debug_set_level(UV_DEBUG_LDAP, debugging);

	{
		char filename[PATH_MAX];
		rv = snprintf(filename, PATH_MAX, "%s/bad_cache", cache_dir);
		if (rv < 0 || rv >= PATH_MAX)
			abort();
		if (stat(filename, &stbuf) == 0) {
			LOG(ERROR, "Corrupt cache");
			exit(3);
		}
	}

	rv = cache_lock();

	if (foreground)
		signals_init();
	else
		daemonize(rv);

	drop_privileges();

	if (from_scratch)
		purge_cache(cache_dir);

	prepare_cache(cache_dir);

	/* choose server to connect to */
	if (lp->host == NULL && lp->uri == NULL) {
		select_server(lp);
	}

	while (do_connection(lp) != 0) {
			if (initialize_only) {
				LOG(ERROR, "can not connect any server, exit");
				exit(1);
			}
			LOG(WARN, "can not connect any server, retrying in 30 seconds");
			sleep(30);

		select_server(lp);
	}

	LOG(INFO, "connection okay to host %s:%d", lp->host, lp->port);

	/* connect to local LDAP server */
	server_role = univention_config_get_string("server/role");
	if (server_role != NULL) {
		if (!strcmp(server_role, "domaincontroller_backup") || !strcmp(server_role, "domaincontroller_slave")) {  // if not master
			lp_local->host = strdup("localhost");                                                             // or fqdn e.g. from univention_config_get_string("ldap/server/name");
			lp_local->base = strdup(lp->base);
			lp_local->binddn = strdup(lp->binddn);
			lp_local->bindpw = strdup(lp->bindpw);
		}
		free(server_role);
	}

	/* XXX: we shouldn't block all signals for so long */
	signals_block();

	cache_entry_init();
	rv = snprintf(cache_mdb_dir, PATH_MAX, "%s/cache", cache_dir);
	if (rv < 0 || rv >= PATH_MAX)
		abort();
	if (cache_init(cache_mdb_dir, 0) != 0)
		exit(1);

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

	if (notifier_get_id_s(NULL, &id) != 0) {
		LOG(ERROR, "failed to receive current ID");
		return 1;
	}

	if (initialize_only) {
		INIT_ONLY = 1;
	}

	/* if no ID is set, assume the database has just been initialized */
	rv = cache_get_master_entry(&cache_master_entry);
	if (rv == MDB_NOTFOUND) {
		cache_get_int("notifier_id", &cache_master_entry.id, -1);
		if (cache_master_entry.id == -1) {
			rv = notifier_get_id_s(NULL, &cache_master_entry.id);
			if (rv != 0) {
				LOG(ERROR, "failed to receive current ID");
				return 1;
			}
		}

		cache_get_schema_id(&cache_master_entry.schema_id, 0);

		rv = cache_update_master_entry(&cache_master_entry);
	}
	if (rv != 0)
		return rv;
	/* Legacy file for Nagios et al. */
	if (cache_set_int("notifier_id", cache_master_entry.id))
		LOG(WARN, "failed to write notifier ID");

	/* update schema */
	if ((rv = change_update_schema(lp)) != LDAP_SUCCESS)
		return rv;

	/* do initial import of entries */
	if ((rv = change_new_modules(lp)) != LDAP_SUCCESS) {
		LOG(ERROR, "change_new_modules=%s", ldap_err2string(rv));
		return rv;
	}
	signals_unblock();

	if (!initialize_only) {
		rv = notifier_listen(lp, write_transaction_file, lp_local);
	}

	if (rv != 0)
		LOG(ERROR, "notifier_listen=%d", rv);

	univention_ldap_close(lp);
	univention_ldap_close(lp_local);

	exit_handler(0);
}
