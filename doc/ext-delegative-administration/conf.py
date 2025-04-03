# SPDX-FileCopyrightText: 2021-2025 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
from __future__ import annotations

import os
import re
import sys
from datetime import date
from typing import Iterator
from urllib.parse import urlparse


def _slugify(s: str) -> str:
    return re.sub(r'[^0-9a-z]', '-', s.lower())[:63].strip('-')


def _inventory(name: str, language: str) -> Iterator[str | None]:
    env = os.environ
    # Local build
    yield f'../{name}/_build/{language}/html/objects.inv'
    yield f'../{name}/_build/html/objects.inv'
    # Previous build: current branch, merge target, default branch
    for var in ('CI_COMMIT_REF_NAME', 'CI_MERGE_REQUEST_TARGET_BRANCH_NAME', 'CI_DEFAULT_BRANCH'):
        try:
            branch = env[var]
            slug = _slugify(branch)
            url = f'{env["CI_API_V4_URL"]}/projects/{env["CI_PROJECT_ID"]}/packages/generic/{name}.{language}/{slug}/objects.inv'
        except LookupError:
            continue
        o = urlparse(url)
        o = o._replace(netloc=f'job:{os.environ["CI_JOB_TOKEN"]}@{o.netloc}')
        yield o.geturl()
    # Public build
    yield None


def ref(name: str, *, lang: str = 'en', ver: str = '') -> tuple[str, tuple[str | None, ...]]:
    ver = ver or version
    return (
        f'https://docs.software-univention.de/{name}/{ver}/{lang}',
        tuple(_inventory(name, language)),
    )


# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

year_range = date.today().year
start_year = 2025
if year_range > start_year:
    year_range = f'{start_year}-{year_range}'
project = 'Univention Corporate Server - Delegative administration documentation'
copyright = f'{year_range}, Univention GmbH'
author = ''

version = '5.2'
# The full version, including alpha/beta/rc tags
release = version

html_show_copyright = True
language = 'en'

html_title = project

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'univention_sphinx_extension',
    'sphinxcontrib.spelling',
    'sphinx_last_updated_by_git',
    'sphinx.ext.intersphinx',
    'sphinx_sitemap',
    'sphinx_copybutton',
    'sphinxcontrib.bibtex',
]

# Warnings may come up by sphinx-last-updated-by-git. Suppress such warnings for all jobs.
suppress_warnings = ['git.too_shallow']

bibtex_bibfiles = ['../bibliography.bib']
bibtex_encoding = 'utf-8'
bibtex_default_style = 'unsrt'
bibtex_reference_style = 'label'

copybutton_prompt_text = r'\$ |> |.+# '
copybutton_prompt_is_regexp = True

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
pdf_doc_base = os.path.basename(os.path.dirname(__file__))

html_theme = 'univention_sphinx_book_theme'
html_theme_options = {
    'use_download_button': False,
    'pdf_download_filename': f'{pdf_doc_base}.pdf',
    'show_source_license': True,
    'typesense_search': False,
    'typesense_document': pdf_doc_base,
    'typesense_document_version': version,
    'univention_matomo_tracking': True,
    'univention_docs_deployment': True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []  # value usually is ['_static']

# https://github.com/mgeier/sphinx-last-updated-by-git
git_last_updated_timezone = 'Europe/Berlin'

numfig = True

if 'spelling' in sys.argv:
    spelling_lang = 'en_US'
    spelling_show_suggestions = True
    spelling_warning = True
    spelling_word_list_filename = ['spelling_wordlist']
    # Don't load extension to speed up the job
    extensions.remove('sphinx_last_updated_by_git')
    extensions.remove('sphinx_sitemap')
    suppress_warnings.append('bibtex')

root_doc = 'contents'

rst_epilog = """
.. include:: /../substitutions.txt
"""

latex_engine = 'lualatex'
latex_show_pagerefs = True
latex_show_urls = 'footnote'
latex_documents = [(root_doc, f'{pdf_doc_base}.tex', '', author, 'howto', False)]
latex_elements = {
    'papersize': 'a4paper',
    'babel': '\\usepackage{babel}',
}

univention_use_doc_base = True

intersphinx_mapping = {
    'uv-manual': ref('manual'),
    'guardian-doc': ('https://docs.software-univention.de/guardian-manual/latest/', None),
}

# See Univention Sphinx Extension for its options.
# https://git.knut.univention.de/univention/documentation/univention_sphinx_extension
# Information about the feedback link.
univention_feedback = True
# Information about the license statement for the source files
univention_pdf_show_source_license = True
