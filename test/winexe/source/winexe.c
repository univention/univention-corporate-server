/*
  Copyright (C) Andrzej Hajda 2009-2013
  Contact: andrzej.hajda@wp.pl
  License: GNU General Public License version 3
*/

#include <sys/epoll.h>
#include <sys/fcntl.h>
#include <sys/unistd.h>
#include <sys/termios.h>
#include <signal.h>
#include <string.h>
#include <stdlib.h>
#include <tevent.h>
#include <popt.h>
#include <util/memory.h>
#include <credentials.h>
#include <util/time.h>
#include <util/debug.h>
#include <smb_cliraw.h>
#include <smb_cli.h>
#include <dcerpc.h>
#include <iconv.h>
#include <errno.h>
#include <credentials.h>

#define TEVENT_CONTEXT_INIT tevent_context_init

#include "async.h"
#include "svcinstall.h"
#include "winexesvc.h"

#define SERVICE_FILENAME SERVICE_NAME ".exe"

static const char version_message_fmt[] = "winexe version %d.%d\nThis program may be freely redistributed under the terms of the GNU GPLv3\n";

static struct loadparm_context *ldprm_ctx;
static struct tevent_context *ev_ctx;

static struct termios termios_orig;
static int termios_orig_is_valid = 0;

static int abort_requested = 0;

/* winexesvc32.exe binary blob */
extern unsigned int winexesvc32_exe_len;
extern unsigned char winexesvc32_exe[];

/* winexesvc64.exe binary blob */
extern unsigned int winexesvc64_exe_len;
extern unsigned char winexesvc64_exe[];

struct program_options {
	char *hostname;
	char *cmd;
	struct cli_credentials *credentials;
	char *runas;
	char *runas_file;
	int flags;
};

