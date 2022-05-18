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
import os
import sys
from datetime import date
sys.path.append(os.path.abspath("./_ext"))

# -- Project information -----------------------------------------------------

project = 'Quick start guide for Univention Corporate Server'
copyright = '2021-{}, Univention GmbH'.format(date.today().year)
author = ''

# The full version, including alpha/beta/rc tags
release = '5.0'
version = release

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
pdf_doc_base = os.path.basename(os.path.dirname(__file__))

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
    # Warnings may come up by sphinx-last-updated-by-git. Shall be suppressed in spelling job
    suppress_warnings = ['git.too_shallow']

root_doc = "contents"

html_sidebars = {
    "**": ["sidebar-logo.html", "search-field.html", "_templates/sidebar-links.html", "sbt-sidebar-footer.html"],
}

latex_engine = 'lualatex'
latex_show_pagerefs = True
latex_show_urls = "footnote"
latex_logo = "_static/univention_logo.pdf"
latex_documents = [(root_doc, f'{pdf_doc_base}.tex', "", author, "howto", False)]
latex_elements = {
    "papersize": "a4paper",
    "babel": "\\usepackage{babel}",
}

# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-figure_language_filename
figure_language_filename = "{root}-{language}{ext}"

univention_use_doc_base = True

intersphinx_mapping = {
    "uv-manual": ("https://docs.software-univention.de/manual/5.0/en", None)
}


def fix_title_translation(app, config):
    if config.language == "de":
        config.project = "Quickstart Guide für Univention Corporate Server"
        config.html_title = config.project
        # TODO : Uncomment, once the German translation is available
        # config.intersphinx_mapping["uv-manual"] = ("https://docs.software-univention.de/manual/5.0/de", None)


def setup(app):
    app.connect(
        "config-inited",
        fix_title_translation,
    )
