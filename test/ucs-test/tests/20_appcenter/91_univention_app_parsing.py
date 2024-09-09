#!/usr/share/ucs-test/runner python3
## desc: Parsing of CLI univention-app
## packages:
##   - univention-appcenter
## exposure: safe
## bugs: [57546]
## tags: [appcenter]

import importlib.machinery
import importlib.util


univention_app_loader = importlib.machinery.SourceFileLoader('univention_app', '/usr/bin/univention-app')
univention_app_spec = importlib.util.spec_from_loader('univention_app', univention_app_loader)
univention_app = importlib.util.module_from_spec(univention_app_spec)
univention_app_loader.exec_module(univention_app)


def test_configure_set_unset():
    parser = univention_app._setup_argparse()
    namespace = parser.parse_args(['configure', 'keycloak', '--set', 'a=b', 'c=d', '--set', 'e=f'])
    assert namespace.set_vars == {'a': 'b', 'c': 'd', 'e': 'f'}, namespace.set_vars

    namespace = parser.parse_args(['configure', 'keycloak', '--unset', 'a', 'b', '--unset', 'c'])
    assert namespace.unset == [['a', 'b'], ['c']], namespace.unset


if __name__ == '__main__':
    test_configure_set_unset()
