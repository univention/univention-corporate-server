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

project = 'Univention Corporate Server - Manual for users and administrators'
copyright = '2021-{}, Univention GmbH'.format(date.today().year)
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
    "sphinx_copybutton",
    "sphinxcontrib.bibtex",
]

bibtex_bibfiles = ["../bibliography.bib"]
bibtex_encoding = "utf-8"
bibtex_default_style = "unsrt"
bibtex_reference_style = "label"

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
pdf_doc_base = "manual"

html_theme = 'univention_sphinx_book_theme'
html_context = {
    "pdf_download_filename": f"{pdf_doc_base}.pdf",
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
    spelling_word_list = []
    # Don't load extension to speed up the job
    extensions.remove("sphinx_last_updated_by_git")
    extensions.remove("sphinx_sitemap")
    # Warnings may come up by sphinx-last-updated-by-git. Shall be suppressed in spelling job
    suppress_warnings = ['git.too_shallow', "bibtex"]

if "linkcheck" in sys.argv:
    suppress_warnings = ['git.too_shallow', "bibtex"]

root_doc = "contents"

rst_epilog = """
.. include:: /../substitutions.txt

.. include:: /links.txt
"""

latex_engine = 'lualatex'
latex_show_pagerefs = True
latex_show_urls = "footnote"
latex_logo = "_static/univention_logo.pdf"
latex_documents = [(root_doc, f'{pdf_doc_base}.tex', "", author, "manual", False)]
latex_elements = {
    "papersize": "a4paper",
    "babel": "\\usepackage{babel}",
}

# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-figure_language_filename
figure_language_filename = "{root}-{language}{ext}"

linkcheck_allowed_redirects = {
    r"https://help\.univention\.com/t/\d+": r"https://help\.univention\.com/t/[\w-]+/\d+",
    r"https://admin\.google\.com/": r"https://accounts\.google\.com/v3/signin/identifier\?.+",
}

linkcheck_ignore = [
    r"https://errata\.software-univention\.de/#/\?erratum=\d\.\dx\d{1,3}",
]

univention_use_doc_base = True

gettext_additional_targets = ["literal-block"]

def adapt_settings_to_translation(app, config):
    """
    Sets the document title correctly according to the target language.

    See https://github.com/sphinx-doc/sphinx/issues/10282
    """
    if config.language == "de":
        config.project = "Univention Corporate Server - Handbuch für Benutzer und Administratoren"
        config.html_title = config.project
        config.tokenizer_lang = "de_DE"
        config.rst_epilog = """
.. include:: /../substitutions-de.txt

.. include:: /links-de.txt
"""


def setup(app):
    app.connect(
        "config-inited",
        adapt_settings_to_translation,
    )
