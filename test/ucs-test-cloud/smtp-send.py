#!/usr/bin/python
# vim:set expandtab shiftwidth=4 tabstop=4:
"""Put ucs-test result into email."""
import sys
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from ConfigParser import ConfigParser


def attach(msg, file_name):
    """Attach file to message."""
    file_part = open(file_name, 'rb')
    try:
        report = MIMEText(file_part.read())
    finally:
        file_part.close()
    report.add_header('Content-Disposition', 'attachment', filename=file_name)
    msg.attach(report)


def collect(base, from_addr, to_addr):
    """Collect xml reports and create MIME message."""
    msg = MIMEMultipart()
    msg['Subject'] = 'ucs-test'
    msg['From'] = from_addr
    msg['To'] = to_addr
    msg.preample = 'ucs-test results'

    for dirpath, dirnames, filenames in os.walk(base):
        for file_name in filenames:
            if not file_name.endswith('.xml'):
                continue
            path_name = os.path.join(dirpath, file_name)
            attach(msg, path_name)
        for dir_name in dirnames:
            if dir_name.startswith('.'):
                dirnames.remove(dir_name)
    return msg


def send(cfg, msg, from_addr, to_addr):
    """Send message 'msg' from 'from_addr' to 'to_addr'."""
    smtp = smtplib.SMTP(cfg.get('mail', 'smtp'))
    smtp.login(cfg.get('mail', 'username'), cfg.get('mail', 'password'))
    smtp.sendmail(from_addr, [to_addr], msg.as_string())
    smtp.quit()


def main():
    """Send test results via SMTP."""
    cfg = ConfigParser()
    cfg.read(os.path.expanduser('~/ucs-test.ini'))

    local, domain = cfg.get('mail', 'username').split('@', 1)
    from_addr = '%s+%s@%s' % (local, os.uname()[1], domain)
    to_addr = cfg.get('mail', 'username')

    msg = collect(cfg.get('test', 'dir'), from_addr, to_addr)
    for path_name in sys.argv[1:]:
        attach(msg, path_name)
    if False:
        print msg.as_string()
    else:
        send(cfg, msg, from_addr, to_addr)


if __name__ == '__main__':
    main()
