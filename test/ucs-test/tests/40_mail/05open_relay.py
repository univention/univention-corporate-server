#!/usr/share/ucs-test/runner python3
## desc: Basic email functions
## tags: [apptest]
## exposure: dangerous
## packages: [univention-mail-server]
## bugs: []

import socket
import subprocess

import netifaces

import univention.testing.ucr as ucr_test
from univention.config_registry import handler_set
from univention.testing import utils


def get_ext_ip():
    ifaces = netifaces.interfaces()
    print(f'interfaces: {ifaces!r}')
    ifaces = [i for i in ifaces if i not in ('docker', 'docker0', 'lo') and not i.startswith('veth')]
    # ignore ipv6 only
    ifaces = [netifaces.ifaddresses(iface)[netifaces.AF_INET] for iface in ifaces if netifaces.AF_INET in netifaces.ifaddresses(iface)]
    print(f'ifaces: {ifaces!r}')
    ifaces = ifaces[0]
    addrs = [i['addr'] for i in ifaces]
    print(f'addrs: {addrs!r}')
    return addrs[0]


def reverse_dns_name(ip):
    reverse = ip.split('.')
    reverse.reverse()
    return '%s.in-addr.arpa' % '.'.join(reverse)


def print_header(section_string):
    print('info', 40 * '+', '\n%s\ninfo' % section_string, 40 * '+')


ucr = ucr_test.UCSTestConfigRegistry()
ucr.load()
fqdn = '{}.{}'.format(ucr['hostname'], ucr['domainname'])
sender_ip = get_ext_ip()
smtp_port = 25


def create_bad_mailheader(mailfrom, rcptto):

    def get_return_code(s):
        try:
            return int(s[:4])
        except ValueError:
            return -1

    def get_reply(s):
        buff_size = 1024
        reply = ''
        while True:
            part = s.recv(buff_size).decode('UTf-8')
            reply += part
            if len(part) < buff_size:
                break
        return reply

    def send_message(s, message):
        print(f'OUT: {message!r}')
        s.send(b'%s\r\n' % (message.encode('UTF-8'),))

    def send_and_receive(s, message):
        send_message(s, message)
        reply = [reply.strip() for reply in get_reply(s).split('\n') if reply.strip()]
        r = get_return_code(reply[-1])
        for line in reply[:-1]:
            print(f'IN : {line!r}')
        print(f'IN : {reply[-1]!r} (return code: {r!r})')
        return r

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((sender_ip, smtp_port))
    s.settimeout(0.2)
    reply = get_reply(s)
    r = get_return_code(reply)
    print(f'IN : {reply!r} (return code: {r!r})')
    send_and_receive(s, 'EHLO %s' % fqdn)
    if mailfrom:
        send_and_receive(s, 'MAIL FROM: %s' % mailfrom)
    send_and_receive(s, 'RCPT TO: %s' % rcptto)
    send_and_receive(s, 'DATA')
    send_and_receive(s, 'SPAMBODY')
    retval = send_and_receive(s, '.')
    send_and_receive(s, 'QUIT')
    s.close()

    if retval == 250:
        return 0
    else:
        return 1


def main():
    header0 = "The classic open-relay test:"
    header1 = "The classic open-relay test with the \"\" (Sendmail 8.8 and others MTAs, much used by the spammers):"
    header2 = "The non-RFC821 compliant test (MS Exchange and SLmail betas):"
    header3 = "No sender-domain vulnerability (Post.Office, Intermail and Sendmail 8.8 misconfigurated):"
    header4 = "A heavily exploited vulnerability (Lotus Notes/Domino, Novell Groupwise, badly secured Sendmails and others):"
    header5 = "A variation of the vulnerability above (using @ instead %, but less popular among spammers):"
    header6 = "Mixed UUCP and Internet addressing (common with Sendmails with FEATURE(nouucp) set):"
    header7 = "A heavily exploited vulnerability using the ':' character:"
    header8 = "An old UUCP style vulnerability:"
    header9 = "NULL sender vulnerability:"

    test_cases = [
        ('%s@%s' % ('spambag', get_ext_ip()), 'victim@mailinator.com', header0),
        ('%s@[%s]' % ('spambag', get_ext_ip()), 'victim@mailinator.com', header0),
        ('%s@%s' % ('spambag', reverse_dns_name(get_ext_ip())), 'victim@mailinator.com', header0),

        ("spambag@mailinator.com", "victim@mailinator.com", header1),

        ("spambag@mailinator.com", "victim@mailinator.com", header2),

        ("spambag", "victim@mailinator.com", header3),

        ("spambag@mailinator.com", "victim%mailinator.com@$SENDERIP", header4),
        ("spambag@mailinator.com", "victim%mailinator.com@[$SENDERIP]", header4),
        ("spambag@mailinator.com", "victim%mailinator.com@$REVERSENAME", header4),

        ("spambag@mailinator.com", "victim@mailinator.com@$SENDERIP", header5),
        ("spambag@mailinator.com", "victim@mailinator.com@[$SENDERIP]", header5),
        ("spambag@mailinator.com", "victim@mailinator.com@$REVERSENAME", header5),

        ("spambag@mailinator.com", "mailinator.com!victim@$SENDERIP", header6),
        ("spambag@mailinator.com", "mailinator.com!victim@[$SENDERIP]", header6),
        ("spambag@mailinator.com", "mailinator.com!victim@$REVERSENAME", header6),

        ("spambag@mailinator.com", "@$SENDERIP:victim@mailinator.com", header7),
        ("spambag@mailinator.com", "@[$SENDERIP]:victim@mailinator.com", header7),
        ("spambag@mailinator.com", "@$REVERSENAME:victim@mailinator.com", header7),

        ("spambag@mailinator.com", "mailinator.com!victim", header8),

        ("", "victim@mailinator.com", header9),
        ("<>", "victim@mailinator.com", header9),
    ]

    for (mailfrom, rcpt, header) in test_cases:
        print_header(header)
        if create_bad_mailheader(mailfrom, rcpt) != 1:
            utils.fail('*** Open relay found ***')


if __name__ == '__main__':
    main()
