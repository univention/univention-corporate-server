#!/usr/bin/python2.7 -u
# -*- coding: utf-8 -*-

"""UCS installation via VNC"""

import os
import sys
import time
from argparse import ArgumentParser, Namespace  # noqa: F401

from helper import trace_calls, verbose
from vncautomate import VNCConnection, init_logger
from vncautomate.config import OCRConfig
from vncdotool.api import VNCDoException


@verbose("sleep", "{0:.1f} {1}")
def sleep(seconds, msg=""):  # type: (float, str) -> None
    time.sleep(seconds)


def build_parser():  # type: () -> ArgumentParser
    parser = ArgumentParser(add_help=False)
    parser.add_argument(
        '--screenshot-dir',
        default='./screenshots',
        help="Directory for storing screenshots",
        metavar="DIR",
    )

    group = parser.add_argument_group("Debugging")
    group.add_argument(
        "--logging", "-l",
        default="info",
        choices=("critical", "error", "warning", "info", "debug"),
        help="Set debug level",
    )
    group.add_argument(
        "--debug-boxes",
        default=OCRConfig.dump_boxes,
        help=OCRConfig._dump_boxes,
        metavar="FILE",
    )
    group.add_argument(
        "--debug-screen",
        default=OCRConfig.dump_screen,
        help=OCRConfig._dump_screen,
        metavar="FILE",
    )
    group.add_argument(
        "--debug-gradients-x",
        default=OCRConfig.dump_x_gradients,
        help=OCRConfig._dump_y_gradients,
        metavar="FILE",
    )
    group.add_argument(
        "--debug-gradients-y",
        default=OCRConfig.dump_y_gradients,
        help=OCRConfig._dump_y_gradients,
        metavar="FILE",
    )
    group.add_argument(
        "--debug-dir",
        default=OCRConfig.dump_dir,
        help=OCRConfig._dump_dir,
        metavar="DIR",
    )

    group = parser.add_argument_group("Virtual machine settings")
    group.add_argument(
        '--vnc',
        required=True,
        help="VNC screen to connect to",
    )

    group = parser.add_argument_group("Host settings")
    group.add_argument(
        '--fqdn',
        default='master.ucs.test',
        help="Fully qualified host name to use",
    )
    group.add_argument(
        '--password',
        default='univention',
        help="Password to setup for user 'root' and/or 'Administrator'",
    )
    group.add_argument(
        '--organisation',
        default='ucs',
        help="Oranisation name to setup",
    )

    group = parser.add_argument_group("Join settings")
    group.add_argument(
        '--dns',
        help="DNS server of UCS domain",
    )
    group.add_argument(
        '--join-user',
        help="User name for UCS domain join",
    )
    group.add_argument(
        '--join-password',
        help="Password for UCS domain join",
    )

    return parser


class VNCInstallation(object):

    def __init__(self, args):  # type: (Namespace) -> None
        # see https://github.com/tesseract-ocr/tesseract/issues/2611
        os.environ['OMP_THREAD_LIMIT'] = '1'
        init_logger(args.logging)
        self.args = args
        self.config = OCRConfig(
            lang=args.language,
            dump_boxes=args.debug_boxes,
            dump_screen=args.debug_screen,
            dump_x_gradients=args.debug_gradients_x,
            dump_y_gradients=args.debug_gradients_y,
            dump_dir=args.debug_dir,
        )
        self.timeout = 120
        self.setup_finish_sleep = 900
        self.connect()
        self._ = self.load_translation(self.args.language)

    def load_translation(self, language: str) -> Dict[str, str]:
        return {}

    def run(self):  # type: () -> None
        try:
            tracing = not sys.gettrace()
            if tracing:
                sys.settrace(trace_calls)
            self.main()
        except Exception:
            self.connect()
            self.screenshot('error.png')
            raise
        finally:
            if tracing:
                sys.settrace(None)

    def main(self):  # type: () -> None
        raise NotImplementedError()

    def connect(self):  # type: () -> None
        self.conn = VNCConnection(self.args.vnc)
        self.client = self.conn.__enter__()
        self.client.updateOCRConfig(self.config)

    def screenshot(self, filename):  # type: (str) -> None
        if not os.path.isdir(self.args.screenshot_dir):
            os.mkdir(self.args.screenshot_dir)
        screenshot_file = os.path.join(self.args.screenshot_dir, filename)
        self.client.captureScreen(screenshot_file)

    @verbose("click_on", "{1!r}")
    def click_on(self, text):  # type: (str) -> None
        self.client.waitForText(text, timeout=self.timeout)
        self.client.mouseClickOnText(text)

    def text_is_visible(self, text, timeout=120):  # type: (str, int) -> bool
        try:
            self.client.waitForText(text, timeout=timeout)
            return True
        except VNCDoException:
            self.connect()
            return False

    def clear_input(self):  # type: () -> None
        self.client.keyPress('end')
        for _ in range(100):
            self.client.keyPress('bsp')
        time.sleep(3)

    def check_apipa(self):  # type: () -> None
        """Check automatic private address if no DHCP answer."""
        try:
            self.client.waitForText('APIPA', timeout=self.timeout)
            self.client.keyPress('enter')
            sleep(60, "net.apipa")
        except VNCDoException:
            self.connect()
