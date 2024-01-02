<!--
SPDX-FileCopyrightText: 2021-2024 Univention GmbH

SPDX-License-Identifier: AGPL-3.0-only
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
the UCS 5.0-6 patch level release version.

1. Update configuration settings in `conf.py`:

   * Set `univention_changelog_previous_release` to `"5.0-5"`.

   * Set `release` to `5.0-6`.

   * Keep `version` at `5.0`.

1. Extract the changes from the errata YAML files and create a reST document:
   ```sh
   root="$(git rev-parse --show-toplevel)"
   git="$(git rev-parse --absolute-git-dir)"
   docker run \
      --network=host \
      --rm -ti \
      -u "$UID" \
      -v "$root:$root" \
      -v "$git:$git" \
      -w "$root/doc/changelog" \
      docker-registry.knut.univention.de/knut/sphinx-base \
      make changelog
   ```

1. Replace the `index.rst` file with the content from the generated reST
   document at `_build/changelog/changelog.rst`.

1. Review the content and add reST semantics to it. Check the style with the
   [Univention Documentation
   Styleguide](https://univention.gitpages.knut.univention.de/documentation/styleguide/).

1. Commit the changes to the repository and let the CI/CD pipeline build the
   artifacts.
