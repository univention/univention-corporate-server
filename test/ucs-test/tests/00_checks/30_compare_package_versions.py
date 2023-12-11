#!/usr/share/ucs-test/runner python3
## desc: Check that package versions of the current release are higher than for the previous.
## bugs: [36369]
## roles: [domaincontroller_master]
## tags: [producttest]
## exposure: safe
## versions:
##  5.0-0: skip

"""
Checks that all the packages in the specified remote repositiories for an
older UCS release have lower version number than for the current UCS ver.
UCS versions are either picked automatically (two most recent, by default)
or can be specified as two command-line arguments.

Broken for UCS 5.0:
- pool/ dists/ layout is used
- no `unmaintained`
- no architecture `i386`
"""

from __future__ import annotations

import re
from argparse import ArgumentParser, Namespace
from contextlib import closing
from dataclasses import dataclass
from gzip import open as gzip_open
from pathlib import Path
from tempfile import TemporaryDirectory
from time import sleep
from typing import Dict, Iterable, List, Set, Tuple
from urllib.error import ContentTooShortError
from urllib.request import urlopen, urlretrieve

from debian.debian_support import Version
from lxml.html import fromstring

from univention.testing import utils


RE_MAJOR_MINOR = re.compile(r'^([1-9][0-9]*.[0-9]+)/?$')
RE_MAJOR_MINOR_PATCH = re.compile(r'([1-9[0-9]*\.[0-9]+-[0-9]+)(?:-errata)?/?$')
ARCHS = frozenset({"amd64", "i386", "all"})
MAINT = ("maintained", "unmaintained")
PUBLIC = "https://updates.software-univention.de/"
TESTING = "https://updates-test.software-univention.de/"

total_errors = 0


@dataclass
class PackageEntry:
    package: str
    version: Version
    filename: str
    sourcepkg: str
    ucs_version: str

    @classmethod
    def parse(cls, entry: str, ucs_version: str) -> PackageEntry:
        package = version = filename = sourcepkg = ""
        for line in entry.splitlines():
            k, _, v = line.partition(": ")
            if k == "Package":
                package = v
            elif k == "Version":
                version = v
            elif k == "Filename":
                filename = v
            elif k == "Source":
                sourcepkg = v

        return cls(package, Version(version), filename, sourcepkg or package, ucs_version)

    def is_ok(self) -> bool:
        return bool(self.package) and bool(self.version)


def download_packages_file(url: str, version: str, arch: str, temp_directory: Path) -> Path | None:
    """
    Downloads a 'Packages.gz' as the given url into the
    'temp_directory/version/arch/' folder.
    """
    file_path = temp_directory / version / arch / 'Packages.gz'

    url += f"{version}/{arch}/Packages.gz"
    print(f"Downloading {url}:")

    file_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        urlretrieve(url, file_path)  # noqa: S310
    except ContentTooShortError as exc:
        print(f"Error {exc!r} occurred, probably the connection was lost. Performing a new attempt in 10 seconds.")
        sleep(10)
        urlretrieve(url, file_path)  # noqa: S310
    except OSError as exc:
        print(f"Error {exc!r} occurred, probably the connection cannot be established or the url is incorrect. Skipping the url '{url}'.")
        return None

    return file_path


def load_packages_file(filename: Path, target_dict: Dict[str, PackageEntry], ucs_version: str) -> None:
    """
    Reads the given 'filename' Packages.gz file.
    Creates a entry object for each found package and fills the target_dict.
    """
    try:
        with closing(gzip_open(filename.as_posix(), 'r')) as fd:
            content = fd.read().decode()
    except OSError:
        content = filename.read_text()

    for entry in content.split('\n\n'):
        if not entry:
            continue
        pkg = PackageEntry.parse(entry, ucs_version)
        if not pkg.is_ok():
            continue
        prev = target_dict.setdefault(pkg.package, pkg)
        if prev and prev.version < pkg.version:
            target_dict[pkg.package] = pkg


def load_version(url: str, architectures: Iterable[str] = ARCHS) -> Dict[str, PackageEntry]:
    """
    Selects all minor and errata versions for the given 'url'.
    Downloads respective 'Packages.gz' for each version and
    returns a dict filled with PackageEntries.
    """
    target: Dict[str, PackageEntry] = {}

    for version in select_minor_levels(url):
        for arch in architectures:
            with TemporaryDirectory() as temp:
                file_name = download_packages_file(url, version, arch, Path(temp))
                if file_name:
                    print(f"Loading packages file: {file_name}")
                    load_packages_file(file_name, target, f'ucs_{version}')

    return target


