/*
 * Univention Directory Listener
 *  signal handlers are initialized and defined here.
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

#include <signal.h>
#include <sys/types.h>
#include <wait.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdio.h>
#include <unistd.h>

#include <univention/debug.h>

#include "handlers.h"
#include "cache.h"
#include "common.h"
extern char **module_dirs;
extern char *pidfile;

int sig_block_count = 0;
sigset_t block_mask;

void signals_block(void) {
	static int init_done = 0;

	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "blocking signals (was %d)", sig_block_count);
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
		init_done = 1;
	}

	sigprocmask(SIG_BLOCK, &block_mask, NULL);
}

void signals_unblock(void) {
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_ALL, "unblocking signals (was %d)", sig_block_count);
	if ((--sig_block_count) != 0)
		return;
	sigprocmask(SIG_UNBLOCK, &block_mask, NULL);
}


void sig_usr1_handler(int sig) {
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "received signal %d", sig);
	int loglevel = univention_debug_get_level(UV_DEBUG_LISTENER);
	if (loglevel < UV_DEBUG_ALL) {
		loglevel += 1;
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "increasing univention_debug_level to %d", loglevel);
		univention_debug_set_level(UV_DEBUG_LISTENER, loglevel);
	}
}

void sig_usr2_handler(int sig) {
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "received signal %d", sig);
	int loglevel = univention_debug_get_level(UV_DEBUG_LISTENER);
	if (loglevel > UV_DEBUG_ERROR) {
		loglevel -= 1;
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "decreasing univention_debug_level to %d", loglevel);
		univention_debug_set_level(UV_DEBUG_LISTENER, loglevel);
	}
}

void exit_handler(int sig) {
	char **c;
	static bool exit_handler_running = false;

	if (exit_handler_running) {
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "received another signal %d, ignoring", sig);
		return;
	}
	exit_handler_running = true;

	if (sig)
		univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "received signal %d", sig);

	cache_close();
	unlink(pidfile);

	for (c = module_dirs; c != NULL && *c != NULL; c++)
		free(*c);
	free(module_dirs);

	handlers_postrun_all();
	handlers_free_all();

	if (sig) {
		signal(sig, SIG_DFL);
		kill(getpid(), sig);
	} else {
		exit(0);
	}
}

void reload_handler(int sig) {
	univention_debug(UV_DEBUG_LISTENER, UV_DEBUG_WARN, "received signal %d", sig);
	handlers_reload_all_paths();
}

static void install_handler(int sig, void (*handler)(int sig)) {
	struct sigaction setup_action;
	sigset_t block_mask;

	sigemptyset(&block_mask);
	sigaddset(&block_mask, SIGPIPE);
	sigaddset(&block_mask, SIGHUP);
	sigaddset(&block_mask, SIGINT);
	sigaddset(&block_mask, SIGQUIT);
	sigaddset(&block_mask, SIGTERM);
	sigaddset(&block_mask, SIGABRT);

	setup_action.sa_handler = handler;
	setup_action.sa_mask = block_mask;
	setup_action.sa_flags = 0;
	sigaction(sig, &setup_action, NULL);
}

#ifdef NEW_SIGNALS
int pending_signals[16];

void signal_handler(int signal) {
	if (signal >= 0 && signal < 16)
		pending_signals[signal] = 1;
}

void process_signals(void) {
	int signal;

	for (signal = 0; signal < 16; signal++) {
		if (!pending_signals[signal])
			continue;
		switch (signal) {
		case SIGPIPE:
		case SIGINT:
		case SIGQUIT:
		case SIGTERM:
		case SIGABRT:
			exit_handler(signal);
			break;
		case SIGHUP:
			reload_handler(signal);
			break;
		case SIGUSR1:
			sig_usr1_handler(signal);
			break;
		case SIGUSR2:
			sig_usr2_handler(signal);
			break;
		}
		pending_signals[signal] = 0;
	}
}

void signals_init(void) {
	int signal;

	for (signal = 0; signal < 16; signal++)
		pending_signals[signal] = 0;

	install_handler(SIGPIPE, &signal_handler);
	install_handler(SIGINT, &signal_handler);
	install_handler(SIGQUIT, &signal_handler);
	install_handler(SIGTERM, &signal_handler);
	install_handler(SIGABRT, &signal_handler);
	install_handler(SIGHUP, &signal_handler);
	install_handler(SIGUSR1, &signal_handler);
	install_handler(SIGUSR2, &signal_handler);
}
#else
/* initialize signal handling */
void signals_init(void) {
	install_handler(SIGPIPE, &exit_handler);
	install_handler(SIGINT, &exit_handler);
	install_handler(SIGQUIT, &exit_handler);
	install_handler(SIGTERM, &exit_handler);
	install_handler(SIGABRT, &exit_handler);
	install_handler(SIGHUP, &reload_handler);
	install_handler(SIGUSR1, &sig_usr1_handler);
	install_handler(SIGUSR2, &sig_usr2_handler);
}
#endif
