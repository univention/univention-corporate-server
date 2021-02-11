#!/usr/bin/python3

import xml.etree.ElementTree as ET
import math
import subprocess
import os

STEPS = 48
THEME = 'light'


def main():
	tree = ET.parse(os.path.join(THEME, 'bootsplash-logo.svg'))
	root = tree.getroot()
	background_rect = root.find(
		'./'
		'{http://www.w3.org/2000/svg}g[@{http://www.inkscape.org/namespaces/inkscape}label="Background"]/'
		'{http://www.w3.org/2000/svg}rect[@id="rect-background"]'
	)
	text = root.find(
		'./'
		'{http://www.w3.org/2000/svg}g[@{http://www.inkscape.org/namespaces/inkscape}label="Text"]'
	)
	logo = root.find(
		'./'
		'{http://www.w3.org/2000/svg}g[@{http://www.inkscape.org/namespaces/inkscape}label="Logo"]'
	)
	background_style = background_rect.get('style')
	text.set('style', 'display:none')
	logo.set('style', 'display:none')
	tree.write('logo-box.svg')
	subprocess.check_call(['inkscape', '--export-type=png', 'logo-box.svg'])
	os.remove('logo-box.svg')
	logo.attrib.pop('style')
	for i in range(STEPS):
		opacity = round((1 + math.cos(2 * math.pi * i / STEPS)) * 1 / 2, 2)
		background_rect.set('style', background_style.replace('stroke-opacity:1', 'stroke-opacity:{}'.format(opacity)))
		logo_fname = 'logo{}.svg'.format(i)
		tree.write(logo_fname)
		subprocess.check_call(['inkscape', '--export-type=png', logo_fname])
		os.remove(logo_fname)


if __name__ == '__main__':
	main()
