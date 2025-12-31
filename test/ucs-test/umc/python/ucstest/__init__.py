#!/usr/bin/python3
#
# Univention Management Console
#  module: ucs-test
#
# SPDX-FileCopyrightText: 2015-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess
import sys
import time

from univention.config_registry import ucr
from univention.management.console.error import UMC_Error
from univention.management.console.modules import Base
from univention.management.console.modules.decorators import simple_response


class NonThreadedError(Exception):
    pass


class ThreadedError(Exception):
    pass


class FakeThread:
    def __init__(self):
        self.exc_info = None
        self.name = "Fake Thread"
        self.trace = None


def joinscript():
    process = subprocess.Popen(['/bin/sh'], stdin=subprocess.PIPE)
    process.communicate(b'''
    . /usr/share/univention-lib/umc.sh

    umc_init
    umc_operation_create "ucstest-all" "UCS Test" "" "ucstest/*"
    umc_policy_append "default-umc-all" "ucstest-all"
    exit 0
    ''')


def unjoinscript():
    pass


if ucr.get_int('ucstest/sleep-during-import', 0) > 0:
    time.sleep(ucr.get_int('ucstest/sleep-during-import'))


class Instance(Base):

    def init(self):
        if ucr.get_int('ucstest/sleep-during-init', 0) > 0:
            time.sleep(ucr.get_int('ucstest/sleep-during-init'))

    @simple_response
    def respond(self):
        return True

    def norespond(self, request):
        pass

    @simple_response
    def non_threaded_traceback(self):
        raise NonThreadedError()

    @simple_response
    def threaded_traceback(self):
        def _throw_exception(_1, _2):
            raise ThreadedError()
        return _throw_exception

    @simple_response
    def umc_error_traceback(self):
        raise UMC_Error("This is an UMC Error")

    @simple_response
    def sleep(self, seconds=1):
        time.sleep(seconds)
        return True

    def traceback_as_thread_result(self, request):
        # UVMM uses this to pass-through traceback from internal umc calls to the frontend
        result = None
        try:
            raise ThreadedError()
        except ThreadedError:
            etype, result, _ = sys.exc_info()
            thread = FakeThread()
            thread.exc_info = (etype, result, None)
        self.thread_finished_callback(thread, result, request)

    def umc_error_as_thread_result(self, request):
        # UVMM uses this to pass-through traceback from internal umc calls to the frontend
        result = None
        try:
            raise UMC_Error("This is an UMC Error")
        except UMC_Error:
            etype, result, _ = sys.exc_info()
            thread = FakeThread()
            thread.exc_info = (etype, result, None)
        self.thread_finished_callback(thread, result, request)
