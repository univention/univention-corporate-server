/*
 * Univention Debug
 *  py_debug.c
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

#include <Python.h>
#include <univention/debug.h>

#if PY_MAJOR_VERSION >= 3
#define PyInt_FromLong PyLong_FromLong
#endif

/*
 * example:
 *
 * import univention.debug
 *
 * fd = univention.debug.init("stdout", univention.debug.DEBUG_NO_FLUSH, univention.debug.DEBUG_FUNCTION)
 * univention.debug.set_level(univention.debug.LISTENER, univention.debug.ERROR)
 * univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Fatal error, var = '+j)
 */

static PyObject *
py_univention_debug_debug(PyObject *self, PyObject *args)
{
    int id;
    int level;
    char *string;

    if (!PyArg_ParseTuple(args, "iis", &id, &level, &string)) {
        return NULL;
    }

    univention_debug(id, level, "%s", string);

    Py_RETURN_NONE;
}
PyDoc_STRVAR(py_univention_debug_debug__doc__,
        "debug(category, level, message) - Log debug message.\n"
        "\n"
        "Log message 'message' of severity 'level' to facility 'category'.\n"
        "category - ID of the category, e.g. MAIN, LDAP, USERS, ...\n"
        "level - Level of logging, e.g. ERROR, WARN, PROCESS, INFO, ALL\n"
        "message - The message to log");

static PyObject *
py_univention_debug_init(PyObject *self, PyObject *args)
{
    char *logfile;
    int flush, function;
    FILE * fd;
    PyObject * file;

    if (!PyArg_ParseTuple(args, "sii", &logfile, &flush, &function)) {
        Py_RETURN_NONE;
    }

    fd = univention_debug_init(logfile, (char)flush, (char)function);

    if ( fd == NULL ) {
        /* BUG: We should raise an exception here using
         * return PyErr_SetFromErrnoWithFilename(PyExc_IOError, logfile);
         * but univention_debug_init() returns NULL in many cases:
         * - when already initialized
         * - when open() fails
         */
        Py_RETURN_NONE;
    }

#if PY_MAJOR_VERSION >= 3
    /* use "w+" instead of "a+" as Python3 handels O_APPEND internally by using lseek(), which breaks on STDOUT and STDERR */
    file = PyFile_FromFd(/*fd*/fileno(fd), /*name*/logfile, /*mode*/"wb+", /*buffering*/0, /*encoding*/NULL, /*errors*/NULL, /*newline*/NULL, /*closefd*/0);
#else
    file = PyFile_FromFile( fd, logfile, "a+", NULL );
#endif

    return file;
}
PyDoc_STRVAR(py_univention_debug_init__doc__,
        "init(logfile, force_flush, trace_function) - Initialize debugging library.\n"
        "\n"
        "Initialize debugging library for logging to 'logfile'.\n"
        "logfile - name of the logfile, or 'stderr', or 'stdout'.\n"
        "force_flush - force flushing of messages (True).\n"
        "trace_function - enable (True) or disable (False) function tracing.");

static PyObject *
py_univention_debug_set_level(PyObject *self, PyObject *args)
{
    int id;
    int level;

    if (!PyArg_ParseTuple(args, "ii", &id, &level)) {
        return NULL;
    }

    univention_debug_set_level(id, level);

    Py_RETURN_NONE;
}
PyDoc_STRVAR(py_univention_debug_set_level__doc__,
        "set_level(category, level) - Set debug level for category.\n"
        "\n"
        "Set minimum required severity 'level' for facility 'category'.\n"
        "category - ID of the category, e.g. MAIN, LDAP, USERS, ...\n"
        "level - Level of logging, e.g. ERROR, WARN, PROCESS, INFO, ALL");

