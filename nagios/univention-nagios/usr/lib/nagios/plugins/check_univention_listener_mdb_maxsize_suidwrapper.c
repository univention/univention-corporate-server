//
// Univention Nagios Plugin
//  wrapper to call script for checking listener_mdb_maxsize
//
// Copyright 2015-2018 Univention GmbH
//
// http://www.univention.de/
//
// All rights reserved.
//
// The source code of this program is made available
// under the terms of the GNU Affero General Public License version 3
// (GNU AGPL V3) as published by the Free Software Foundation.
//
// Binary versions of this program provided by Univention to you as
// well as other copyrighted, protected or trademarked materials like
// Logos, graphics, fonts, specific documentations and configurations,
// cryptographic keys etc. are subject to a license agreement between
// you and Univention and not subject to the GNU AGPL V3.
//
// In the case you use this program under the terms of the GNU AGPL V3,
// the program is provided in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public
// License with the Debian GNU/Linux or Univention distribution in file
// /usr/share/common-licenses/AGPL-3; if not, see
// <http://www.gnu.org/licenses/>.

#include <unistd.h>
#include <errno.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <getopt.h>

#define COMMAND "/usr/lib/nagios/plugins/check_univention_listener_mdb_maxsize"

main(int argc, char ** argv, char ** envp) {
	int i = 0;
	char warning[] = "75";
	char critical[] = "90";
	while ((i = getopt(argc, argv, "c:w:")) != -1) {
		switch (i) {
			case 'w':
				strncpy(warning, optarg, 2);
				break;
			case 'c':
				strncpy(critical, optarg, 2);
				break;
			default:
				exit(EXIT_FAILURE);
		}
	}
	uid_t uid = getuid();
	if (setgid(getegid()))
		perror("setgid");
	if (setuid(geteuid()))
		perror("setuid");
	execle(COMMAND, COMMAND, "-w", warning, "-c", critical, (char *)0, (char *)0);
	perror("execle");
	setuid(uid);
	exit(0);
}
