// SPDX-FileCopyrightText: 2022-2024 Univention GmbH
// SPDX-License-Identifier: AGPL-3.0-only
#include <stdio.h>
int main(void) {
	for (;;) {
		int c = getchar();
		if (c == '\n') {
			c = getchar();
			if (c == ' ' || c == '\t')
				continue;
			putchar('\n');
		}
		if (c == EOF)
			break;
		putchar(c);
	}
	return 0;
}
