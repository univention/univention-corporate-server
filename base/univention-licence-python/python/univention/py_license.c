#include <univention/license.h>
#include <Python.h>

//select license
static PyObject *
PySelect (PyObject *self, PyObject *args)
{
	char* module = NULL;
	PyObject* retObj = NULL;
	
	if (PyArg_ParseTuple(args, "s", &module))
	{
		retObj = Py_BuildValue("i", univention_license_select(module));
	}
	return retObj;
}

//select license by DN
static PyObject *
PySelectDN (PyObject *self, PyObject *args)
{
	char* licenseDN = NULL;
	PyObject* retObj = NULL;
	
	if (PyArg_ParseTuple(args, "s", &licenseDN))
	{
		retObj = Py_BuildValue("i", univention_license_selectDN(licenseDN));
	}
	return retObj;
}


//get value
static PyObject *
PyGetValue (PyObject *self, PyObject *args)
{
	char* arg = NULL;
	lStrings* values = NULL;
	PyObject* retObj = NULL;
	
	if (PyArg_ParseTuple(args, "s", &arg))
	{
		values = univention_license_get_value(arg);
		if (values != NULL)
		{
			int i;
			//create convert parameter string
			/*
			char* param = malloc(sizeof(char)*values->num+1);
			memset(param, 's', sizeof(char)*values->num);
			param[values->num] = 0;
			printf("DEBUG:param:%i:%s.\n", values->num, param);
			*/
			//convert to python
			retObj = Py_BuildValue("s", values->line[0]);
			for (i=1; i < values->num; i++)
			{
				retObj = Py_BuildValue("Os",retObj, values->line[i]);
			}
			
			//cleanup
			//free(param);
			univention_licenseStrings_free(values);
			values = NULL;
		}
	}
	return retObj;
}

//check license
static PyObject *
PyCheck (PyObject *self, PyObject *args)
{
	char* objectDN = NULL;
	PyObject* retObj = NULL;
	
	if (PyArg_ParseTuple(args, "s", &objectDN))
	{
		retObj = Py_BuildValue("i", univention_license_check(objectDN));
	}
	return retObj;
}

//cleanup
static PyObject *
PyFree(PyObject* self, PyObject* args)
{
	univention_license_free();
	return Py_BuildValue("i", 1);
}

static struct PyMethodDef license_methods[] = {
	{"select", PySelect, METH_VARARGS, "Select the License of this Moduletype"},
	{"selectDN", PySelectDN, METH_VARARGS, "Select the License at this location."},
	{"getValue", PyGetValue, METH_VARARGS, "Get the value of the attribute of the current selected License."},
	{"check", PyCheck, METH_VARARGS, "Check the state of the license at objectDN"},
	{"free",   PyFree, METH_VARARGS, "Cleanup the license lib."},
	{NULL, NULL, 0, NULL}
};

void initlibuniventionlicense(void)
{
	(void) Py_InitModule("libuniventionlicense", license_methods);
}

void initlicense(void)
{
	(void) Py_InitModule("license", license_methods);
}
