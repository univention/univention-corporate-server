/*
 * PAM Run As Root
 *  C source for the PAM module runasroot
 *
 * Copyright 2001-2019 Univention GmbH
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

#include <stdarg.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <pwd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <dirent.h>
#include <signal.h>
#include <wait.h>
#include <security/pam_appl.h>

#define PAM_SM_AUTH
#define PAM_SM_SESSION

#include <security/pam_modules.h>
#include <security/_pam_macros.h>

#include <syslog.h>

static unsigned int exp_pass = 0;
static unsigned int save_pass = 0;
static unsigned int run_in_user_context = 0;
static char program[BUFSIZ] = "";
static char saved_pass[BUFSIZ] = "";
static char demouser[BUFSIZ] = "";
static char demouserscript[BUFSIZ];

#define RUNASROOT_QUIET 020

/* some syslogging */
static void _log_err(int err, const char *format, ...)
{
	va_list args;

	va_start(args, format);
	openlog("PAM-runasroot", LOG_CONS|LOG_PID, LOG_AUTH);
	vsyslog(err, format, args);
	va_end(args);
	closelog();
}

static int _pam_parse(int flags, int argc, const char **argv)
{
	int ctrl = 0;

	/* does the application require quiet? */
	if ((flags & PAM_SILENT) == PAM_SILENT)
		ctrl |= RUNASROOT_QUIET;


	/* reset global variables to their default values */
	exp_pass = 0;
	save_pass = 0;
	run_in_user_context = 0;
	program[0] = 0;
	//saved_pass[0] = 0;
	demouser[0] = 0;
	demouserscript[0] = 0;

	/* step through arguments */
	for (; argc-- > 0; ++argv)
	{
		if (!strcmp(*argv, "silent"))
		{
			ctrl |= RUNASROOT_QUIET;
		}
		else if (!strncmp(*argv,"export_pass",11))
			exp_pass = 1;
		else if (!strncmp(*argv,"save_pass",11))
			save_pass = 1;
		else if (!strncmp(*argv,"user",4))
			run_in_user_context = 1;
		else if (!strncmp(*argv,"program=",8))
			strcpy(program,*argv+8);
		else if (!strncmp(*argv,"demouser=",9))
			strncpy(demouser,*argv+9,BUFSIZ);
		else if (!strncmp(*argv,"demouserscript=",15))
			strncpy(demouserscript,*argv+15,BUFSIZ);
		else
		{
			_log_err(LOG_ERR, "unknown option; %s", *argv);
		}
	}

	return ctrl;
}

/* This common function is used to send a message to the applications
   conversion function. Our only use is to ask the application to print
   an informative message that we are creating a home directory */
static int converse(pam_handle_t * pamh, int ctrl, int nargs
		,struct pam_message **message
		,struct pam_response **response)
{
	int retval;
	struct pam_conv *conv;

	retval = pam_get_item(pamh, PAM_CONV, (const void **) &conv);
	if (retval == PAM_SUCCESS)
	{

		retval = conv->conv(nargs, (const struct pam_message **) message
				,response, conv->appdata_ptr);
	}
	else
	{
		_log_err(LOG_ERR, "couldn't obtain coversation function [%s]"
				,pam_strerror(pamh, retval));
	}

	return retval;		/* propagate error status */
}

static int sigchld_blocked = 0;
static sigset_t sigchldblock_mask, sigchldblock_oldmask;

static int sigterm_blocked = 0;
static sigset_t sigtermblock_mask, sigtermblock_oldmask;

	void
sigchld_block_push (void)
{
	sigchld_blocked ++;

	if (sigchld_blocked == 1) {
		/* Set signal mask */
		sigemptyset (&sigchldblock_mask);
		sigaddset (&sigchldblock_mask, SIGCHLD);
		sigprocmask (SIG_BLOCK, &sigchldblock_mask, &sigchldblock_oldmask);
	}
}

	void
sigchld_block_pop (void)
{
	sigchld_blocked --;

	if (sigchld_blocked == 0) {
		/* reset signal mask back */
		sigprocmask (SIG_SETMASK, &sigchldblock_oldmask, NULL);
	}
}

	void
