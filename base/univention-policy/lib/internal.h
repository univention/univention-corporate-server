#include <univention/policy.h>

#define FREE(p)	\
	do {	\
		if (p != NULL) {	\
			free(p);	\
			p = NULL;	\
		}	\
	} while (0)

#define FREE_ARRAY(a)	\
	do {	\
		if (a) {	\
			int _i;	\
			for (_i = 0; a[_i]; _i++)	\
				FREE(a[_i]);	\
			FREE(a);	\
		}	\
	} while (0)

struct univention_policy_attribute_list_s;
struct univention_policy_attribute_list_s {
	struct univention_policy_attribute_list_s* next;
	char* name;
	univention_policy_result_t* values;
};

struct univention_policy_list_s;
struct univention_policy_list_s {
	struct univention_policy_list_s* next;
	char* name;
	struct univention_policy_attribute_list_s* attributes;
};

struct univention_policy_handle_s {
	struct univention_policy_list_s* policies;
};
