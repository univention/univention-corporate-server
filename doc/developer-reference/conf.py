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
# sys.path.insert(0, os.path.abspath('.'))

from datetime import date
from os import path

# -- Project information -----------------------------------------------------

project = 'Univention Corporate Server - Manual for developers'
copyright = '2021-{}, Univention GmbH'.format(date.today().year)
author = ''

# The full version, including alpha/beta/rc tags
release = '5.0-2'
version = '5.0'

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
    "sphinx_sitemap",
    "sphinx_copybutton",
    "sphinxcontrib.bibtex",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.inkscapeconverter",
]

bibtex_bibfiles = ["../bibliography.bib"]
bibtex_encoding = "utf-8"
bibtex_default_style = "unsrt"
bibtex_reference_style = "label"

intersphinx_mapping = {
    "uv-manual": (f"https://docs.software-univention.de/manual/{version}/en", None),
    "uv-app-center": (f"https://docs.software-univention.de/app-center/{version}/en/", None),
    "python": ("https://docs.python.org/3.7/", None),
    "python-general": ("https://docs.python.org/3/", None),
}

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
pdf_doc_base = path.basename(path.dirname(__file__))

html_theme = 'univention_sphinx_book_theme'
html_context = {
    "pdf_download_filename": f"{pdf_doc_base}.pdf",
}

html_style = 'custom.css'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static', ]  # value usually is ['_static']
html_last_updated_fmt = "%a, %d. %b %Y at %H:%M (UTC%z)"

# https://github.com/mgeier/sphinx-last-updated-by-git
git_last_updated_timezone = 'Europe/Berlin'

numfig = True

if "spelling" in sys.argv:
    spelling_lang = "en_US"
    spelling_show_suggestions = True
    spelling_warning = True
    spelling_word_list = []
    # Don't load extension to speed up the job
    extensions.remove("sphinx_last_updated_by_git")
    extensions.remove("sphinx_sitemap")
    # Warnings may come up by sphinx-last-updated-by-git. Shall be suppressed in spelling job
    suppress_warnings = ['git.too_shallow', "bibtex"]

if "linkcheck" in sys.argv:
    suppress_warnings = ['git.too_shallow', "bibtex"]

linkcheck_ignore = [
    r"https://errata\.software-univention\.de/#/\?erratum=\d\.\dx\d{1,3}",
]

linkcheck_allowed_redirects = {
    r"https://help\.univention\.com/c/knowledge-base/supported/":
        r"https://help\.univention\.com/c/knowledge-base/supported/48",
    r"https://help\.univention\.com/t/13149":
        r"https://help\.univention\.com/t/howto-update-listener-cachemasterentry/13149",
}

root_doc = "contents"

rst_epilog = """
.. include:: /../substitutions.txt
"""

latex_engine = 'lualatex'
latex_show_pagerefs = True
latex_show_urls = "footnote"
latex_documents = [(root_doc, f'{pdf_doc_base}.tex', "", author, "manual", False)]
latex_elements = {
    "papersize": "a4paper",
    "babel": "\\usepackage{babel}",
}

univention_use_doc_base = True

manpages_url = "https://manpages.debian.org/{path}"
