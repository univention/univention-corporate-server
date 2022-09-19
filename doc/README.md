# Univention production documentation for UCS

This directory contains the product documentation related to UCS.

## Contribution

Every contribution to the documentation is welcome and appreciated. The
workflow regarding issues and bugs is the same as with implementing software.

For your content, consider the [Documentation Style
Guide](https://hutten.knut.univention.de/mediawiki/index.php/Documentation_Style_Guide).

For contribution to RST content, see the [Working with
Sphinx](https://hutten.knut.univention.de/mediawiki/index.php/Docs#Working_with_Sphinx)
section in the Internal wiki.

For contribution to DocBook content, see the [DocBook
article](https://hutten.knut.univention.de/mediawiki/index.php/Docbook) in the
Univention Internal wiki.

## Versioning of documentation

All documents, except the `changelog` and the `release-notes`, use the major
and minor version numbers for the deployment path and within the document.

### General documents

You configure the document target version with `DOC_TARGET_VERSION` in
[base-doc.yml](./../.gitlab-ci/base-doc.yml).

You **must** update the `DOC_TARGET_VERSION` upon a new minor release for UCS.

### Changelog and release notes

The version string for the UCS changelog and release notes goes down to the
patch level.

For each new UCS patch level releases, you **must** update the
`CHANGELOG_TARGET_VERSION` in [base-doc.yml](./../.gitlab-ci/base-doc.yml), for
example `5.0-2`. The version string **must not** contain spaces. Keep in mind,
the version string is used for the deployment path of the document.

To reference the correct changelog document in the release notes, use the following steps:

1. Adjust `CHANGELOG_TARGET_VERSION`.
2. Write and publish the changelog document.
3. Adjust the URL value to the new changelog document location in the
   `intersphinx_mapping` variables (English and German language settings) in
   the release notes [conf.py](./release-notes/conf.py).
