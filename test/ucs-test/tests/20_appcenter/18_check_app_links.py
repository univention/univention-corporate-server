#!/usr/share/ucs-test/runner python3
## desc: Check that links in the .ini files do not return errors when accessed.
## roles: [domaincontroller_master]
## tags: [basic, apptest]
## bugs: [37717, 37950]
## packages: [univention-management-console-module-appcenter]
## exposure: careful

import glob
import re
import time
from html.parser import HTMLParser

import requests

from univention.testing import utils

from appcentertest import get_requested_apps


# taken from https://mail.python.org/pipermail/tutor/2002-September/017228.html
urls = '(?: %s)' % '|'.join("http https telnet gopher file wais ftp".split())
ltrs = r'\w'
gunk = r'/#~:.?+=&%@!\-'
punc = r'.:?\-'
anyl = "%(ltrs)s%(gunk)s%(punc)s" % {
    'ltrs': ltrs,
    'gunk': gunk,
    'punc': punc,
}

url = r"""
    \b                            # start at word boundary
        %(urls)s    :             # need resource and a colon
        [%(anyl)s]  +?            # followed by one or more
                                  #  of any valid character, but
                                  #  be conservative and take only
                                  #  what you need to....
    (?=                           # look-ahead non-consumptive assertion
            [%(punc)s]*           # either 0 or more punctuation
            (?:   [^%(anyl)s]     #  followed by a non-url char
                |                 #   or end of the string
                  $
            )
    )
    """ % {'urls': urls,
           'anyl': anyl,
           'punc': punc}

url_re = re.compile(url, re.VERBOSE | re.MULTILINE)

# these links return 403 -> Bug #39730
forbidden_links = {}
forbidden_links['https://univention.ikarus.at/index-en.php'] = True
forbidden_links['https://univention.ikarus.at/index.php'] = True
forbidden_links['http://download.siouxapp.com/redirect/ucs-appcenter/appvendor.html'] = True
forbidden_links['http://www.cloudssky.com/en/support/opencms/index.html'] = True
forbidden_links['http://cloudssky.com/en/solutions/index.html'] = True
forbidden_links['http://www.cloudssky.com'] = True
forbidden_links['https://$DASHBOARD_SERVER/metrics-prometheus/graph'] = True

README_FILES = [
    'README',
    'README_INSTALL',
    'README_POST_INSTALL',
    'README_UPDATE',
    'README_POST_UPDATE',
    'README_UNINSTALL',
    'README_POST_UNINSTALL',
]


class MyHTMLParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.href = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href":
                    self.href.append(value)


def findall_urls_from_readme(app):
    """Readme files are html snippets, check with html parser"""
    files_to_check = []
    all_urls = {}
    for readme_file in README_FILES:
        for f in glob.glob('%s*' % app.get_cache_file(readme_file)):
            files_to_check.append(f)  # noqa: PERF402
    for filename in files_to_check:
        print("\nChecking file:", filename)
        parser = MyHTMLParser()
        try:
            with open(filename) as fd:
                html = fd.read()
                parser.feed(html)
                for url in parser.href:
                    if 'http://' in url or 'https://' in url:
                        print('found URL - %s' % url)
                        if all_urls.get(url):
                            all_urls[url].append(filename)
                        else:
                            all_urls[url] = [filename]
        except OSError as exc:
            utils.fail("An %r error occurred while working with %s" % (exc, filename))
    return all_urls


def findall_urls_from_ini(app):
    all_urls = {}
    files_to_check = [app.get_ini_file()]
    for filename in files_to_check:
        print("\nChecking file:", filename)
        try:
            with open(filename) as ini_file:
                for line in ini_file:
                    if not line.startswith('#'):
                        url = url_re.findall(line)
                        for u in url:
                            print('found URL - %s' % u)
                            u = re.sub(r'<[^>]+>', '', u)
                            if all_urls.get(u):
                                all_urls[u].append(filename)
                            else:
                                all_urls[u] = [filename]
        except OSError as exc:
            utils.fail("An %r error occurred while working with %s" % (exc, filename))
    return all_urls


def check_files():
    """
    Collects all links from .inis and Readmes of installed Apps;
    Tries to open each URL found using urlopen with a timeout.
    """
    links = {}
    for app in get_requested_apps():
        print("\nChecking App:", app)
        links[app.id] = findall_urls_from_ini(app)
        links[app.id].update(findall_urls_from_readme(app))
    bad_links = []
    for app in links:
        for link in links[app]:
            if link in forbidden_links:
                print("Ignore link:", link)
                continue
            time.sleep(1)
            print("Checking link:", link)
            requests_timeout = 10
            headers = requests.utils.default_headers()
            headers.update({'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:59.0) Gecko/20100101 Firefox/59.0'})
            try:
                r = requests.get(link, timeout=requests_timeout, verify=False, headers=headers)  # noqa: S501
            except Exception as exc:
                print("Response code indicates a problem. %s" % str(exc))
                bad_links.append(f'Link: {link} App: {app} File: {links[app][link]}')
                continue
            print(r.status_code)
            if str(r.status_code).startswith(('4', '5')):
                print("Response code indicates a problem.")
                bad_links.append(f'Link: {link} App: {app} File: {links[app][link]}')
    return bad_links


if __name__ == '__main__':
    # skip the test if there are no Apps (in 'APPCENTER_FILE'):
    bad_links = check_files()
    if bad_links:
        utils.fail("Problematic links are: \n\t* %s" % ('\n\t* '.join(bad_links)))
    else:
        print("\nNo errors were detected.\n")
