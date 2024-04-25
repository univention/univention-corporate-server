import passlib.hash
import pytest

import univention.testing.strings as uts
import univention.testing.udm as udm_test


@pytest.fixture(scope="session")
def rad_user(udm_session, ucr_session):
    password = uts.random_string()
    dn, name = udm_session.create_user(networkAccess=1, password=password, birthday='2001-01-01')
    return dn, name, password


@pytest.fixture(scope="session")
def udm_session():
    with udm_test.UCSTestUDM() as udm:
        yield udm


@pytest.fixture()
def ssp():
    password = uts.random_string().encode('utf-8')
    nt = passlib.hash.nthash.hash(password).upper().encode('utf-8')
    return password, nt
