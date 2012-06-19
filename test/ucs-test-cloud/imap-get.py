#!/usr/bin/python
# vim:set expandtab shiftwidth=4 tabstop=4:
"""Fetch ucs-test result mails from IMAP account and pass to Jenkins."""
import sys
import os
import imaplib
import email
import errno
from ConfigParser import ConfigParser
from optparse import OptionParser


def unpack(msg, output_dir):
    """Unpack attachmants to local directory."""
    try:
        os.makedirs(output_dir)
    except OSError, ex:
        if ex.errno != errno.EEXIST:
            raise
    for part in email.iterators.typed_subpart_iterator(msg, 'text'):
        if part.get_content_maintype() == 'multipart':
            continue
        filename = part.get_filename()
        if not filename:
            print >> sys.stderr, 'Skipping part...'
            continue
        path_name = os.path.join(output_dir, filename)
        if not os.path.abspath(output_dir) < os.path.abspath(path_name):
            print >> sys.stderr, 'Skipping because of directory traversal...'
            continue
        dirname = os.path.dirname(path_name)
        try:
            os.makedirs(dirname)
        except OSError, ex:
            if ex.errno != errno.EEXIST:
                raise
        file_part = open(path_name, 'w')
        try:
            file_part.write(part.get_payload(decode=True))
        finally:
            file_part.close()


def fetch(host, username, password, outdir=None, limit=1<<16):
    """Fetch all messages from IMAP."""
    found = False
    imap = imaplib.IMAP4(host)
    typ, data = imap.login(username, password)
    # ('OK', ['LOGIN completed'])
    assert typ == 'OK'
    try:
        typ, data = imap.select()
        # ('OK', ['1'])
        assert typ == 'OK'
        try:
            # msg_count = int(data[0])

            typ, data = imap.search(None, 'ALL')
            # ('OK', ...)
            assert typ == 'OK'

            for num in data[0].split():
                if outdir is None:
                    return True
                found = True
                typ, data = imap.fetch(num, '(RFC822)')
                # [('1 (RFC822 {3967}', '...')]
                assert typ == 'OK'

                text = data[0][1]
                msg = email.message_from_string(text)
                unpack(msg, os.path.join(outdir, '%s' % (num,)))
                imap.store(num, '+FLAGS', '\\Deleted')
                limit -= 1
                if limit <= 0:
                    break
        finally:
            typ, data = imap.close()
            # ('OK', ['CLOSE completed'])
            # assert typ == 'OK'
    finally:
        imap.logout()
    return found


def main():
    """Check or fetch imaps from IMAP."""
    cfg = ConfigParser()
    cfg.read(os.path.expanduser('~/ucs-test.ini'))

    host = cfg.get('mail', 'imap')
    username = cfg.get('mail', 'username')
    password = cfg.get('mail', 'password')
    outdir = cfg.get('test', 'dir')

    parser = OptionParser()
    parser.add_option('-c', '--check',
            dest='check', action='store_true', default=False,
            help='Check for new mail only')
    parser.add_option('-l', '--limit',
            dest='limit', action='store', type='int', default=1,
            help='Limit number of mails to fetch')
    options, args = parser.parse_args()
    if args:
        print >> sys.stderr, 'Optional arguments are ignored: %r' % (args,)
        sys.exit(2)
    if options.check:
        outdir = None

    if fetch(host, username, password, outdir, limit=options.limit):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()
