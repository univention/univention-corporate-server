import io

import setuptools
from debian.changelog import Changelog

dch = Changelog(io.open('debian/changelog', encoding='utf-8'))

if __name__ == '__main__':
    setuptools.setup(
        name=dch.package,
        version=dch.version.full_version,
    )
