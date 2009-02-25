/*
 * Univention Debug
 *  py_debug.c
 *
 * Copyright (C) 2004-2009 Univention GmbH
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
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

#include <Python.h>
#include <univention/debug.h>

/*
 * example:
 *
 * import univention.debug
 *
 * univention.debug.init("stdout", DEBUG_NO_FLUSH, DEBUG_FUNCTION)
 * univention.debug.set_level(univention.debug.LISTENER, univention.debug.ERROR)
 * univention.debug.debug(univention.debug.LISTENER, univention.debug.ERROR, 'Fatal error, var = '+j)
 *
 */

static PyObject *py_univention_debug_debug(PyObject *self, PyObject *args)
{
    int id;
    int level;
    char *string;

    if ( !PyArg_ParseTuple(args,"iis",&id,&level,&string) )
    {
        return NULL;
    }

    univention_debug(id, level, string);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *py_univention_debug_init(PyObject *self, PyObject *args)
{
    char *logfile;
    int flush,function;

    if ( !PyArg_ParseTuple(args,"sii",&logfile,&flush,&function))
    {
        return NULL;
    }

    univention_debug_init(logfile, (char)flush, (char)function);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *py_univention_debug_set_level(PyObject *self, PyObject *args)
{
    int id;
    int level;

    if ( !PyArg_ParseTuple(args,"ii",&id,&level))
    {
        return NULL;
    }

    univention_debug_set_level(id,level);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *py_univention_debug_set_function(PyObject *self, PyObject *args)
{
    int function;

    if ( !PyArg_ParseTuple(args,"i",&function))
    {
        return NULL;
    }

    univention_debug_set_function(function);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *py_univention_debug_begin(PyObject *self, PyObject *args)
{
    char *string;

    if ( !PyArg_ParseTuple(args,"s",&string))
    {
        return NULL;
    }

    univention_debug_begin(string);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *py_univention_debug_end(PyObject *self, PyObject *args)
{
    char *string;

    if ( !PyArg_ParseTuple(args,"s",&string))
    {
        return NULL;
    }

    univention_debug_end(string);

    Py_INCREF(Py_None);
    return Py_None;
}

static PyObject *py_univention_debug_exit(PyObject *self, PyObject *args)
{
	univention_debug_exit();

	Py_INCREF(Py_None);
    return Py_None;
}


static struct PyMethodDef debug_methods[] = {
    {"debug", py_univention_debug_debug, METH_VARARGS, "Print a debug message" },
    {"init",py_univention_debug_init, METH_VARARGS, "Init the debug module"},
    {"set_level", py_univention_debug_set_level, METH_VARARGS, "set the level for one debug modul"},
    {"set_function", py_univention_debug_set_function, METH_VARARGS, "Printing funcion entry"},
    {"begin", py_univention_debug_begin, METH_VARARGS, "Function starts here"},
    {"end", py_univention_debug_end, METH_VARARGS, "Function ends here"},
	{"exit", py_univention_debug_exit, METH_VARARGS, "Close debuglog"},
    { NULL, NULL, 0, NULL}
};

void init_debug()
{
    PyObject *module, *dict;

    module = Py_InitModule("_debug", debug_methods);

    dict = PyModule_GetDict(module);

    PyDict_SetItemString(dict, "ERROR",PyInt_FromLong( UV_DEBUG_ERROR));
    PyDict_SetItemString(dict, "WARN",PyInt_FromLong( UV_DEBUG_WARN));
    PyDict_SetItemString(dict, "PROCESS",PyInt_FromLong( UV_DEBUG_PROCESS));
    PyDict_SetItemString(dict, "INFO",PyInt_FromLong( UV_DEBUG_INFO));
    PyDict_SetItemString(dict, "ALL",PyInt_FromLong( UV_DEBUG_ALL));

    PyDict_SetItemString(dict, "MAIN",PyInt_FromLong( UV_DEBUG_MAIN));
    PyDict_SetItemString(dict, "LDAP",PyInt_FromLong( UV_DEBUG_LDAP));
    PyDict_SetItemString(dict, "USERS",PyInt_FromLong( UV_DEBUG_USERS));
    PyDict_SetItemString(dict, "NETWORK",PyInt_FromLong( UV_DEBUG_NETWORK));
    PyDict_SetItemString(dict, "SSL",PyInt_FromLong( UV_DEBUG_SSL));
    PyDict_SetItemString(dict, "SLAPD",PyInt_FromLong( UV_DEBUG_SLAPD));
    PyDict_SetItemString(dict, "SEARCH",PyInt_FromLong( UV_DEBUG_SEARCH));
    PyDict_SetItemString(dict, "TRANSFILE",PyInt_FromLong( UV_DEBUG_TRANSFILE));
    PyDict_SetItemString(dict, "LISTENER",PyInt_FromLong( UV_DEBUG_LISTENER));
    PyDict_SetItemString(dict, "POLICY",PyInt_FromLong( UV_DEBUG_POLICY));
    PyDict_SetItemString(dict, "ADMIN",PyInt_FromLong( UV_DEBUG_ADMIN));
    PyDict_SetItemString(dict, "CONFIG",PyInt_FromLong( UV_DEBUG_CONFIG));

    PyDict_SetItemString(dict, "NO_FLUSH",PyInt_FromLong( UV_DEBUG_NO_FLUSH));
    PyDict_SetItemString(dict, "FLUSH",PyInt_FromLong( UV_DEBUG_FLUSH));

    PyDict_SetItemString(dict, "NO_FUNCTION",PyInt_FromLong( UV_DEBUG_NO_FUNCTION));
    PyDict_SetItemString(dict, "FUNCTION",PyInt_FromLong( UV_DEBUG_FUNCTION));

}
