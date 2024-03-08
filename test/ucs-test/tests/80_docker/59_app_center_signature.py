#!/usr/share/ucs-test/runner pytest-3 -s -l -vv
## desc: Verify the signature implementation
## tags: [docker]
## exposure: dangerous
## packages:
##   - docker.io

import os
from subprocess import call

import pytest

from univention.config_registry import ConfigRegistry, handler_set
from univention.testing.utils import fail

from dockertest import Appcenter


class SyncedAppcenter(Appcenter):
    def __init__(self):
        Appcenter.__init__(self)
        self.vv = self.ucr.get('version/version')
        self.all_versions = ['4.4', '5.0', '5.1']
        self.upstream_appcenter = 'https://appcenter.software-univention.de'
        handler_set([
            'appcenter/index/verify=true',
        ])

    def reset_local_cache(self):
        handler_set([
            'repository/app_center/server=%s' % (self.upstream_appcenter),
        ])
        call('univention-app update', shell=True)
        handler_set([
            'repository/app_center/server=http://%(hostname)s.%(domainname)s' % self.ucr,
        ])

    def download(self, f):
        if os.path.exists('/var/www/%s' % f):
            os.remove('/var/www/%s' % f)

        d = os.path.dirname(f'/var/www/{f}')
        if not os.path.exists(d):
            os.makedirs(d)

        call('wget -O /var/www/%s %s/%s' % (f, self.upstream_appcenter, f), shell=True)

    def download_index_json(self):
        for version in self.all_versions:
            self.download(f'meta-inf/{version}/index.json.gz')
            self.download(f'meta-inf/{version}/all.tar.zsync')
            self.download(f'meta-inf/{version}/all.tar.gz')

    def download_index_json_gpg(self):
        for version in self.all_versions:
            self.download(f'meta-inf/{version}/index.json.gz.gpg')
            self.download(f'meta-inf/{version}/all.tar.gpg')

    def remove_from_cache(self, f):
        if os.path.exists(os.path.join('/var/cache/univention-appcenter/', f)):
            os.remove(os.path.join('/var/cache/univention-appcenter/', f))

    def file_exists_in_cache(self, f):
        return os.path.exists(os.path.join('/var/cache/univention-appcenter/', f))

    def test_index_without_gpg(self):
        self.download_index_json()
        res = call('univention-app update', shell=True)
        if res == 0:
            fail('_test_index_without_gpg failed')
        print('### _test_index_without_gpg passed')

    def __exit__(self, exc_type, exc_value, traceback):
        Appcenter.__exit__(self, exc_type, exc_value, traceback)


@pytest.fixture(scope="module")
def test_appcenter():
    with SyncedAppcenter() as sac:
        yield sac


@pytest.fixture()
def appcenter(test_appcenter):
    test_appcenter.download_index_json()
    test_appcenter.download_index_json_gpg()
    yield test_appcenter
    test_appcenter.reset_local_cache()


def test_index_with_gpg(appcenter):
    res = call('univention-app update', shell=True)
    if res != 0:
        fail('_test_index_with_gpg failed')
    print('### _test_index_with_gpg passed')


def test_modify_index(appcenter):
    ucr = ConfigRegistry()
    ucr.load()
    f = f'/var/www/meta-inf/{appcenter.vv}'
    # this just so that all.tar gets newly synced
    call('rm /var/cache/univention-appcenter/%(fqdn)s/%(vv)s/.etags' % {'vv': appcenter.vv, 'fqdn': '%(hostname)s.%(domainname)s' % appcenter.ucr}, shell=True)
    call('echo "foo" > nasty ; tar --append -f %(f)s/all.tar nasty' % {'f': f}, shell=True)
    call('zsyncmake -z -u %(server)s/meta-inf/%(vv)s/all.tar.gz %(f)s/all.tar -o %(f)s/all.tar.zsync' % {'server': ucr.get('repository/app_center/server'), 'vv': appcenter.vv, 'f': f}, shell=True)
    res = call('univention-app update', shell=True)
    if res == 0:
        fail('_test_modify_index failed')
    print('### _test_modify_index passed')


def test_modify_inst(appcenter):
    filename = 'tecart_20151204.inst'
    basename, ext = os.path.splitext(filename)
    appcenter.remove_from_cache(filename)
    appcenter.download(f'univention-repository/{appcenter.vv}/maintained/component/{basename}/{ext}')
    call(f'echo "## SIGNATURE TEST ###" >>/var/www/univention-repository/{appcenter.vv}/maintained/component/{basename}/{ext}', shell=True)
    call('univention-app update', shell=True)
    # Check only if the file was removed from the local cache
    if appcenter.file_exists_in_cache(filename):
        fail('_test_modify_inst failed')
    print('### _test_modify_inst passed')