sigterm_block_push (void)
{
	sigterm_blocked ++;

	if (sigterm_blocked == 1) {
		/* Set signal mask */
		sigemptyset (&sigtermblock_mask);
		sigaddset (&sigtermblock_mask, SIGTERM);
		sigaddset (&sigtermblock_mask, SIGINT);
		sigaddset (&sigtermblock_mask, SIGHUP);
		sigprocmask (SIG_BLOCK, &sigtermblock_mask, &sigtermblock_oldmask);
	}
}

	void
sigterm_block_pop (void)
{
	sigterm_blocked --;

	if (sigterm_blocked == 0) {
		/* reset signal mask back */
		sigprocmask (SIG_SETMASK, &sigtermblock_oldmask, NULL);
	}
}


int run_program(pam_handle_t * pamh, int ctrl, char *prog, const char * user, unsigned int pw,
		const char * password, const int run_in_user_context )
{
	pid_t pid;
	int status, i;
	extern char **environ;
	const struct passwd *pwd;


	sigchld_block_push ();
	sigterm_block_push ();
	pid = fork ();
	sigterm_block_pop ();
	sigchld_block_pop ();

	switch (pid) {

		case -1:
			_log_err(LOG_ERR, "can't fork program" );
			return PAM_SYSTEM_ERR;

		case 0:

			pwd = getpwnam(user);

			int uidset = 0;
			if(run_in_user_context) {
				if ( pwd == NULL ) {
					return PAM_USER_UNKNOWN;
				}
				uidset = setgid(pwd->pw_gid);
				if(!uidset) {
					uidset = setuid(pwd->pw_uid);
				}
			}

			if(uidset == 0)  {

				environ[0] = NULL;

				setenv ( "USER", user, 1 );
				setenv ( "LOGNAME", user, 1 );
				setenv ( "USERNAME", user, 1 );
				if ( pwd != NULL ) {
					setenv ( "HOME", pwd->pw_dir, 1 );
					setenv ( "SHELL", pwd->pw_shell, 1 );
				}
				setenv ( "PATH", "/usr/sbin:/usr/bin:/sbin:/bin", 1 );
				if ( pw )
				{

					setenv ( "PASSWD", password, 1 );
					//_log_err(LOG_NOTICE, "password: \"%s\"",password);
				}

				umask (022);
				chdir ( "/" );

				/* do we need to delete the PAM environment here?
				   The following line will end the forked process

				   pam_end ( pamh, PAM_SUCCESS );

*/

				/* close all file handles */
				for (i = 0; i < sysconf (_SC_OPEN_MAX); i++)
					close(i);
				open ("/dev/null", O_RDONLY); /* open stdin - fd 0 */
				open ("/dev/null", O_RDWR); /* open stdout - fd 1 */
				open ("/dev/null", O_RDWR); /* open stderr - fd 2 */
				// sigprocmask (SIG_SETMASK, &sysmask, NULL);

				execl ( prog, NULL );
			}
			else {
				_log_err ( LOG_ERR, "could not set uid/gid");
			}

			_log_err ( LOG_ERR, "could not start program %s", prog );

			exit ( 128 );


		default:
			break;
	}

	sigchld_block_push ();
	waitpid (pid, &status, 0);
	sigchld_block_pop ();

	if ( WEXITSTATUS(status) == 0 ) {
		return PAM_SUCCESS;
	}
	else {
		return PAM_SYSTEM_ERR;
	}

}

void cleanup ( pam_handle_t *pamh, void * data, int error_status )
{
	char *pass_string = (char *)data;
	if ( pass_string == NULL ) return;
	while ( *pass_string ) {
		*pass_string = '\0';
		pass_string++;
	}
	return;
}

/* --- authentication management functions (only) --- */

	PAM_EXTERN
