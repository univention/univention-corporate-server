# SPDX-FileCopyrightText: 2021-2023 Univention GmbH
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
# import os
import sys
from datetime import date


# -- Project information -----------------------------------------------------

version = "5.1"
release = "5.1-0"
project = f"Univention Corporate Server Architecture {version}"
copyright = f'{date.today().year}, Univention GmbH'
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
    "sphinxcontrib.inkscapeconverter",
    "sphinxext.rediraffe",
    "sphinxcontrib.bibtex",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "uv-manual": ("https://docs.software-univention.de/manual/5.1/en", ("../manual/_build/html/objects.inv", None)),
    "uv-developer-reference": ("https://docs.software-univention.de/developer-reference/5.1/en", ("../developer-reference/_build/html/objects.inv", None)),
    "uv-app-center": ("https://docs.software-univention.de/app-center/5.1/en", ("../app-center/_build/html/objects.inv", None)),
    "uv-ucs-python-api": ("https://docs.software-univention.de/ucs-python-api", None),
}

bibtex_bibfiles = ["../bibliography.bib", "bibliography.bib"]
bibtex_encoding = "utf-8"
bibtex_default_style = "unsrt"
bibtex_reference_style = "label"

root_doc = "contents"

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

rst_epilog = """
.. include:: /links.txt

.. include:: /../abbreviations.txt
"""

rediraffe_redirects = "redirects.txt"
rediraffe_branch = release


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
pdf_doc_base = "architecture"

html_theme = 'univention_sphinx_book_theme'

html_theme_options = {
    "pdf_download_filename": f"{pdf_doc_base}.pdf",
    "show_source_license": True,
    "typesense_search": True,
    "typesense_document": pdf_doc_base,
    "typesense_document_version": version,
    "univention_matomo_tracking": True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []  # value usually is ['_static']

# https://github.com/mgeier/sphinx-last-updated-by-git
git_last_updated_timezone = 'Europe/Berlin'

numfig = True

linkcheck_ignore = [
    "https://github.com/univention/univention-corporate-server/blob/5.0-5/base/univention-config-registry/python/univention/config_registry/misc.py",
]

# Warnings may come up by sphinx-last-updated-by-git. Shall be suppressed to
# avoid the warnings from failing the pipeline.
suppress_warnings = ['git.too_shallow']

if "spelling" in sys.argv:
    spelling_lang = "en_US"
    spelling_show_suggestions = True
    spelling_word_list_filename = ["spelling_wordlist"]

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
