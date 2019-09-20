//
// Univention Nagios Plugin
//  check_univention_ad_connector_suidwrapper: 
//  wrapper to call script for checking Active Directory connector status
//
// Copyright 2011-2019 Univention GmbH
//
// https://www.univention.de/
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
// <https://www.gnu.org/licenses/>.
//

#include <signal.h>
#include <sys/param.h>
#include <pwd.h>
#include <unistd.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

#define COMMAND "/usr/lib/nagios/plugins/check_univention_ad_connector"


// sanitize string by only accepting the characters [0-9a-zA-Z_-. ]
char saneChars[] = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-. ";
char* strSanitize(char * str)
{
	int n = strlen(str);
	int i = 0;
	
	// replace all insane characters by '_'
	i = strspn(str, saneChars);
	while (i < n) {
		// replace character
		//printf("# str:'%s' replace:%d=%c\n", str, i, str[i]);
		str[i] = '_';
		i = strspn(str, saneChars);
	}

	// return modified string
	return str;
}

main( int argc, char ** argv, char ** envp )
{
	int status = 0;
	int i = 0;
	uid_t uid = getuid();
	if (setgid(getegid()))
		perror("setgid");
	if (setuid(geteuid())) 
		perror("setuid");
	
	if (argc >= 2)
		execle(COMMAND, COMMAND, strSanitize(argv[1]), (char *)0, (char *)0);
		//printf("%s %s\n", COMMAND, strSanitize(argv[1]));
	else 
		execle(COMMAND, COMMAND, (char *)0, (char *)0);
		//printf("%s\n", COMMAND);
	setuid(uid);
	exit(1);
}