static void parse_args(int argc, char *argv[], struct program_options *options)
{
	poptContext pc;
	int opt, i;
	struct cli_credentials *cred;

	int argc_new;
	char **argv_new;

	int flag_interactive = SVC_IGNORE_INTERACTIVE;
	int flag_ostype = 2;
	int flag_reinstall = 0;
	int flag_uninstall = 0;
	int flag_system = 0;
	int flag_help = 0;
	int flag_version = 0;
	int flag_profile = 0;
	int flag_convert = 0;
	int flag_nopass = 0;
	char *opt_user = NULL;
	char *opt_kerberos = NULL;
	char *opt_auth_file = NULL;
	char *opt_debuglevel = NULL;
	
	memset(options, 0, sizeof(struct program_options));

	struct poptOption long_options[] = {
		{ "help", 'h', POPT_ARG_NONE, &flag_help, 0,
			"Display help message" },
		{ "version", 'V', POPT_ARG_NONE, &flag_version, 0,
			"Display version number" },
		{ "user", 'U', POPT_ARG_STRING, &opt_user, 0,
			"Set the network username", "[DOMAIN/]USERNAME[%PASSWORD]" },
		{ "authentication-file", 'A', POPT_ARG_STRING, &opt_auth_file, 0,
			"Get the credentials from a file", "FILE" },
		{ "no-pass", 'N', POPT_ARG_NONE, &flag_nopass, 0,
			"Do not ask for a password", NULL },
		{ "kerberos", 'k', POPT_ARG_STRING, &opt_kerberos, 0,
			"Use Kerberos, -k [yes|no]" },
		{ "debuglevel", 'd', POPT_ARG_STRING, &opt_debuglevel, 0,
			"Set debug level", "DEBUGLEVEL" },
		{ "uninstall", 0, POPT_ARG_NONE, &flag_uninstall, 0,
			"Uninstall winexe service after remote execution", NULL},
		{ "reinstall", 0, POPT_ARG_NONE, &flag_reinstall, 0,
			"Reinstall winexe service before remote execution", NULL},
		{ "system", 0, POPT_ARG_NONE, &flag_system, 0,
			"Use SYSTEM account" , NULL},
		{ "profile", 0, POPT_ARG_NONE, &flag_profile, 0,
			"Load user profile", NULL},
		{ "convert", 0, POPT_ARG_NONE, &flag_convert, 0,
			"Try to convert characters between local and remote code-pages", NULL},
		{ "runas", 0, POPT_ARG_STRING, &options->runas, 0,
			"Run as the given user (BEWARE: this password is sent in cleartext over the network!)" , "[DOMAIN\\]USERNAME%PASSWORD"},
		{ "runas-file", 0, POPT_ARG_STRING, &options->runas_file, 0,
			"Run as user options defined in a file", "FILE"},
		{ "interactive", 0, POPT_ARG_INT, &flag_interactive, 0,
			"Desktop interaction: 0 - disallow, 1 - allow. If allow, also use the --system switch (Windows requirement). Vista does not support this option.", "0|1"},
		{ "ostype", 0, POPT_ARG_INT, &flag_ostype, 0,
			"OS type: 0 - 32-bit, 1 - 64-bit, 2 - winexe will decide. Determines which version (32-bit or 64-bit) of service will be installed.", "0|1|2"},
		POPT_TABLEEND
	};

	pc = poptGetContext(argv[0], argc, (const char **) argv, long_options, 0);

	poptSetOtherOptionHelp(pc, "[OPTION]... //HOST COMMAND\nOptions:");

	if (((opt = poptGetNextOpt(pc)) != -1) || flag_help || flag_version) {
		DEBUG(0, (version_message_fmt, VERSION_MAJOR, VERSION_MINOR));
		if (flag_version)
			exit(0);
		poptPrintHelp(pc, stdout, 0);
		if (flag_help)
			exit(0);
		exit(1);
	}

	argv_new = discard_const_p(char *, poptGetArgs(pc));

	argc_new = argc;
	for (i = 0; i < argc; i++) {
		if (!argv_new || argv_new[i] == NULL) {
			argc_new = i;
			break;
		}
	}

	if (argc_new != 2 || argv_new[0][0] != '/' || argv_new[0][1] != '/') {
		DEBUG(0, (version_message_fmt, VERSION_MAJOR, VERSION_MINOR));
		poptPrintHelp(pc, stdout, 0);
		exit(1);
	}

	if (opt_debuglevel)
		lpcfg_set_cmdline(ldprm_ctx, "log level", opt_debuglevel);

	cred = cli_credentials_init(talloc_autofree_context());

	if (opt_user)
		cli_credentials_parse_string(cred, opt_user, CRED_SPECIFIED);
	else if (opt_auth_file)
		cli_credentials_parse_file(cred, opt_auth_file, CRED_SPECIFIED);
	cli_credentials_guess(cred, ldprm_ctx);
	if (!cli_credentials_get_password(cred) && !flag_nopass) {
		char *p = getpass("Enter password: ");
		if (*p)
			cli_credentials_set_password(cred, p, CRED_SPECIFIED);
	}

	if (opt_kerberos)
		cli_credentials_set_kerberos_state(cred,
		                                   strcmp(opt_kerberos, "yes")
		                                   ? CRED_MUST_USE_KERBEROS
		                                   : CRED_DONT_USE_KERBEROS);

	if (options->runas == NULL && options->runas_file != NULL) {
		struct cli_credentials* cred = cli_credentials_init(talloc_autofree_context());
		cli_credentials_parse_file(cred, options->runas_file, CRED_SPECIFIED);
		const char *user = cli_credentials_get_username(cred);
		const char *pass = cli_credentials_get_password(cred);
		if (user && pass) {
			char buffer[1024];
			const char *dom = cli_credentials_get_domain(cred);
			if (dom) {
				snprintf(buffer, sizeof(buffer), "%s\\%s%%%s", dom, user, pass);
			} else {
				snprintf(buffer, sizeof(buffer), "%s%%%s", user, pass);
			}
			buffer[sizeof(buffer)-1] = '\0';
			options->runas = strdup(buffer);
		}
	}

	options->credentials = cred;

	options->hostname = argv_new[0] + 2;
	options->cmd = argv_new[1];
	
	options->flags = flag_interactive;
	if (flag_reinstall)
		options->flags |= SVC_FORCE_UPLOAD;
	if (flag_ostype == 1)
		options->flags |= SVC_OS64BIT;
	if (flag_ostype == 2)
		options->flags |= SVC_OSCHOOSE;
	if (flag_uninstall)
		options->flags |= SVC_UNINSTALL;
	if (flag_system)
		options->flags |= SVC_SYSTEM;
	if (flag_profile)
		options->flags |= SVC_PROFILE;
	if (flag_convert)
		options->flags |= SVC_CONVERT;
}

