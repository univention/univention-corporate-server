#!/usr/bin/python
"""Generate noscript.html index file."""

import os
from optparse import OptionParser


def generate(lang):
	"""Generate noscript.html for languag."""
	with open('noscript.html', 'w') as out:
		out.write('<html>\n')
		out.write('\t<head><title>UCS documentation</title></head>\n')
		out.write('\t<body>\n')
		out.write('\t\t<dl>\n')
		for root, _dirs, files in os.walk(lang):
			for filename in files:
				if filename.endswith('_docs.txt'):
					doc_list = open(os.path.join(root, filename), "r")
					for line in doc_list:
						title, html, pdf = line.strip().split('; ')
						out.write('\t\t\t<dt>%s</dt>\n' % title)
						out.write('\t\t\t<dd><a href="%s">%s</a> <a href="%s">%s</a></dd>\n' % (
							os.path.basename(html),
							os.path.basename(html),
							os.path.basename(pdf),
							os.path.basename(pdf),
							))
					doc_list.close()
		out.write('\t\t</dl>\n')
		out.write('\t\t<p><img src="http://piwik.univention.de/piwik.php?idsite=11" style="border:0" alt="" /></p>\n')
		out.write('\t\t<p><img src="http://piwik.univention.de/piwik.php?idsite=10" style="border:0" alt="" /></p>\n')
		out.write('\t</body>\n')
		out.write('</html>')


def main():
	"""Generare noscript.html for index file."""
	parser = OptionParser()
	parser.add_option('-l', '--language',
			dest='lang', type='string', action='store', default='en',
			help='Directory name by language code [%default]')
	options, _args = parser.parse_args()

	generate(options.lang)


if __name__ == '__main__':
	main()
