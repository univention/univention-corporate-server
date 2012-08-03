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
