# -*- coding: utf-8 -*-

"""UCS installation via VNC"""

import logging
import os
import sys
import time
from argparse import ArgumentParser, Namespace
from contextlib import suppress
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from helper import trace_calls, verbose
from twisted.internet import reactor
from vncautomate import VNCAutomateFactory, init_logger
from vncautomate.config import OCRConfig
from vncdotool.api import ThreadedVNCClientProxy, connect
from vncdotool.client import VNCDoException


@verbose("sleep", "{0:.1f} {1}")
def sleep(seconds: float, msg: str = "") -> None:
    time.sleep(seconds)


def build_parser() -> ArgumentParser:
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


class VNCInstallation:

    def __init__(self, args: Namespace) -> None:
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
        self.translations = self.load_translation(self.args.language)
        self._client: Optional[ThreadedVNCClientProxy] = None
        self._stopping = False

    def load_translation(self, language: str) -> Dict[str, str]:
        return {}

    def translate(self, text: str) -> str:
        return self.translations.get(text) or text

    @property
    def client(self) -> ThreadedVNCClientProxy:
        if self._client is None:
            self._client = connect(
                self.args.vnc,
                factory_class=VNCAutomateFactory,
                timeout=self.timeout,
            )
            self._client.updateOCRConfig(self.config)
        return self._client

    def run(self) -> None:
        # https://docs.twisted.org/en/stable/core/howto/threading.html#running-code-in-threads
        reactor.addSystemEventTrigger("before", "shutdown", self._onShutdown)
        reactor.callInThread(self.runner)
        reactor.run()

    def _onShutdown(self) -> None:
        self._stopping = True

    def runner(self) -> None:
        ret = 0
        try:
            tracing = not sys.gettrace()
            if tracing:
                sys.settrace(trace_calls)
            self.main()
        except SystemExit as ex:
            if isinstance(ex.code, int):
                ret = ex.code
            elif ex.code is None:
                ret = 0
            else:
                ret = 1
        except Exception as ex:
            log = logging.getLogger(__name__)
            log.fatal(ex, exc_info=True)
            with suppress(VNCDoException):
                self.screenshot('error.png')
            os._exit(1)
        finally:
            if tracing:
                sys.settrace(None)
            if not self._stopping:
                reactor.callWhenRunning(reactor.stop)
        os._exit(ret)

    def main(self) -> None:
        raise NotImplementedError()

    def screenshot(self, filename: str) -> None:
        if not os.path.isdir(self.args.screenshot_dir):
            os.mkdir(self.args.screenshot_dir)
        screenshot_file = os.path.join(self.args.screenshot_dir, filename)
        self.client.captureScreen(screenshot_file)

    @verbose("click_on", "{1!r}")
    def click_on(self, text: str) -> None:
        translated = self.translate(text)
        self.client.timeout = self.timeout + 5
        self.client.mouseClickOnText(translated, timeout=self.timeout)

    @verbose("click_at", "{1},{2} {3}")
    def click_at(self, x: int, y: int, button: int = 1) -> None:
        self.client.mouseMove(x, y)
        self.client.mousePress(button)

    def text_is_visible(self, text: str, timeout: int = 0, wait: bool = True) -> bool:
        try:
            self.wait_for_text(text, timeout, wait)
            return True
        except VNCDoException:
            return False

    def wait_for_text(self, text: str, timeout: int = 0, wait: bool = True) -> None:
        translated = self.translate(text)
        timeout = self.timeout * (timeout >= 0) + abs(timeout)
        self.client.timeout = timeout + 5
        result: List[Tuple[int, int]] = []
        self.client.waitForText(translated, timeout, wait, result)
        if not result:
            raise VNCDoException()

    @verbose("type", "{1!r} clear={2}")
    def type(self, text: str, clear: bool = False) -> None:
        translated = self.translate(text)
        if self.config.dump_dir and "\n" in text:
            img_path = os.path.join(self.config.dump_dir, "vnc_automate_%s.png" % datetime.now().isoformat())
            self.client.captureScreen(img_path)
        time.sleep(1)
        if clear:
            self.clear_input()
        self.client.enterKeys(translated)

    def clear_input(self) -> None:
        self.client.keyPress('end')
        for _ in range(100):
            self.client.keyPress('bsp')
        time.sleep(3)

    def check_apipa(self) -> None:
        """Check automatic private address if no DHCP answer."""
        if self.text_is_visible('APIPA'):
            self.type("\n")
            sleep(60, "net.apipa")
