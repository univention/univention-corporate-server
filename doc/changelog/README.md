<!--
Like what you see? Join us!
https://www.univention.com/about-us/careers/vacancies/

Copyright (C) 2021-2023 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only

https://www.univention.com/

All rights reserved.

The source code of this program is made available under the terms of
the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
published by the Free Software Foundation.

Binary versions of this program provided by Univention to you as
well as other copyrighted, protected or trademarked materials like
Logos, graphics, fonts, specific documentations and configurations,
cryptographic keys etc. are subject to a license agreement between
you and Univention and not subject to the AGPL-3.0-only.

In the case you use this program under the terms of the AGPL-3.0-only,
the program is provided in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public
License with the Debian GNU/Linux or Univention distribution in file
/usr/share/common-licenses/AGPL-3; if not, see
<https://www.gnu.org/licenses/agpl-3.0.txt>.
-->

# Changelog for UCS

This directory contains the changelog document for UCS.

The changelog is a distinct document that lists all the changes for the
respective version since the last version.

The content for the changelog comes from the errata updates described in the
errata YAML files in the directory
[/doc/errata/published](../errata/published). The changelog associates the
changes in their respective section in the changelog.

## Create a changelog

This document uses Sphinx for building the artifacts from the reStructeredText
(reST) documents. To extract the content from the errata YAML files, Sphinx
uses the custom builder [Univention Sphinx
Changelog](https://git.knut.univention.de/univention/documentation/univention_sphinx_changelog).

The following example illustrates the procedure in detail on the example for
the UCS 5.0-3 patch level release version.

1. Update configuration settings in `conf.py`:

   * Set `univention_changelog_previous_release` to `"5.0-2"`.

   * Set `release` to `5.0-3`.

   * Keep `version` at `5.0`.

1. Extract the changes from the errata YAML files and create a reST document:
   `docker run --rm -ti -v "/home/phahn/REPOS/ucs:/project" -w /project/doc/changelog --network=host -u "$UID" docker-registry.knut.univention.de/knut/sphinx-base make changelog`.

1. Replace the `index.rst` file with the content from the generated reST
   document at `_build/changelog/changelog.rst`.

1. Review the content and add reST semantics to it. Check the style with the
   [Univention Documentation
   Styleguide](https://univention.gitpages.knut.univention.de/documentation/styleguide/).

1. Commit the changes to the repository and let the CI/CD pipeline build the
   artifacts.