static PyObject *
py_univention_debug_get_level(PyObject *self, PyObject *args)
{
    int id;
    enum uv_debug_level level;

    if (!PyArg_ParseTuple(args, "i", &id)) {
        return NULL;
    }

    level = univention_debug_get_level(id);

    return Py_BuildValue("i", level);
}
PyDoc_STRVAR(py_univention_debug_get_level__doc__,
        "get_level(category) -> int - Get debug level for category.\n"
        "\n"
        "Get minimum required severity for facility 'category'.\n"
        "category - ID of the category, e.g. MAIN, LDAP, USERS, ...\n");

static PyObject *
py_univention_debug_set_function(PyObject *self, PyObject *args)
{
    int function;

    if (!PyArg_ParseTuple(args, "i", &function)) {
        return NULL;
    }

    univention_debug_set_function(function);

    Py_RETURN_NONE;
}
PyDoc_STRVAR(py_univention_debug_set_function__doc__,
        "set_function(activate) - Enable function tracing.\n"
        "\n"
        "Enable or disable the logging of function begins and ends.\n"
        "activate - enable (True) or disable (False) function tracing.");

static PyObject *
py_univention_debug_begin(PyObject *self, PyObject *args)
{
    char *string;

    if (!PyArg_ParseTuple(args, "s", &string)) {
        return NULL;
    }

    univention_debug_begin(string);

    Py_RETURN_NONE;
}
PyDoc_STRVAR(py_univention_debug_begin__doc__,
        "begin(fname) - Function starts here.\n"
        "\n"
        "Log the begin of function 'fname'.\n"
        "fname - name of the function starting.");

static PyObject *
py_univention_debug_end(PyObject *self, PyObject *args)
{
    char *string;

    if (!PyArg_ParseTuple(args, "s", &string)) {
        return NULL;
    }

    univention_debug_end(string);

    Py_RETURN_NONE;
}
PyDoc_STRVAR(py_univention_debug_end__doc__,
        "end(fname) - Function ends here.\n"
        "\n"
        "Log the end of function 'fname'.\n"
        "fname - name of the function ending.");

static PyObject *
py_univention_debug_exit(PyObject *self)
{
    univention_debug_exit();

    Py_RETURN_NONE;
}
PyDoc_STRVAR(py_univention_debug_exit__doc__,
        "exit() - Close debug log.\n"
        "\n"
        "Close the debug logfile.");

static PyObject *
py_univention_debug_reopen(PyObject *self)
{
    univention_debug_reopen();

    Py_RETURN_NONE;
}
PyDoc_STRVAR(py_univention_debug_reopen__doc__,
        "reopen() - Re-open logfile.\n"
        "\n"
        "Close and re-open the debug logfile.");


