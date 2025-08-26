#
# UCS test
#
# SPDX-FileCopyrightText: 2013-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


import os
import pwd
import subprocess
import sys
import time
from types import TracebackType
from typing import Self


class MailSinkGuard:
    """
    This class is a simple context manager that stops all attached mail sinks
    if the context is left.

    with MaiLSinkGuard() as msg:
            sink = MailSink(......)
            msg.add(sink)
            ....use sink....
    """

    def __init__(self) -> None:
        self.mail_sinks: set[MailSink] = set()

    def add(self, sink: 'MailSink') -> None:
        self.mail_sinks.add(sink)

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, etraceback: TracebackType | None) -> None:
        for mail_sink in self.mail_sinks:
            mail_sink.stop()


class MailSink:
    """
    This class starts an SMTP sink on the specified address/port.
    Each incoming mail will be written to a single file if target_dir is used.
    To write all incoming mails into one file, use filename.

    >>> ms = MailSink('127.0.0.1', 12345, target_dir='/tmp/')
    >>> ms.start()
    <do some stuff>
    >>> ms.stop()

    >>> ms = MailSink('127.0.0.1', 12345, filename='/tmp/sinkfile.eml')
    >>> ms.start()
    <do some stuff>
    >>> ms.stop()

    >>> with MailSink('127.0.0.1', 12345, filename='/tmp/sinkfile.eml') as ms:
    >>>     <do some stuff>
    """

    def __init__(self, address: str, port: int, filename: str | None = None, target_dir: str | None = None, fqdn: str | None = None) -> None:
        self.address = address
        self.port = port
        self.filename = filename
        self.target_dir = target_dir
        self.process: subprocess.Popen | None = None
        self.fqdn = fqdn

    def __enter__(self) -> Self:
        self.start()
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_value: BaseException | None, etraceback: TracebackType | None) -> None:
        self.stop()

    def start(self) -> None:
        print(f'*** Starting SMTPSink at {self.address}:{self.port}')
        cmd = ['/usr/sbin/smtp-sink']  # use postfix' smtp-sink tool
        if self.filename is not None:
            cmd.extend(['-D', self.filename])
        elif self.target_dir is not None:
            cmd.extend(['-d', os.path.join(self.target_dir, '%Y%m%d-%H%M%S.')])
        else:
            cmd.extend(['-d', os.path.join('./%Y%m%d-%H%M%S.')])
        if self.fqdn:
            cmd.extend(['-h', self.fqdn])
        if os.geteuid() == 0:
            cmd.extend(['-u', pwd.getpwuid(os.getuid()).pw_name])
        cmd.append(f'{self.address}:{self.port}')
        cmd.append('10')
        print(f'*** {cmd!r}')
        self.process = subprocess.Popen(cmd, stderr=sys.stdout, stdout=sys.stdout)

    def stop(self) -> None:
        if self.process is not None:
            self.process.terminate()
            time.sleep(1)
            self.process.kill()
            print(f'*** SMTPSink at {self.address}:{self.port} stopped')
            self.process = None


if __name__ == '__main__':
    # ms = MailSink('127.0.0.1', 12345, target_dir='/tmp/')
    ms = MailSink('127.0.0.1', 12345, filename='/tmp/sink.eml')
    print('Starting sink')
    ms.start()
    print('Waiting')
    time.sleep(25)
    print('Stopping sink')
    ms.stop()
    print('Waiting')
    time.sleep(5)
