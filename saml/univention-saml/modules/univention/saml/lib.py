from __future__ import annotations, print_function

import os
import sys
import typing  # noqa: F401
from urllib.parse import urlparse

from univention.config_registry import ConfigRegistry  # noqa: F401


def get_idps(ucr: ConfigRegistry, log_fd: typing.TextIO | None=sys.stderr) -> None:

    def __get_supplement(key):
        return key.replace(idp_supplement_keybase, '')

    def __is_enabled_supplement(key, value):
        return key.startswith(idp_supplement_keybase) and ucr.is_true(value=value)

    def __is_valid_supplement(supplement):
        return supplement not in supplement_blacklist and '/' not in supplement

    def __get_supplement_entityID(supplement):
        if urlparse(main_entityID).path.startswith(f'/{main_basepath}/'):
            return main_entityID.replace(
                f'/{main_basepath}/',
                f'/{main_basepath}/{supplement}/',
            )
        else:
            print('Unknown default entity ID format, using fallback for supplement entity IDs', file=log_fd)
            return main_entityID + f'/{supplement}'

    def __get_supplement_basepath(supplement):
        return os.path.join(main_basepath, supplement)

    def __get_supplement_baseurl(supplement):
        return os.path.join(sso_fqdn, __get_supplement_basepath(supplement))

    supplement_blacklist = (os.listdir('/usr/share/simplesamlphp/www/'))
    main_basepath = 'simplesamlphp'
    sso_fqdn = ucr.get('ucs/server/sso/fqdn', f'{"ucs-sso"}.{ucr.get("domainname")}')
    main_entityID = ucr.get('saml/idp/entityID', f'https://{sso_fqdn}/{main_basepath}/saml2/idp/metadata.php')
    idp_supplement_keybase = 'saml/idp/entityID/supplement/'
    idp_supplements = (__get_supplement(key) for key, value in ucr.items() if __is_enabled_supplement(key, value))
    entityIDs = [{
        'entityID': main_entityID,
        'basepath': main_basepath,
        'baseurl': '__DEFAULT__',
    }]
    for idp_supplement in idp_supplements:
        if __is_valid_supplement(idp_supplement):
            supplement_entityID = __get_supplement_entityID(idp_supplement)
            entityIDs.append({
                'entityID': supplement_entityID,
                'basepath': __get_supplement_basepath(idp_supplement),
                'baseurl': __get_supplement_baseurl(idp_supplement),
            })
        else:
            print(f'"{idp_supplement}" is not a valid entity id supplement. Ignoring.', file=log_fd)
    return entityIDs


def _decode(x: bytes | str) -> str:
    return x.decode('ASCII') if isinstance(x, bytes) else x


def escape_php_string(string: str) -> str:
    return string.replace('\x00', '').replace("\\", "\\\\").replace("'", r"\'")


def php_string(string: str) -> str:
    return "'%s'" % (escape_php_string(_decode(string)),)


def php_array(list_: typing.List[str]) -> str:
    if not list_:
        return 'array()'
    return "array('%s')" % "', '".join(escape_php_string(_decode(x).strip()) for x in list_)


def php_bool(bool_: str) -> str:
    bool_ = _decode(bool_)
    mapped = {
        'true': True,
        '1': True,
        'false': False,
        '0': False,
    }.get(bool_.lower())
    if mapped is None:
        raise TypeError(f'Not a PHP bool: {bool_}')
    return 'true' if mapped else 'false'
