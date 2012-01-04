#include <stdio.h>
#include <assert.h>
#include <univention/debug.h>

int main(void) {
	FILE * f;
	enum uv_debug_level l;
	f = univention_debug_init("stdout", UV_DEBUG_NO_FLUSH, UV_DEBUG_FUNCTION);
	assert (f != NULL);

	univention_debug(UV_DEBUG_MAIN, UV_DEBUG_ERROR, "Error in main: %%%%%%");
	univention_debug(UV_DEBUG_MAIN, UV_DEBUG_WARN, "Warning in main: %%%%%%");
	univention_debug(UV_DEBUG_MAIN, UV_DEBUG_PROCESS, "Process in main: %%%%%%");
	univention_debug(UV_DEBUG_MAIN, UV_DEBUG_INFO, "Information in main: %%%%%%");
	univention_debug(UV_DEBUG_MAIN, UV_DEBUG_ALL, "All in main: %%%%%%");

	univention_debug_set_level(UV_DEBUG_MAIN, UV_DEBUG_PROCESS);
	l = univention_debug_get_level(UV_DEBUG_MAIN);
	assert (l == UV_DEBUG_PROCESS);

	univention_debug_set_function(UV_DEBUG_FUNCTION);
	univention_debug_begin("Function");
	univention_debug_end("Function");

	univention_debug_set_function(UV_DEBUG_NO_FUNCTION);
	univention_debug_begin("No function");
	univention_debug_end("No function");

	univention_debug_exit();

	univention_debug_set_level(UV_DEBUG_MAIN, UV_DEBUG_ALL);
	l = univention_debug_get_level(UV_DEBUG_MAIN);
	assert (l != UV_DEBUG_ALL);

	univention_debug(UV_DEBUG_MAIN, UV_DEBUG_ALL, "No crash");

	return 0;
}
