#!/usr/share/ucs-test/runner python3
## desc: Basic email functions
## tags: [apptest]
## exposure: dangerous
## packages: [univention-mail-server]

import socket
import subprocess
from time import sleep

import netifaces

import univention.testing.ucr as ucr_test
from univention.config_registry import handler_set
from univention.testing import utils


SMTP_PORT = 25


def get_ext_ip() -> str:
    for iface in netifaces.interfaces():
        if iface in {"lo"}:
            continue
        if iface.startswith(("docker", "veth")):
            continue
        addrs = netifaces.ifaddresses(iface)
        for rec in addrs.get(netifaces.AF_INET, []):
            addr = rec["addr"]
            print(f"iface={iface} addr={addr}")
            return addr
    raise ValueError("No usable IPv4 address found")


def reverse_dns_name(ip: str) -> str:
    reverse = ip.split('.')
    reverse.reverse()
    return '%s.in-addr.arpa' % '.'.join(reverse)


def print_header(section_string: str) -> None:
    print('info', 40 * '+', '\n%s\ninfo' % section_string, 40 * '+')


def create_bad_mailheader(fqdn: str, sender_ip: str, mailfrom: str, rcptto: str) -> None:
    def get_return_code(s: str) -> int:
        try:
            return int(s[:4])
        except ValueError:
            return -1

    def get_reply(s: socket.socket) -> str:
        buff_size = 1024
        reply = b''
        while True:
            part = s.recv(buff_size)
            reply += part
            if len(part) < buff_size:
                break
        return reply.decode('UTF-8')

    def send_message(s: socket.socket, message: str) -> None:
        print(f'OUT: {message!r}')
        s.send(b'%s\r\n' % (message.encode('UTF-8'),))

    def send_and_receive(s: socket.socket, message: str) -> int:
        send_message(s, message)
        reply = [reply.strip() for reply in get_reply(s).split('\n') if reply.strip()]
        r = get_return_code(reply[-1])
        for line in reply[:-1]:
            print(f'IN : {line!r}')
        print(f'IN : {reply[-1]!r} (return code: {r!r})')
        return r

    print(f'Connecting to {sender_ip}:{SMTP_PORT} (TCP)...')
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        for _ in range(3):
            try:
                s.connect((sender_ip, SMTP_PORT))
                break
            except ConnectionRefusedError:
                sleep(1)
        else:
            raise ConnectionRefusedError()

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
        send_message(s, 'QUIT')
    assert retval != 250


def main(ucr) -> None:
    fqdn = '%(hostname)s.%(domainname)s' % ucr
    sender_ip = get_ext_ip()

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
        ('%s@%s' % ('spambag', sender_ip), 'victim@mailinator.com', header0),
        ('%s@[%s]' % ('spambag', sender_ip), 'victim@mailinator.com', header0),
        ('%s@%s' % ('spambag', reverse_dns_name(sender_ip)), 'victim@mailinator.com', header0),

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
        create_bad_mailheader(fqdn, sender_ip, mailfrom, rcpt)


if __name__ == '__main__':
    with utils.AutoCallCommand(exit_cmd=["systemctl", "restart", "postfix.service"]), utils.AutoCallCommand(exit_cmd=["/usr/sbin/ucr", "commit", "/etc/postfix/main.cf"]), ucr_test.UCSTestConfigRegistry() as ucr:
        # disable postscreen to check postfix rules directly otherwise
        # connection might get dropped directly on first misbehaviour by postscreen.
        print('Disabling postscreen during tests...')
        handler_set(['mail/postfix/postscreen/enabled=no'])
        subprocess.call(["systemctl", "restart", "postfix.service"])
        print('postscreen disabled. Starting tests...')
        main(ucr)
