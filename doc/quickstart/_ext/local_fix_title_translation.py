"""
This local extension ensures that the document title is correctly set according
to the target language of the project.

See https://github.com/sphinx-doc/sphinx/issues/10282
"""


def fix_title(app, config):
    if config.language == "de":
        config.project = "Quickstart Guide für Univention Corporate Server"
        config.html_title = config.project


def setup(app):
    app.connect(
        "config-inited",
        fix_title,
    )
