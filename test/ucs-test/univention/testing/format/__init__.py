from tap import TAP as format_tap
from text import Text as format_text
from html import HTML as format_html
from jenkins import Jenkins as format_jenkins
FORMATS = [f[7:] for f in dir() if f.startswith('format_')]