def compare(old_pkgs: Dict[str, PackageEntry], new_pkgs: Dict[str, PackageEntry]) -> None:
    """
    Compares 'old_pkgs' and 'new_pkgs' versions via apt.
    Prints all the errors detected.
    """
    errors = 0
    src_package_list: Set[str] = set()

    for package, new in sorted(new_pkgs.items()):
        old = old_pkgs.get(package)
        if not old:
            continue
        elif old.version <= new.version:
            continue

        if errors == 0:
            print('---------------------------------------------------------')
            print('  The following packages use a smaller package version:')
            print('---------------------------------------------------------')

        print(f" Package: {package} from source package: {new.sourcepkg}")
        print(f"   {old.ucs_version}: {old.version}")
        print(f"   {new.ucs_version}: {new.version}")

        src_package_list.add(new.sourcepkg)
        errors += 1

    if errors:
        print("Affected source packages:")
        for package in sorted(src_package_list):
            print("  %s" % package)

        print(f"Number of affected binary packages: {errors}")
        print(f"Number of affected source packages: {len(src_package_list)}")

        global total_errors
        total_errors += errors


def read_url(url: str):
    """Returns the 'url' in an easy to parse format for finding links."""
    with urlopen(url) as connection:  # noqa: S310
        return fromstring(connection.read())


def select_errata_levels(repo_component_url: str) -> List[str]:
    """Returns list of .*-errata levels found in the given 'repo_component_url'."""
    return [
        f'component/{link.rstrip("/")}'
        for link in read_url(repo_component_url).xpath('//a/@href')
        if RE_MAJOR_MINOR_PATCH.match(link.rstrip("/"))
    ]


def select_minor_levels(repo_major_url: str) -> List[str]:
    """
    Returns the list of minor versions with patch and errata levels as found
    for the given 'repo_major_url'.
    """
    check_patchlevels: List[str] = []

    for link in read_url(repo_major_url).xpath('//a/@href'):
        link = link.rstrip("/")
        if RE_MAJOR_MINOR_PATCH.match(link):
            check_patchlevels.append(link)
        if link == 'component':
            check_patchlevels += select_errata_levels(f"{repo_major_url}component/")

    if not check_patchlevels:
        utils.fail(f"Could not find at least one patch level number in the given repository at {repo_major_url}s")

    print(f"The following patch levels will be checked: {check_patchlevels}")
    return check_patchlevels


def select_major_versions_for_test(repo_url: str) -> Tuple[Version, Version]:
    """
    Looks into specified 'repo_url' and picks up the two most recent
    major versions (for example 3.2 and 4.0).
    """
    versions: List[Version] = [
        Version(link.rstrip("/"))
        for link in read_url(repo_url).xpath('//a/@href')
        if RE_MAJOR_MINOR.match(link.rstrip("/"))
    ]

    versions.sort()
    return (versions[-2], versions[-1])


def parse_arguments() -> Namespace:
    """
    Returns the parsed arguments when test is run interactively via
    'python3 testname ...'
    First an older version should be specified.
    """
    parser = ArgumentParser(description=__doc__)
    parser.add_argument(
        "--architecture", "-a",
        action="append",
        default=[],
        help="Check only these architectures",
    )
    parser.add_argument(
        "--maintained-only", "-m",
        action="store_true",
        help="Only check maintained packages",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--public", "-p",
        action="store_const",
        const=[PUBLIC],
        help="Use public mirror",
        dest="mirror",
    )
    group.add_argument(
        "--testing", "-t",
        action="store_const",
        const=[TESTING],
        help="Use testing mirror",
        dest="mirror",
    )
    group.add_argument(
        "--repository", "-r",
        action="append",
        default=[],
        help="Use given mirror",
        dest="mirror",
    )
    parser.add_argument(
        "old_release",
        type=_release,
        nargs="?",
    )
    parser.add_argument(
        "new_release",
        type=_release,
        nargs="?",
    )
    args = parser.parse_args()

    if args.old_release and args.new_release:
        if args.old_release >= args.new_release:
            parser.error(f"The given new release '{args.new_release}' cannot be smaller than the older release '{args.old_release}'")
    else:
        print("The UCS releases for the test will be determined automatically:")

    args.architectures = {arch for archs in args.architecture for arch in archs.split(",")} if args.architecture else ARCHS

    return args


def _release(arg: str) -> Version:
    m = RE_MAJOR_MINOR.match(arg)
    if m:
        return Version(arg)
    raise ValueError(arg)


def main() -> None:
    args = parse_arguments()

    try:
        for repo_url in args.mirror or (PUBLIC, TESTING):
            old, new = (args.old_release, args.new_release) if args.new_release else select_major_versions_for_test(repo_url)
            print(f"Comparing packages for UCS versions {old} and {new} in repository at '{repo_url}':")

            for repo_type in MAINT[:1 if args.maintained_only else -1]:
                print(f"Checking {repo_type} packages:")
                previous_version = f"{repo_url}{old}/{repo_type}/"
                current_version = f"{repo_url}{new}/{repo_type}/"
                compare(load_version(previous_version), load_version(current_version, args.architectures))
    finally:
        if total_errors:  # an overall statistics
            utils.fail(f"There were {total_errors} errors detected in total. Please check the complete test output.")

        print("No errors were detected.")


if __name__ == '__main__':
    main()