enum {
	STATE_OPENING,
	STATE_GETTING_VERSION,
	STATE_RUNNING,
	STATE_CLOSING,
	STATE_CLOSING_FOR_REINSTALL,
	STATE_INSTALLING
};

enum {
	RET_CODE_CTRL_PIPE_ERROR = 0xf0,
	RET_CODE_INSTALL_ERROR = 0xf1,
	RET_CODE_UNKNOWN_ERROR = 0xf2
};

struct winexe_context {
	int state;
	iconv_t iconv_enc;
	iconv_t iconv_dec;
	struct program_options *args;
	struct smbcli_tree *tree;
	struct async_context *ac_ctrl;
	struct async_context *ac_in;
	struct async_context *ac_out;
	struct async_context *ac_err;
	struct tevent_timer *ev_timeout;
	struct tevent_fd *ev_stdin;
	int return_code;
};

static void on_in_pipe_open(struct winexe_context *c);
static void on_in_pipe_write(struct winexe_context *c);

static void on_out_pipe_read(struct winexe_context *c, const char *data, int len);
static void on_err_pipe_read(struct winexe_context *c, const char *data, int len);

static void on_in_pipe_error(struct winexe_context *c, int func, NTSTATUS status);
static void on_out_pipe_error(struct winexe_context *c, int func, NTSTATUS status);
static void on_err_pipe_error(struct winexe_context *c, int func, NTSTATUS status);

static const char *cmd_check(const char *data, const char *cmd, int len)
{
	int lcmd = strlen(cmd);
	if (lcmd >= len)
		return 0;
	if (
		!strncmp(data, cmd, lcmd)
		&& (data[lcmd] == ' ' || data[lcmd] == '\n')
	) {
		return data + lcmd + 1;
	}
	return 0;
}

static void catch_alarm(int sig)
{
	if (++abort_requested > 1) {
		if (termios_orig_is_valid)
			tcsetattr(0, TCSANOW, &termios_orig);
		exit(1);
	}
}

static void timer_handler(struct tevent_context *ev, struct tevent_timer *te, struct timeval current_time, void *private_data)
{
	struct winexe_context *c = talloc_get_type(private_data, struct winexe_context);
	if (abort_requested) {
		fprintf(stderr, "Aborting...\n");
		async_write(c->ac_ctrl, "abort\n", 6);
	} else {
		c->ev_timeout = tevent_add_timer(c->tree->session->transport->ev, c, timeval_current_ofs(0, 10000), (tevent_timer_handler_t)timer_handler, c);
	}
}

static void on_ctrl_pipe_open(struct winexe_context *c)
{
	char *str = (c->args->flags & SVC_CONVERT) ? "get codepage\nget version\n" : "get version\n";

	DEBUG(1, ("CTRL: Sending command: %s", str));
	c->state = STATE_GETTING_VERSION;
	async_write(c->ac_ctrl, str, strlen(str));
	signal(SIGINT, catch_alarm);
	signal(SIGTERM, catch_alarm);
	c->ev_timeout = tevent_add_timer(c->tree->session->transport->ev, c, timeval_current_ofs(0, 10000), (tevent_timer_handler_t)timer_handler, c);
}

static void on_ctrl_pipe_close(struct winexe_context *c)
{
	TALLOC_FREE(c->ev_stdin);
	TALLOC_FREE(c->ev_timeout);
}

static void on_ctrl_pipe_error(struct winexe_context *c, int func, NTSTATUS status)
{
	DEBUG(1, ("ERROR: on_ctrl_pipe_error - %s\n", nt_errstr(status)));
	if (func == ASYNC_OPEN_RECV) {
		if (c->state == STATE_OPENING) {
			DEBUG(1, ("ERROR: Cannot open control pipe - %s, installing service\n", nt_errstr(status)));
			c->state = STATE_INSTALLING;
			return;
		}
		DEBUG(1, ("ERROR: Control pipe - %s, closing\n", nt_errstr(status)));
		c->state = STATE_CLOSING;
		c->return_code = RET_CODE_CTRL_PIPE_ERROR;
	}

	TALLOC_FREE(c->ev_stdin);
	TALLOC_FREE(c->ev_timeout);
}

const char *codepage_to_string(int cp)
{
	switch (cp) {
	  case 850: return "CP850";
	  case 852: return "CP852";
	  default: return "CP850";
	}
}

