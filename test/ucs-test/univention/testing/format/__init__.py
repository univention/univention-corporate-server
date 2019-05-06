# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
"""Import all UCS Test formatters."""
from univention.testing.format.tap import TAP as format_tap
from univention.testing.format.text import Text as format_text
from univention.testing.format.html import HTML as format_html
from univention.testing.format.jenkins import Jenkins as format_jenkins
from univention.testing.format.junit import Junit as format_junit
FORMATS = [f[7:] for f in dir() if f.startswith('format_')]
