import re


def expand_path(xpath):
	# replaces instances of [@containsClass="className"]
	# with
	# [contains(concat(" ", normalize-space(@class), " "), " className ")]
	pattern = r'(?<=\[)@containsClass=([\"\'])(.*?)\1(?=\])'
	replacement = r'contains(concat(\1 \1, normalize-space(@class), \1 \1), \1 \2 \1)'
	return re.sub(pattern, replacement, xpath)