static void on_ctrl_pipe_read(struct winexe_context *c, const char *data, int len)
{
	const char *p;
	DEBUG(1, ("CTRL: Received: %.*s", len, data));
	if ((p = cmd_check(data, CMD_STD_IO_ERR, len))) {
		unsigned int npipe = strtoul(p, 0, 16);
		char *fn;
		/* Open in */
		c->ac_in = talloc_zero(c, struct async_context);
		c->ac_in->tree = c->tree;
		c->ac_in->cb_ctx = c;
		c->ac_in->cb_open = (async_cb_open) on_in_pipe_open;
		c->ac_in->cb_write = (async_cb_write) on_in_pipe_write;
		c->ac_in->cb_error = (async_cb_error) on_in_pipe_error;
		fn = talloc_asprintf(c->ac_in, "\\" PIPE_NAME_IN, npipe);
		async_open(c->ac_in, fn, OPENX_MODE_ACCESS_RDWR);
		/* Open out */
		c->ac_out = talloc_zero(c, struct async_context);
		c->ac_out->tree = c->tree;
		c->ac_out->cb_ctx = c;
		c->ac_out->cb_read = (async_cb_read) on_out_pipe_read;
		c->ac_out->cb_error = (async_cb_error) on_out_pipe_error;
		fn = talloc_asprintf(c->ac_out, "\\" PIPE_NAME_OUT, npipe);
		async_open(c->ac_out, fn, OPENX_MODE_ACCESS_RDWR);
		/* Open err */
		c->ac_err = talloc_zero(c, struct async_context);
		c->ac_err->tree = c->tree;
		c->ac_err->cb_ctx = c;
		c->ac_err->cb_read = (async_cb_read) on_err_pipe_read;
		c->ac_err->cb_error = (async_cb_error) on_err_pipe_error;
		fn = talloc_asprintf(c->ac_err, "\\" PIPE_NAME_ERR, npipe);
		async_open(c->ac_err, fn, OPENX_MODE_ACCESS_RDWR);
	} else if ((p = cmd_check(data, CMD_RETURN_CODE, len))) {
		c->return_code = strtoul(p, 0, 16);
	} else if ((p = cmd_check(data, "version", len))) {
		int ver = strtoul(p, 0, 0);
		if (ver/10 != VERSION/10) {
			DEBUG(1, ("CTRL: Bad version of service (is %d.%d, expected %d.%d), reinstalling.\n", ver/100, ver%100, VERSION/100, VERSION%100));
			async_close(c->ac_ctrl);
			c->state = STATE_CLOSING_FOR_REINSTALL;
		} else {
			char *str = "";
			if (c->args->flags & SVC_PROFILE)
				str = "set profile 1\n";
			if (c->args->runas)
				str = talloc_asprintf(c, "%sset runas %s\nrun %s\n", str, c->args->runas, c->args->cmd);
			else
				str = talloc_asprintf(c, "%s%srun %s\n", str, (c->args->flags & SVC_SYSTEM) ? "set system 1\n" : "" , c->args->cmd);
			DEBUG(1, ("CTRL: Sending command: %s", str));
			async_write(c->ac_ctrl, str, strlen(str));
			talloc_free(str);
			c->state = STATE_RUNNING;
		}
	} else if ((p = cmd_check(data, "codepage", len))) {
		int cp = strtoul(p, 0, 0);
		const char *cp_str = codepage_to_string(cp);
		DEBUG(1,("Creating iconv for %s\n", cp_str));
		c->iconv_enc = iconv_open(cp_str, "UTF-8");
		c->iconv_dec = iconv_open("UTF-8//TRANSLIT", cp_str);
	} else if ((p = cmd_check(data, "error", len))) {
		DEBUG(0, ("Error: %.*s", len, data));
		if (c->state == STATE_GETTING_VERSION) {
			DEBUG(0, ("CTRL: Probably old version of service, reinstalling.\n"));
			async_close(c->ac_ctrl);
			c->state = STATE_CLOSING_FOR_REINSTALL;
		}
	} else {
		DEBUG(0, ("CTRL: Unknown command: %.*s", len, data));
	}
}

