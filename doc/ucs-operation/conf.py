# SPDX-FileCopyrightText: 2021-2026 Univention GmbH
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
import os
import sys
from datetime import date

from univention_sphinx_conf_helper.inventory_resolver import reference_inventory


# -- Project information -----------------------------------------------------

year_range = date.today().year
start_year = 2025
if year_range > start_year:
    year_range = f"{start_year}-{year_range}"
copyright = f"{year_range}, Univention GmbH"
author = ""

version = "5.2"
# The full version, including alpha/beta/rc tags
release = version

project = f"Nubus for UCS {version} - Operation Manual"
html_show_copyright = True
language = "en"

html_title = project

# The doc_basename must match the documents root directory name on the public
# target location. Otherwise the PDF link on the overview page will point to
# the wrong file.
doc_basename = os.path.basename(os.path.dirname(__file__))

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_copybutton",
    "sphinxcontrib.spelling",
    "univention_sphinx_extension",
    "sphinx_sitemap",
    "sphinx_last_updated_by_git",
    "sphinx.ext.intersphinx",
    "sphinxcontrib.bibtex",
    "sphinx_inline_tabs",
    "sphinx_design",
]

intersphinx_mapping = {
    "uv-nubus-manual": (
        "https://docs.software-univention.de/nubus-manual/latest/en",
        None,
    ),
    "uv-ucs-manual": reference_inventory("manual", version=version),
    "uv-architecture": reference_inventory("architecture", version=version),
    "uv-debian-admins": reference_inventory("debian-admins", version=version),
    "uv-keycloak-app": (
        "https://docs.software-univention.de/keycloak-app/latest",
        None,
    ),
    "uv-docs-overview": ("https://docs.software-univention.de/n/en/", None),
    "uv-nubus-customization": (
        "https://docs.software-univention.de/nubus-customization/latest/en/",
        None,
    ),
    "linux-kernel-docs": (
        "https://www.kernel.org/doc/html/v6.1/",
        None,
    ),  # UCS 5.2 Kernel is 6.1
}

# TODO: When using a kernel different from 6.1, update the reference to the Kernel docs in the intersphinx mapping.

# Warnings may come up by sphinx-last-updated-by-git. Suppress such warnings for all jobs.
suppress_warnings = ["git.too_shallow"]

bibtex_bibfiles = ["../bibliography.bib"]
bibtex_encoding = "utf-8"
bibtex_default_style = "unsrt"
bibtex_reference_style = "label"

# For Windows prompt, we still need ``> ``
copybutton_prompt_text = r"\$ |> |.+# "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\\"
copybutton_here_doc_delimiter = "EOT"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#

html_theme = "univention_sphinx_book_theme"
html_theme_options = {
    "show_source_license": True,
    "typesense_search": True,
    "typesense_document": doc_basename,
    "typesense_document_version": version,
    "univention_matomo_tracking": True,
    "univention_docs_deployment": True,
    "announcement": "<p><i class='fa-solid fa-circle-exclamation'></i> "
    "This document is work in progress and will replace the UCS Manual.</br> "
    "If you don't find the content "
    "you are looking for, refer to the "
    "<a href='https://docs.software-univention.de/manual/5.2/en/' "
    "target='_blank' style='color: var(--pst-color-secondary)'>"
    "UCS Manual</a>.</p>",
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = []  # value usually is ['_static']

# https://github.com/mgeier/sphinx-last-updated-by-git
git_last_updated_timezone = "Europe/Berlin"

numfig = True

if "spelling" in sys.argv:
    spelling_lang = "en_US"
    spelling_show_suggestions = True
    spelling_warning = True
    spelling_word_list_filename = ["spelling_wordlist"]
    # Don't load extension to speed up the job
    extensions.remove("sphinx_last_updated_by_git")
    extensions.remove("sphinx_sitemap")
    suppress_warnings.append("bibtex")

root_doc = "contents"

latex_engine = "lualatex"
latex_show_pagerefs = True
latex_show_urls = "footnote"
latex_documents = [(root_doc, f"{doc_basename}.tex", "", author, "manual", False)]
latex_elements = {
    "papersize": "a4paper",
    "babel": "\\usepackage{babel}",
}

# https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-figure_language_filename
figure_language_filename = "{root}-{language}{ext}"

linkcheck_allowed_redirects = {
    r"https://help\.univention\.com/t/\d+": r"https://help\.univention\.com/t/[\w-]+/\d+",
}

linkcheck_ignore = [
    r"https://errata\.software-univention\.de/#/\?erratum=\d\.\dx\d{1,3}",
    r"https://www\.gnu\.org/software/grub/manual/grub/",  # rate limited
]

univention_use_doc_base = True

gettext_additional_targets = ["literal-block"]

# See Univention Sphinx Extension for its options.
# https://git.knut.univention.de/univention/documentation/univention_sphinx_extension
# Information about the feedback link.
univention_feedback = True


def adapt_settings_to_translation(app, config):
    """
    Sets the document title correctly according to the target language.

    See https://github.com/sphinx-doc/sphinx/issues/10282
    """
    if config.language == "de":
        config.project = "Nubus für UCS - Betriebshandbuch"
        config.html_title = config.project
        config.tokenizer_lang = "de_DE"

        # Replace English spelling word list with the German spelling word list
        config.spelling_word_list_filename[0] = "spelling_wordlist_de"

        config.bibtex_bibfiles = ["../bibliography-de.bib"]
        config.intersphinx_mapping = {
            "uv-nubus-manual": (
                "https://docs.software-univention.de/nubus-manual/latest/de",
                None,
            ),
            "uv-ucs-manual": reference_inventory(
                "manual",
                version=version,
                language=config.language,
            ),
            "uv-architecture": reference_inventory("architecture", version=version),
            "uv-keycloak-app": (
                "https://docs.software-univention.de/keycloak-app/latest",
                None,
            ),
            "uv-docs-overview": ("https://docs.software-univention.de/n/de/", None),
            "uv-nubus-customization": (
                "https://docs.software-univention.de/nubus-customization/latest/en/",
                None,
            ),
            "uv-debian-admins": reference_inventory("debian-admins", version=version),
            "linux-kernel-docs": (
                "https://www.kernel.org/doc/html/v6.1/",
                None,
            ),  # UCS 5.2 Kernel is 6.1
        }
        config.numfig_format["code-block"] = "Listing %s"
        config.html_theme_options["announcement"] = """
<p><i class='fa-solid fa-circle-exclamation'></i>
Dieses Dokument befindet sich in Arbeit
und wird das UCS Handbuch ablösen.</br>
Wenn Sie den gesuchten Inhalt nicht finden,
schauen Sie in das
<a href='https://docs.software-univention.de/manual/5.2/de/'
target='_blank' style='color: var(--pst-color-secondary)'>
UCS Handbuch</a>.</p>
"""


def setup(app):
    app.connect(
        "config-inited",
        adapt_settings_to_translation,
    )
