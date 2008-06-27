/*
 * Univention Client Login
 *  this file is part of the Univention thin client tools
 *
 * Copyright (C) 2004, 2005, 2006 Univention GmbH
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
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA 02110-1301 USA
 */

#include <stdlib.h>
#include <stdio.h>
#include <wait.h>
#include <string.h>
#include <ctype.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <pwd.h>

#include "command.h"
#include "debug.h"
#include "process.h"
#include "protocol.h"
#include "security.h"

int alive_handler(char **argv);
int ok_handler(char **argv);
int setenv_handler(char **argv);
int unsetenv_handler(char **argv);
int run_handler(char **argv);
int start_handler(char **argv);
int exit_handler(char **argv);
int error_handler(char **argv);
void call_cleanup_script(void);
int cleanup_handler(char **argv);
int stdout_handler(char **argv);
int stderr_handler(char **argv);
int exit_on_last_handler(char **argv);
int mount_handler(char **argv);
int get_command_args(char *buffer, char **argv, int max);
