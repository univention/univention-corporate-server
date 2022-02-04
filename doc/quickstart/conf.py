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

# -- Project information -----------------------------------------------------

project = 'Quick start guide for Univention Corporate Server'
copyright = '2021-{}, Univention GmbH.'.format(date.today().year)
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
    "sphinx_sitemap",
]

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
html_theme = 'univention_sphinx_book_theme'
html_theme_options = {
    "extra_navbar": "Status: DRAFT. Work in Progress.",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']
html_last_updated_fmt = "%a, %d. %b %Y at %H:%M (UTC%z)"

# https://github.com/mgeier/sphinx-last-updated-by-git
git_last_updated_timezone = 'Europe/Berlin'

numfig = True

if "spelling" in sys.argv:
    spelling_lang = "en_US"
    spelling_show_suggestions = True
    spelling_warning = True
    spelling_word_list_filename = ["spelling_wordlist"]
    # Warnings may come up by sphinx-last-updated-by-git. Shall be suppressed in spelling job
    suppress_warnings = ['git.too_shallow']

root_doc = "index"

latex_engine = 'lualatex'
latex_show_pagerefs = True
latex_show_urls = "footnote"
latex_logo = "_static/univention_logo.pdf"
latex_documents = [(root_doc, 'quickstart.tex', project, author, "manual", False)]
latex_elements = {
    "papersize": "a4paper",
}

# Sitemap, see https://github.com/jdillard/sphinx-sitemap
html_baseurl = 'http://https://docs.software-univention.de/quickstart/en/5.0'

# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-figure_language_filename
figure_language_filename = "{root}-{language}.{ext}"