int pam_sm_authenticate(pam_handle_t *pamh, int flags,
		int argc, const char **argv)
{
	int retval, ctrl;
	const char* auth_user;
	char user[BUFSIZ];
	const char * password = NULL;
	char pass_string[BUFSIZ] = "";
	/* const struct passwd *pwd;*/
	char demouser_prefix[BUFSIZ] = "";

	/* Parse the flag values */
	ctrl = _pam_parse(flags, argc, argv);

	/* Determine the user name so we can get the home directory */
	retval = pam_get_item(pamh, PAM_USER, (const void **) &auth_user);

	if (retval != PAM_SUCCESS || auth_user == NULL || *auth_user == '\0')
	{
		_log_err(LOG_NOTICE, "user unknown");
		return PAM_USER_UNKNOWN;
	}

	/* Get the password entry */
	/* we don't need the password entry
	pwd = getpwnam(auth_user);
	if (pwd == NULL)
	{
		return PAM_CRED_INSUFFICIENT;
	}
	*/

	*pass_string = '\0';

	retval = pam_get_item ( pamh, PAM_AUTHTOK, (const void **) &password );
	if ( retval == PAM_SUCCESS && password != NULL && *password != '\0' ) {
		strcpy ( pass_string, password );
	}
	if ( *pass_string == '\0' ) {
		_log_err(LOG_ERR, "can't get password for user %s", auth_user );
	}
	if ( save_pass ) {
		strcpy ( saved_pass, pass_string );
		//_log_err(LOG_NOTICE, "saved password: \"%s\"",saved_pass);
		return PAM_SUCCESS;
	}


	snprintf(demouser_prefix, BUFSIZ, "%s-", demouser);
	/* change to demo user */
	if (strcmp(auth_user, demouser) == 0) {
		char hostname[512];
		if (gethostname(hostname, 512) == -1) {
			_log_err(LOG_NOTICE, "could not determine hostname");
			return PAM_USER_UNKNOWN;
		}
		snprintf(user, BUFSIZ, "%s-%s", auth_user, hostname);
		retval = pam_set_item(pamh, PAM_USER, user);
		if (retval != PAM_SUCCESS) {
			_log_err(LOG_NOTICE, "could not set new username");
			return PAM_USER_UNKNOWN;
		}
		_log_err(LOG_NOTICE, "continuing as demo user");
		if ( demouserscript && *demouserscript != '\0')
			run_program ( pamh, ctrl, demouserscript, user, exp_pass, pass_string, run_in_user_context );
	} else if (strncmp(demouser_prefix, auth_user, strlen(demouser_prefix)) == 0) {
		_log_err(LOG_NOTICE, "rejected specific demouser");
		return PAM_CRED_INSUFFICIENT;
	} else {
		_log_err(LOG_NOTICE, "continuing as normal user");
		strncpy(user, auth_user, BUFSIZ);
	}

	if ( *program != '\0' )
		return run_program ( pamh, ctrl, program, user, exp_pass, pass_string, run_in_user_context );
	else
		return PAM_SUCCESS;

}

PAM_EXTERN
int pam_sm_open_session(pam_handle_t * pamh, int flags, int argc
		,const char **argv)
{
	int retval, ctrl;
	const char *user;
	/* const struct passwd *pwd;*/

	/* Parse the flag values */
	ctrl = _pam_parse(flags, argc, argv);

	/* Determine the user name so we can get the home directory */
	retval = pam_get_item(pamh, PAM_USER, (const void **) &user);

	if (retval != PAM_SUCCESS || user == NULL || *user == '\0')
	{
		_log_err(LOG_NOTICE, "user unknown");
		return PAM_USER_UNKNOWN;
	}

	/* Get the password entry */
	/* we don't need the password entry
	pwd = getpwnam(user);
	if (pwd == NULL)
	{
		return PAM_CRED_INSUFFICIENT;
	}
	*/

	if ( *program != '\0' )
		return run_program ( pamh, ctrl, program, user, exp_pass, saved_pass, run_in_user_context );
	else
		return PAM_SUCCESS;
}

/* Ignore */
PAM_EXTERN
int pam_sm_close_session(pam_handle_t * pamh, int flags, int argc
		,const char **argv)
{
	return PAM_SUCCESS;
}

/* Ignore */
int pam_sm_setcred(pam_handle_t *pamh, int flags, int
		argc, const char **argv) {
	return PAM_SUCCESS;
}

#ifdef PAM_STATIC

/* static module data */
struct pam_module _pam_runasroot_modstruct =
{
	"pam_runasroot",
	pam_sm_authenticate,
	pam_sm_setcred,
	NULL,
	NULL,
	pam_sm_open_session,
	pam_sm_close_session,
	NULL,
};

#endif
