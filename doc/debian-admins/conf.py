# SPDX-FileCopyrightText: 2023-2024 Univention GmbH
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
    return re.sub(r"[^0-9a-z]", "-", s.lower())[:63].strip("-")


def _inventory(name: str, language: str) -> Iterator[str | None]:
    env = os.environ
    # Local build
    yield f"../{name}/_build/{language}/html/objects.inv"
    yield f"../{name}/_build/html/objects.inv"
    # Previous build: current branch, merge target, default branch
    for var in ('CI_COMMIT_REF_NAME', 'CI_MERGE_REQUEST_TARGET_BRANCH_NAME', 'CI_DEFAULT_BRANCH'):
        try:
            branch = env[var]
            slug = _slugify(branch)
            url = f"{env['CI_API_V4_URL']}/projects/{env['CI_PROJECT_ID']}/packages/generic/{name}.{language}/{slug}/objects.inv"
        except LookupError:
            continue
        o = urlparse(url)
        o = o._replace(netloc=f"job:{os.environ['CI_JOB_TOKEN']}@{o.netloc}")
        yield o.geturl()
    # Public build
    yield None


def ref(name: str, *, lang: str = "en", ver: str = "") -> tuple[str, tuple[str | None, ...]]:
    ver = ver or version
    return (
        f"https://docs.software-univention.de/{name}/{ver}/{lang}",
        tuple(_inventory(name, language)),
    )


# -- Project information -----------------------------------------------------

version = "5.0"
release = "5.0-9"
project = f"UCS {version} for Debian and Ubuntu Administrators"
copyright = f'2023-{date.today().year}, Univention GmbH'
author = 'Univention GmbH'
language = 'en'

html_title = project

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinxcontrib.spelling",
    "univention_sphinx_extension",
    "sphinx_last_updated_by_git",
    "sphinxcontrib.bibtex",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "uv-manual": ref("manual"),
    "uv-architecture": ref("architecture"),
    "uv-navigation": ("https://docs.software-univention.de/n/en", None),
    "python": ("https://docs.python.org/3.7/", None),
}

bibtex_bibfiles = ["../bibliography.bib"]
bibtex_encoding = "utf-8"
bibtex_default_style = "unsrt"
bibtex_reference_style = "label"

root_doc = "index"

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

rst_epilog = """
.. include:: /../abbreviations.txt
"""


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
pdf_doc_base = "debian-admins"

html_theme = 'univention_sphinx_book_theme'

html_theme_options = {
    "pdf_download_filename": f"{pdf_doc_base}.pdf",
    "show_source_license": True,
    "typesense_search": True,
    "typesense_document": pdf_doc_base,
    "typesense_document_version": version,
    "univention_matomo_tracking": True,
    "univention_docs_deployment": True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []  # value usually is ['_static']

# https://github.com/mgeier/sphinx-last-updated-by-git
git_last_updated_timezone = 'Europe/Berlin'

numfig = True

# Warnings may come up by sphinx-last-updated-by-git. Shall be suppressed to
# avoid the warnings from failing the pipeline.
suppress_warnings = ['git.too_shallow']

if "spelling" in sys.argv:
    spelling_lang = "en_US"
    spelling_show_suggestions = True
    spelling_word_list_filename = []

latex_engine = 'lualatex'
latex_show_pagerefs = True
latex_show_urls = "footnote"
latex_documents = [(root_doc, f'{pdf_doc_base}.tex', project, author, "manual", False)]
latex_elements = {
    "papersize": "a4paper",
}

# See Univention Sphinx Extension for its options.
# https://git.knut.univention.de/univention/documentation/univention_sphinx_extension
# Information about the feedback link.
univention_feedback = True
# Information about the license statement for the source files
univention_pdf_show_source_license = True
