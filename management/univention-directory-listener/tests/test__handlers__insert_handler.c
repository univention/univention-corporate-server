#include "test.c"

#include "../src/handlers.c"

#define TEST(n)   \
	_TEST(n); \
	static bool test_##n(void)

#define ASSERT(cond)                                      \
	do {                                              \
		if (!(cond)) {                            \
			fprintf(stderr, "! " #cond "\n"); \
			return false;                     \
		}                                         \
	} while (0)

TEST(empty) {
	Handler *h = calloc(1, sizeof(Handler));
	h->priority = PRIORITY_DEFAULT;

	insert_handler(h);

	ASSERT(handlers == h);

	free(h);
	handlers = NULL;
	return true;
}

TEST(smaller) {
	Handler *h = calloc(2, sizeof(Handler));
	h[0].priority = PRIORITY_DEFAULT;
	h[1].priority = PRIORITY_MINIMUM;

	insert_handler(h + 0);
	insert_handler(h + 1);

	ASSERT(handlers == h + 1);
	ASSERT(h[1].next == h + 0);
	ASSERT(h[0].next == NULL);

	free(h);
	handlers = NULL;
	return true;
}

TEST(bigger) {
	Handler *h = calloc(2, sizeof(Handler));
	h[0].priority = PRIORITY_DEFAULT;
	h[1].priority = PRIORITY_MAXIMUM;

	insert_handler(h + 0);
	insert_handler(h + 1);

	ASSERT(handlers == h + 0);
	ASSERT(h[0].next == h + 1);
	ASSERT(h[1].next == NULL);

	free(h);
	handlers = NULL;
	return true;
}