static void on_stdin_read_event(struct tevent_context *ev,
                                struct tevent_fd *fde,
                                uint16_t flags,
                                struct winexe_context *c)
{
	char data[256];
	int len;
	if ((len = read(0, &data, sizeof(data))) > 0) {
		if (c->iconv_enc == (iconv_t)(-1)) {
			async_write(c->ac_in, data, len);
			return;
		}

		char *pdata = data;
		size_t l = len;
		while (l > 0) {
			char buf[4096];
			char *p = buf;
			size_t left = sizeof(buf);

			size_t nchars = iconv(c->iconv_enc, (char **)&pdata, &l, &p, &left);

			if (p - buf > 0)
				async_write(c->ac_in, buf, p - buf);
			if (nchars == -1) {
				DEBUG(9, ("Could not convert: \"%.*s\", errno=%d\n", (int)l, pdata, errno));
				async_write(c->ac_in, pdata, l);
				return;
			}

		}
	} else {
		usleep(10);
	}
}

static bool is_fd_pollable(int fd)
{
	struct epoll_event ev = {};

	/* dirty check, probably not portable */
	epoll_ctl(fd, EPOLL_CTL_ADD, fd, &ev);

	return errno != EPERM;
}

static void on_in_pipe_open(struct winexe_context *c)
{
	if (is_fd_pollable(0))
	    c->ev_stdin = tevent_add_fd(c->tree->session->transport->ev,
	                            c->tree, 0, TEVENT_FD_READ,
	                            (tevent_fd_handler_t) on_stdin_read_event, c);
	else
	    on_stdin_read_event(NULL, NULL, 0, c);

	struct termios termios_tmp;
	tcgetattr(0, &termios_orig);
	termios_orig_is_valid = 1;
	termios_tmp = termios_orig;
	termios_tmp.c_lflag &= ~ICANON;
	tcsetattr(0, TCSANOW, &termios_tmp);
	setbuf(stdin, NULL);
}

static void on_in_pipe_write(struct winexe_context *c)
{
	if (c->ev_stdin)
		return;

	on_stdin_read_event(NULL, NULL, 0, c);
}

static void write_checking_retval(int fd, const char *data, int len)
{
	ssize_t r = write(fd, data, len);
	if (r < len)
		DEBUG(0, ("ERROR: Failed trying to write %d bytes; value returned was %d\n",
		      len, (int)r));
	return;
}

static void write_conv_buf(int fd, struct winexe_context *c, const char *data, int len)
{
	if (c->iconv_dec == (iconv_t)(-1)) {
		write_checking_retval(fd, data, len);
		return;
	}

	size_t l = len;
	while (l > 0) {
		char buf[4096];
		char *p = buf;
		size_t left = sizeof(buf);

		size_t nchars = iconv(c->iconv_dec, (char **)&data, &l, &p, &left);

		write_checking_retval(fd, buf, p - buf);
		if (nchars == -1) {
			DEBUG(9, ("Could not convert: \"%.*s\", errno=%d\n", (int)l, data, errno));
			write_checking_retval(1, data, l);
			return;
		}

	}
}

static void on_out_pipe_read(struct winexe_context *c, const char *data, int len)
{
	write_conv_buf(1, c, data, len);
}

static void on_in_pipe_error(struct winexe_context *c, int func, NTSTATUS status)
{
	async_close(c->ac_in);
}

static void on_out_pipe_error(struct winexe_context *c, int func, NTSTATUS status)
{
	async_close(c->ac_out);
}

static void on_err_pipe_read(struct winexe_context *c, const char *data, int len)
{
	write_conv_buf(2, c, data, len);
}

static void on_err_pipe_error(struct winexe_context *c, int func, NTSTATUS status)
{
	async_close(c->ac_err);
}

static int exit_program(struct winexe_context *c)
{
	if (c->args->flags & SVC_UNINSTALL) {
		svc_uninstall(ev_ctx, c->args->hostname,
		              SERVICE_NAME, SERVICE_FILENAME,
		              c->args->credentials, ldprm_ctx);
	}
	if (termios_orig_is_valid)
		tcsetattr(0, TCSANOW, &termios_orig);
	return c->return_code;
}