static struct PyMethodDef debug_methods[] = {
    {"debug", (PyCFunction)py_univention_debug_debug, METH_VARARGS, py_univention_debug_debug__doc__},
    {"init", (PyCFunction)py_univention_debug_init, METH_VARARGS, py_univention_debug_init__doc__},
    {"set_level", (PyCFunction)py_univention_debug_set_level, METH_VARARGS, py_univention_debug_set_level__doc__},
    {"get_level", (PyCFunction)py_univention_debug_get_level, METH_VARARGS, py_univention_debug_get_level__doc__},
    {"set_function", (PyCFunction)py_univention_debug_set_function, METH_VARARGS, py_univention_debug_set_function__doc__},
    {"begin", (PyCFunction)py_univention_debug_begin, METH_VARARGS, py_univention_debug_begin__doc__},
    {"end", (PyCFunction)py_univention_debug_end, METH_VARARGS, py_univention_debug_end__doc__},
    {"exit", (PyCFunction)py_univention_debug_exit, METH_NOARGS, py_univention_debug_exit__doc__},
    {"reopen", (PyCFunction)py_univention_debug_reopen, METH_NOARGS, py_univention_debug_reopen__doc__},
    { NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3
PyDoc_STRVAR(m_doc,
        "univention._debug module");
static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    .m_name = "_debug",
    .m_doc = m_doc,
    .m_methods = debug_methods,
};
#endif


#if PY_MAJOR_VERSION >= 3
PyMODINIT_FUNC PyInit__debug(void)
#else
PyMODINIT_FUNC init_debug(void)
#endif
{
    PyObject *module, *dict;

#if PY_MAJOR_VERSION >= 3
    module = PyModule_Create(&moduledef);
#else
    module = Py_InitModule("univention._debug", debug_methods);
#endif

    dict = PyModule_GetDict(module);

    PyDict_SetItemString(dict, "ERROR", PyInt_FromLong(UV_DEBUG_ERROR));
    PyDict_SetItemString(dict, "WARN", PyInt_FromLong(UV_DEBUG_WARN));
    PyDict_SetItemString(dict, "PROCESS", PyInt_FromLong(UV_DEBUG_PROCESS));
    PyDict_SetItemString(dict, "INFO", PyInt_FromLong(UV_DEBUG_INFO));
    PyDict_SetItemString(dict, "ALL", PyInt_FromLong(UV_DEBUG_ALL));

    PyDict_SetItemString(dict, "MAIN", PyInt_FromLong(UV_DEBUG_MAIN));
    PyDict_SetItemString(dict, "LDAP", PyInt_FromLong(UV_DEBUG_LDAP));
    PyDict_SetItemString(dict, "USERS", PyInt_FromLong(UV_DEBUG_USERS));
    PyDict_SetItemString(dict, "NETWORK", PyInt_FromLong(UV_DEBUG_NETWORK));
    PyDict_SetItemString(dict, "SSL", PyInt_FromLong(UV_DEBUG_SSL));
    PyDict_SetItemString(dict, "SLAPD", PyInt_FromLong(UV_DEBUG_SLAPD));
    PyDict_SetItemString(dict, "SEARCH", PyInt_FromLong(UV_DEBUG_SEARCH));
    PyDict_SetItemString(dict, "TRANSFILE", PyInt_FromLong(UV_DEBUG_TRANSFILE));
    PyDict_SetItemString(dict, "LISTENER", PyInt_FromLong(UV_DEBUG_LISTENER));
    PyDict_SetItemString(dict, "POLICY", PyInt_FromLong(UV_DEBUG_POLICY));
    PyDict_SetItemString(dict, "ADMIN", PyInt_FromLong(UV_DEBUG_ADMIN));
    PyDict_SetItemString(dict, "CONFIG", PyInt_FromLong(UV_DEBUG_CONFIG));
    PyDict_SetItemString(dict, "LICENSE", PyInt_FromLong(UV_DEBUG_LICENSE));
    PyDict_SetItemString(dict, "KERBEROS", PyInt_FromLong(UV_DEBUG_KERBEROS));
    PyDict_SetItemString(dict, "DHCP", PyInt_FromLong(UV_DEBUG_DHCP));
    PyDict_SetItemString(dict, "PROTOCOL", PyInt_FromLong(UV_DEBUG_PROTOCOL));
    PyDict_SetItemString(dict, "MODULE", PyInt_FromLong(UV_DEBUG_MODULE));
    PyDict_SetItemString(dict, "ACL", PyInt_FromLong(UV_DEBUG_ACL));
    PyDict_SetItemString(dict, "RESOURCES", PyInt_FromLong(UV_DEBUG_RESOURCES));
    PyDict_SetItemString(dict, "PARSER", PyInt_FromLong(UV_DEBUG_PARSER));
    PyDict_SetItemString(dict, "LOCALE", PyInt_FromLong(UV_DEBUG_LOCALE));
    PyDict_SetItemString(dict, "AUTH", PyInt_FromLong(UV_DEBUG_AUTH));

    PyDict_SetItemString(dict, "NO_FLUSH", PyInt_FromLong(UV_DEBUG_NO_FLUSH));
    PyDict_SetItemString(dict, "FLUSH", PyInt_FromLong(UV_DEBUG_FLUSH));

    PyDict_SetItemString(dict, "NO_FUNCTION", PyInt_FromLong(UV_DEBUG_NO_FUNCTION));
    PyDict_SetItemString(dict, "FUNCTION", PyInt_FromLong(UV_DEBUG_FUNCTION));

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}

/* vim:set ts=4 sw=4 et: */
