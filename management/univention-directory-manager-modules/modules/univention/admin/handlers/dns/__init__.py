# vim: set fileencoding=utf-8 et sw=4 ts=4 :

ARPA_IP4 = '.in-addr.arpa'
ARPA_IP6 = '.ip6.arpa'

def makeContactPerson(obj, arg):
    """Create contact Email-address for domain."""
    domain = obj.position.getDomain()
    return 'root@%s.' % (domain.replace('dc=', '').replace(',','.'),)

def unescapeSOAemail(email):
    r"""
    Un-escape Email-address from DNS SOA record.
    >>> unescapeSOAemail(r'first\.last.domain.tld')
    'first.last@domain.tld'
    """
    ret = ''
    i = 0
    while i < len(email):
        if email[i] == '\\':
            i += 1
            if i >= len(email):
                raise ValueError()
        elif email[i] == '.':
            i += 1
            if i >= len(email):
                raise ValueError()
            ret += '@'
            ret += email[i:]
            return ret
        ret += email[i]
        i += 1
    raise ValueError()

def escapeSOAemail(email):
    r"""
    Escape Email-address for DNS SOA record.
    >>> escapeSOAemail('first.last@domain.tld')
    'first\\.last.domain.tld'
    """
    SPECIAL_CHARACTERS = set('"(),.:;<>@[\\]')
    if not '@' in email:
        raise ValueError()
    (local, domain) = email.rsplit('@', 1)
    tmp = ''
    for c in local:
        if c in SPECIAL_CHARACTERS:
            tmp += '\\'
        tmp += c
    local = tmp
    return local + '.' + domain

if __name__ == '__main__':
    import doctest
    doctest.testmod()