int main(int argc, char *argv[])
{
	NTSTATUS status;
	struct smbcli_tree *cli_tree;
	struct program_options options;

	dcerpc_init();
	ldprm_ctx = loadparm_init_global(false);
	parse_args(argc, argv, &options);
	DEBUG(1, (version_message_fmt, VERSION_MAJOR, VERSION_MINOR));
	ev_ctx = TEVENT_CONTEXT_INIT(talloc_autofree_context());

	if (options.flags & SVC_FORCE_UPLOAD) {
		svc_uninstall(ev_ctx, options.hostname,
		              SERVICE_NAME, SERVICE_FILENAME,
		              options.credentials,
		              ldprm_ctx);
	}

	if ((options.flags & SVC_FORCE_UPLOAD) || !(options.flags & SVC_IGNORE_INTERACTIVE)) {
		status = svc_install(ev_ctx, options.hostname,
		                     SERVICE_NAME, SERVICE_FILENAME,
		                     winexesvc32_exe, winexesvc32_exe_len,
		                     winexesvc64_exe, winexesvc64_exe_len,
		                     options.credentials, ldprm_ctx, options.flags);
		if (!NT_STATUS_IS_OK(status))
			return 1;
	}

	struct smbcli_options smb_options;
	struct smbcli_session_options session_options;

	lpcfg_smbcli_options(ldprm_ctx, &smb_options);
	lpcfg_smbcli_session_options(ldprm_ctx, &session_options);

	struct smbcli_state *cli_state;
	status = smbcli_full_connection(NULL, &cli_state, options.hostname, lpcfg_smb_ports(ldprm_ctx),
	                                "IPC$", NULL, lpcfg_socket_options(ldprm_ctx), options.credentials,
	                                lpcfg_resolve_context(ldprm_ctx), ev_ctx,
	                                &smb_options, &session_options,
	                                lpcfg_gensec_settings(NULL, ldprm_ctx));
	if (!NT_STATUS_IS_OK(status)) {
		if (NT_STATUS_EQUAL(status, NT_STATUS_NO_MEMORY))
			status = NT_STATUS_OBJECT_NAME_NOT_FOUND;
		DEBUG(0,
			("ERROR: Failed to open connection - %s\n",
			nt_errstr(status)));
		return 1;
	}

	cli_tree = cli_state->tree;

	struct winexe_context *c =
		talloc_zero(NULL, struct winexe_context);
	if (c == NULL) {
		DEBUG(0, ("ERROR: Failed to allocate struct winexe_context\n"));
		return 1;
	}

	c->tree = cli_tree;
	c->ac_ctrl = talloc_zero(NULL, struct async_context);
	c->ac_ctrl->tree = cli_tree;
	c->ac_ctrl->cb_ctx = c;
	c->ac_ctrl->cb_open = (async_cb_open) on_ctrl_pipe_open;
	c->ac_ctrl->cb_close = (async_cb_open) on_ctrl_pipe_close;
	c->ac_ctrl->cb_read = (async_cb_read) on_ctrl_pipe_read;
	c->ac_ctrl->cb_error = (async_cb_error) on_ctrl_pipe_error;
	c->args = &options;
	c->return_code = RET_CODE_UNKNOWN_ERROR;
	c->iconv_dec = (iconv_t)-1;
	c->iconv_enc = (iconv_t)-1;
	c->state = STATE_OPENING;
	do {
		async_open(c->ac_ctrl, "\\" PIPE_NAME, OPENX_MODE_ACCESS_RDWR);

		tevent_loop_wait(cli_tree->session->transport->ev);

		if (c->state == STATE_CLOSING_FOR_REINSTALL) {
			DEBUG(1,("Uninstalling service\n"));
			svc_uninstall(ev_ctx, c->args->hostname,
			              SERVICE_NAME, SERVICE_FILENAME,
			              c->args->credentials,
			              ldprm_ctx);
			c->state = STATE_INSTALLING;
		}

		if (c->state != STATE_INSTALLING)
			break;

		DEBUG(1,("Installing service\n"));
		status = svc_install(ev_ctx, c->args->hostname,
		                     SERVICE_NAME, SERVICE_FILENAME,
		                     winexesvc32_exe, winexesvc32_exe_len,
		                     winexesvc64_exe, winexesvc64_exe_len,
		                     c->args->credentials, ldprm_ctx,
		                     c->args->flags);
		if (!NT_STATUS_IS_OK(status)) {
			c->return_code = RET_CODE_INSTALL_ERROR;
			break;
		}
	} while (1);

	return exit_program(c);
}

