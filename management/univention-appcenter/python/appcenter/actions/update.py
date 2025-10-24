#!/usr/bin/python3
#
# Univention App Center
#  univention-app module for updating the list of available apps
#
# SPDX-FileCopyrightText: 2015-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import os
import os.path
import zlib
from argparse import SUPPRESS, ArgumentParser, Namespace
from glob import glob
from gzip import open as gzip_open
from typing import TYPE_CHECKING
from urllib.error import HTTPError
from urllib.request import Request

from univention.appcenter.actions import UniventionAppAction, possible_network_error
from univention.appcenter.app import LOCAL_ARCHIVE_DIR
from univention.appcenter.app_cache import AppCache, AppCenterCache, Apps
from univention.appcenter.exceptions import NetworkError, UpdateSignatureVerificationFailed, UpdateUnpackArchiveFailed
from univention.appcenter.log import catch_stdout
from univention.appcenter.ucr import ucr_get_int, ucr_is_false, ucr_is_true, ucr_save
from univention.appcenter.utils import gpg_verify, mkdir, urlopen
from univention.config_registry import handler_commit


if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Mapping


ETAGS_NAME = '.etags'
ZSYNC_BINARY_PATH = 'zsync'
TIMEOUT_EXIT_CODE = 124


class Update(UniventionAppAction):
    """Updates the list of all available applications by asking the App Center server"""

    help = 'Updates the list of apps'

    def setup_parser(self, parser: ArgumentParser) -> None:
        parser.add_argument('--ucs-version', help=SUPPRESS)
        parser.add_argument('--appcenter-server', help=SUPPRESS)
        parser.add_argument('--cache-dir', help=SUPPRESS)
        parser.add_argument('--just-get-cache', action='store_true', default=False, help=SUPPRESS)

    def main(self, args: Namespace) -> None:
        something_changed = False
        for app_cache in self._app_caches(args):
            # first of all, set up local cache
            mkdir(app_cache.get_cache_dir())
            if self._extract_local_archive(app_cache):
                something_changed = True

        for appcenter_cache in self._appcenter_caches(args):
            # download meta files like index.json
            mkdir(appcenter_cache.get_cache_dir())
            if self._download_supra_files(appcenter_cache):
                something_changed = True

        for app_cache in self._app_caches(args):
            # try it one more time (ucs.ini may have changed)
            mkdir(app_cache.get_cache_dir())
            if self._extract_local_archive(app_cache):
                something_changed = True
            # download apps based on meta files
            if self._download_apps(app_cache):
                something_changed = True

        if something_changed and not args.just_get_cache:
            apps_cache = Apps()
            for app in apps_cache.get_all_locally_installed_apps():
                newest_app = apps_cache.find_candidate(app) or app
                if app < newest_app:
                    ucr_save({app.ucr_upgrade_key: 'yes'})
            self._update_local_files()

    def _appcenter_caches(self, args: Namespace) -> list[AppCenterCache]:
        if args.appcenter_server:
            return [AppCenterCache(server=args.appcenter_server)]

        ret = []
        servers = set()
        for appcenter_cache in Apps().get_appcenter_caches():
            server = appcenter_cache.get_server()
            if server not in servers:
                servers.add(server)
                ret.append(appcenter_cache)
        return ret

    def _app_caches(self, args: Namespace) -> Iterator[AppCenterCache]:
        for appcenter_cache in self._appcenter_caches(args):
            for app_cache in appcenter_cache.get_app_caches():
                if args.ucs_version:
                    yield app_cache.copy(ucs_version=args.ucs_version, cache_dir=args.cache_dir)
                    break
                else:
                    yield app_cache.copy(cache_dir=args.cache_dir)

    def _get_etags(self, etags_file: str) -> dict[str, str]:
        ret = {}
        try:
            with open(etags_file) as f:
                for line in f:
                    try:
                        fname, etag = line.split('\t')
                    except ValueError:
                        pass
                    else:
                        ret[fname] = etag.rstrip('\n')
        except OSError:
            pass
        return ret

    def _save_etags(self, cache: AppCenterCache, etags: Mapping[str, str]) -> None:
        etags_file = os.path.join(cache.get_cache_dir(), ETAGS_NAME)
        with open(etags_file, 'w') as f:
            f.writelines('%s\t%s\n' % (fname, etag) for fname, etag in etags.items())

    def _download_supra_files(self, appcenter_cache: AppCenterCache) -> bool:
        return self._download_files(appcenter_cache, ['app-categories.ini', 'rating.ini', 'license_types.ini', 'ucs.ini', 'suggestions.json'])

    def _download_files(self, cache: AppCenterCache, filenames: Iterable[str]) -> bool:
        updated = False
        server = cache.get_server()
        cache_dir = cache.get_cache_dir()
        etags_file = os.path.join(cache_dir, ETAGS_NAME)
        present_etags = self._get_etags(etags_file)
        ucs_version = None
        if hasattr(cache, 'get_ucs_version'):
            ucs_version = cache.get_ucs_version()
        for filename in filenames:
            etag = present_etags.get(filename)
            new_etag = self._download_file(server, filename, cache_dir, etag, ucs_version)
            if new_etag:
                present_etags[filename] = new_etag
                updated = True
        self._save_etags(cache, present_etags)
        return updated

    def _verify_file(self, cache_dir: str) -> None:
        if ucr_is_false('appcenter/index/verify'):
            return

        fname = os.path.join(cache_dir, '.tmp.tar')
        sname = os.path.join(cache_dir, '.all.tar.gpg')

        # there have been Signature Verification failures we want to investigate
        # one theory is, that the signature file and the file to verify do not match,
        # e.g the signature has been updated but not the file
        # we put the timestamp diff in the exception to gain some information
        file_timestamp = os.path.getmtime(fname)
        signature_timestamp = os.path.getmtime(sname)
        time_diff = file_timestamp - signature_timestamp

        (rc, gpg_error) = gpg_verify(fname, sname)
        if not rc:
            return

        if gpg_error:
            self.fatal(gpg_error)

        os.unlink(fname)
        os.unlink(sname)

        raise UpdateSignatureVerificationFailed(fname, gpg_error, time_diff)

    def _download_apps_zsync(self, app_cache: AppCache):
        """
        Download app metadata archive using zsync for efficient delta synchronization.

        This method attempts to download the app metadata using zsync, which only
        transfers the differences between the local and remote versions. If zsync
        fails or times out, it automatically falls back to direct HTTPS download.

        :param app_cache: The app cache instance containing server and version info
        :raises: NetworkError if both zsync and direct download fail
        """
        appcenter_host = app_cache.get_server()
        if appcenter_host.startswith('https'):
            appcenter_host = 'http://%s' % appcenter_host[8:]

        cache_dir = app_cache.get_cache_dir()
        tmp_file = os.path.join(cache_dir, '.tmp.tar')
        all_tar_file = os.path.join(cache_dir, '.all.tar')
        all_tar_url = '%s/meta-inf/%s/all.tar.zsync' % (appcenter_host, app_cache.get_ucs_version())

        self.log('Downloading "%s"...' % all_tar_url)

        zsync_args = [ZSYNC_BINARY_PATH, all_tar_url, '-q', '-o', tmp_file, '-i', all_tar_file]
        zsync_timeout = ucr_get_int('appcenter/update/zsync-timeout')
        if zsync_timeout:
            timeout_args = ['timeout', '--kill-after', '2', '-v', str(zsync_timeout)]
            timeout_args.extend(zsync_args)
            zsync_args = timeout_args

        result = self._subprocess(zsync_args, cwd=cache_dir)
        if result.returncode == TIMEOUT_EXIT_CODE:
            self.warn('Downloading the App archive via zsync timed out. Falling back to downloading it directly.')
            self._download_apps_directly(app_cache)
        elif result.returncode:
            # fallback: download all.tar.gz without zsync. some proxys have difficulties with it, including:
            #   * Range requests are not supported
            #   * HTTP requests are altered
            self.warn('Downloading the App archive via zsync failed. Falling back to download it directly.')
            self.warn('For better performance, try to make zsync work for "%s". The error may be caused by a proxy altering HTTP requests' % all_tar_url)
            self._download_apps_directly(app_cache)

    def _download_apps_directly(self, app_cache: AppCache):
        """
        Download app metadata archive directly via HTTPS without using zsync.

        This method downloads the complete all.tar.gz file via HTTPS. It is used
        as a fallback when zsync fails or when explicitly enabled via UCR variable
        appcenter/update/skip-zsync.

        :param app_cache: The app cache instance containing server and version info
        :raises: NetworkError if the download fails
        """
        cache_dir = app_cache.get_cache_dir()
        try:
            self._download_files(app_cache, ['all.tar.gz'])
        except NetworkError as exc:
            # if we cannot download all.tar.gz, the .etags file is not valid anymore
            # https://forge.univention.org/bugzilla/show_bug.cgi?id=58469
            self.fatal('Failed to download all.tar.gz: %s' % exc)
            if os.path.exists(os.path.join(cache_dir, ETAGS_NAME)):
                self.warn('Removing the old etags file %s' % os.path.join(cache_dir, ETAGS_NAME))
                # remove the old etags file, so that the next update will try to download it again
                os.unlink(os.path.join(cache_dir, ETAGS_NAME))
            raise
        # files are always downloaded with their filename prepended by '.'
        tgz_file = os.path.join(cache_dir, '.all.tar.gz')
        self._uncompress_archive(app_cache, tgz_file)

    def _download_apps(self, app_cache: AppCache) -> bool:
        filenames = [] if ucr_is_false('appcenter/index/verify') else ['all.tar.gpg']
        if filenames and not self._download_files(app_cache, filenames):
            return False

        if ucr_is_true('appcenter/update/skip-zsync'):
            self._download_apps_directly(app_cache)
        else:
            self._download_apps_zsync(app_cache)

        self._verify_file(app_cache.get_cache_dir())

        self._extract_archive(app_cache)
        return True

    @possible_network_error
    def _download_file(self, base_url: str, filename: str, cache_dir: str, etag: str | None, ucs_version: str | None = None) -> str | None:
        url = os.path.join(base_url, 'meta-inf', ucs_version or '', filename)
        target = os.path.join(cache_dir, '.%s' % filename)
        if not os.path.exists(target):
            etag = None
        self.log('Downloading "%s"...' % url)
        headers = {}
        if etag:
            headers['If-None-Match'] = etag
        request = Request(url, headers=headers)  # noqa: S310
        try:
            response = urlopen(request)
        except HTTPError as exc:
            if exc.getcode() == 304:
                self.debug('  ... Not Modified')
                return None
            raise
        etag = response.headers.get('etag')
        content = response.read()
        with open(target, 'wb') as f:
            f.write(content)
        return etag

    def _update_local_files(self) -> None:
        self.debug('Updating app files...')
        # some variables could change UCR templates
        # e.g. Name, Description
        self._update_conffiles()

    def _get_conffiles(self) -> list[str]:
        return []

    def _update_conffiles(self) -> None:
        conffiles = self._get_conffiles()
        if conffiles:
            with catch_stdout(self.logger):
                handler_commit(conffiles)

    def _get_local_archive(self, app_cache: AppCenterCache) -> str | None:
        fname = os.path.join(LOCAL_ARCHIVE_DIR, app_cache.get_server_netloc(), app_cache.get_ucs_version(), 'all.tar.gz')
        if os.path.exists(fname):
            return fname

    def _extract_local_archive(self, app_cache: AppCenterCache) -> bool:
        local_archive = self._get_local_archive(app_cache)
        if not local_archive:
            # Not my local_archive
            return False
        if any(not fname.startswith('.') for fname in os.listdir(app_cache.get_cache_dir())):
            # we already have a cache. our archive is just outdated...
            return False
        self.log('Filling the App Center file cache from our local archive %s!' % local_archive)
        if not self._uncompress_archive(app_cache, local_archive):
            return False
        return self._extract_archive(app_cache)

    def _uncompress_archive(self, app_cache: AppCenterCache, local_archive: str) -> bool:
        """`gunzip` in Python"""
        try:
            with gzip_open(local_archive, 'rb') as zipped_file:
                archive_content = zipped_file.read()
            with open(os.path.join(app_cache.get_cache_dir(), '.tmp.tar'), 'wb') as extracted_file:
                extracted_file.write(archive_content)
        except (OSError, zlib.error) as exc:
            self.warn('Error while reading %s: %s' % (local_archive, exc))
            return False
        else:
            return True

    def _extract_archive(self, app_cache: AppCenterCache) -> None:
        """`tar xf` in 'Python'"""
        cache_dir = app_cache.get_cache_dir()
        self.debug('Extracting archive in %s' % cache_dir)
        self._purge_old_cache(cache_dir)
        tmp_file = os.path.join(cache_dir, '.tmp.tar')
        self.debug('Unpacking %s...' % tmp_file)
        if self._subprocess(['tar', '-C', cache_dir, '-x', '-f', tmp_file]).returncode:
            raise UpdateUnpackArchiveFailed(tmp_file)
        # make sure cache dir is available for everybody
        os.chmod(cache_dir, 0o755)
        # `touch tmp_file` to get a new cache in case it was created in between extraction
        os.utime(tmp_file, None)
        # Rename temporary to final file name
        all_tar_file = os.path.join(cache_dir, '.all.tar')
        os.rename(tmp_file, all_tar_file)

    def _purge_old_cache(self, cache_dir: str) -> None:
        self.debug('Removing old files...')
        for fname in glob(os.path.join(cache_dir, '*')):
            try:
                os.unlink(fname)
            except OSError as exc:
                self.warn('Cannot delete %s: %s' % (fname, exc))
