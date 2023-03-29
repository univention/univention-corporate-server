# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright (C) 2021-2023 Univention GmbH
#
# SPDX-License-Identifier: AGPL-3.0-only
#
# https://www.univention.com/
#
# All rights reserved.
#
# The source code of this program is made available under the terms of
# the GNU Affero General Public License v3.0 only (AGPL-3.0-only) as
# published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the AGPL-3.0-only.
#
# In the case you use this program under the terms of the AGPL-3.0-only,
# the program is provided in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, see
# <https://www.gnu.org/licenses/agpl-3.0.txt>.

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
import sys
from datetime import date


# -- Project information -----------------------------------------------------

project = 'Univention Corporate Server - Extended IP and network management documentation'
copyright = f'2021-{date.today().year}, Univention GmbH'
author = ''

# The full version, including alpha/beta/rc tags
release = '5.0'

html_show_copyright = True
language = 'en'

html_title = project

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "univention_sphinx_extension",
    "sphinxcontrib.spelling",
    "sphinx_last_updated_by_git",
    "sphinx.ext.intersphinx",
    "sphinx_sitemap",
    "sphinx_copybutton",
]

# Warnings may come up by sphinx-last-updated-by-git. Suppress such warnings for all jobs.
suppress_warnings = ['git.too_shallow']

copybutton_prompt_text = r"\$ |> |.+# "
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
pdf_doc_base = "ext-networks"

html_theme = 'univention_sphinx_book_theme'
html_theme_options = {
    "show_source_license": True,
    "pdf_download_filename": f"{pdf_doc_base}.pdf",
    "use_download_button": False,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []  # value usually is ['_static']
html_last_updated_fmt = "%a, %d. %b %Y at %H:%M (UTC%z)"

# https://github.com/mgeier/sphinx-last-updated-by-git
git_last_updated_timezone = 'Europe/Berlin'

numfig = True

if "spelling" in sys.argv:
    spelling_lang = "en_US"
    spelling_show_suggestions = True
    spelling_warning = True
    spelling_word_list_filename = []
    # Don't load extension to speed up the job
    extensions.remove("sphinx_last_updated_by_git")
    extensions.remove("sphinx_sitemap")
    suppress_warnings.append("bibtex")

root_doc = "index"

rst_epilog = """
.. include:: /../substitutions.txt
"""

html_sidebars = {
    "**": [
        "sidebar-logo.html",
        "search-field.html",
        "_templates/sidebar-links.html",
    ],
}

latex_engine = 'lualatex'
latex_show_pagerefs = True
latex_show_urls = "footnote"
latex_documents = [
    (root_doc, f'{pdf_doc_base}.tex', "", author, "howto", False)]
latex_elements = {
    "papersize": "a4paper",
    "babel": "\\usepackage{babel}",
}

univention_use_doc_base = True

intersphinx_mapping = {
    "uv-manual": ("https://docs.software-univention.de/manual/5.0/en", None),
}

# See Univention Sphinx Extension for its options and information about the
# feedback link.
# https://git.knut.univention.de/univention/documentation/univention_sphinx_extension
univention_feedback = True
