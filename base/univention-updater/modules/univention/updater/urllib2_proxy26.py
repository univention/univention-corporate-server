from urllib2 import *

# /usr/lib/python2.6/urllib.py (C) PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
def proxy_bypass_environment(host):
    """Test if proxies should not be used for a particular host.

    Checks the environment for a variable named no_proxy, which should
    be a list of DNS suffixes separated by commas, or '*' for all hosts.
    """
    no_proxy = os.environ.get('no_proxy', '') or os.environ.get('NO_PROXY', '')
    # '*' is special case for always bypass
    if no_proxy == '*':
        return 1
    # strip port off host
    hostonly, port = splitport(host)
    # check if the host ends with any of the DNS suffixes
    for name in no_proxy.split(','):
        if name and (hostonly.endswith(name) or host.endswith(name)):
            return 1
    # otherwise, don't bypass
    return 0
proxy_bypass = proxy_bypass_environment

# /usr/lib/python2.6/urllib2.py (C) PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
def _parse_proxy(proxy):
    """Return (scheme, user, password, host/port) given a URL or an authority.

    If a URL is supplied, it must have an authority (host:port) component.
    According to RFC 3986, having an authority component means the URL must
    have two slashes after the scheme:

    >>> _parse_proxy('file:/ftp.example.com/')
    Traceback (most recent call last):
    ValueError: proxy URL with no authority: 'file:/ftp.example.com/'

    The first three items of the returned tuple may be None.

    Examples of authority parsing:

    >>> _parse_proxy('proxy.example.com')
    (None, None, None, 'proxy.example.com')
    >>> _parse_proxy('proxy.example.com:3128')
    (None, None, None, 'proxy.example.com:3128')

    The authority component may optionally include userinfo (assumed to be
    username:password):

    >>> _parse_proxy('joe:password@proxy.example.com')
    (None, 'joe', 'password', 'proxy.example.com')
    >>> _parse_proxy('joe:password@proxy.example.com:3128')
    (None, 'joe', 'password', 'proxy.example.com:3128')

    Same examples, but with URLs instead:

    >>> _parse_proxy('http://proxy.example.com/')
    ('http', None, None, 'proxy.example.com')
    >>> _parse_proxy('http://proxy.example.com:3128/')
    ('http', None, None, 'proxy.example.com:3128')
    >>> _parse_proxy('http://joe:password@proxy.example.com/')
    ('http', 'joe', 'password', 'proxy.example.com')
    >>> _parse_proxy('http://joe:password@proxy.example.com:3128')
    ('http', 'joe', 'password', 'proxy.example.com:3128')

    Everything after the authority is ignored:

    >>> _parse_proxy('ftp://joe:password@proxy.example.com/rubbish:3128')
    ('ftp', 'joe', 'password', 'proxy.example.com')

    Test for no trailing '/' case:

    >>> _parse_proxy('http://joe:password@proxy.example.com')
    ('http', 'joe', 'password', 'proxy.example.com')

    """
    scheme, r_scheme = splittype(proxy)
    if not r_scheme.startswith("/"):
        # authority
        scheme = None
        authority = proxy
    else:
        # URL
        if not r_scheme.startswith("//"):
            raise ValueError("proxy URL with no authority: %r" % proxy)
        # We have an authority, so for RFC 3986-compliant URLs (by ss 3.
        # and 3.3.), path is empty or starts with '/'
        end = r_scheme.find("/", 2)
        if end == -1:
            end = None
        authority = r_scheme[2:end]
    userinfo, hostport = splituser(authority)
    if userinfo is not None:
        user, password = splitpasswd(userinfo)
    else:
        user = password = None
    return scheme, user, password, hostport

class ProxyHandler(ProxyHandler):
    # Proxies must be in front
    handler_order = 100

    def __init__(self, proxies=None):
        if proxies is None:
            proxies = getproxies()
        assert hasattr(proxies, 'has_key'), "proxies must be a mapping"
        self.proxies = proxies
        for type, url in proxies.items():
            setattr(self, '%s_open' % type,
                    lambda r, proxy=url, type=type, meth=self.proxy_open: \
                    meth(r, proxy, type))

    def proxy_open(self, req, proxy, type):
        orig_type = req.get_type()
        proxy_type, user, password, hostport = _parse_proxy(proxy)

        if proxy_type is None:
            proxy_type = orig_type

        if req.host and proxy_bypass(req.host):
            return None

        if user and password:
            user_pass = '%s:%s' % (unquote(user), unquote(password))
            creds = base64.b64encode(user_pass).strip()
            req.add_header('Proxy-authorization', 'Basic ' + creds)
        hostport = unquote(hostport)
        req.set_proxy(hostport, proxy_type)

        if orig_type == proxy_type or orig_type == 'https':
            # let other handlers take care of it
            return None
        else:
            # need to start over, because the other handlers don't
            # grok the proxy's URL type
            # e.g. if we have a constructor arg proxies like so:
            # {'http': 'ftp://proxy.example.com'}, we may end up turning
            # a request for http://acme.example.com/a into one for
            # ftp://proxy.example.com/a
            return self.parent.open(req, timeout=req.timeout)
