# -*- coding: utf-8 -*-

import traceback
import sys
def formatTraceback(): # call this function directly in the "except"-clause
	stackIn = traceback.extract_stack()
	stackDown = traceback.extract_tb(sys.exc_info()[2])
	stack = stackIn[:-2] + stackDown # -2 to remove exception handler and this function
	return traceback.format_list(stack)
