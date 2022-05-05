#!/usr/bin/env python3
import argparse
from configparser import ConfigParser, NoOptionError
import re
import os


# path pattern matching for excluded directories
EXCLUDED_DIRECTORIES = [
    "ucslint",
    "univention-package-template",
]

parser = argparse.ArgumentParser(description="Convert UCR variable documentation to RST and PO")
parser.add_argument("-u", "--ucs_path", type=str)
parser.add_argument("-o", "--rst_outpath", type=str)

args = parser.parse_args()


if args.ucs_path is None:
    ucs_path = f"{os.getenv('HOME')}/git/ucs/"
else:
    ucs_path = args.ucs_path

if not os.path.exists(ucs_path):
    print(f"Path {ucs_path} does not exist.")
    quit()

if args.rst_outpath is None:
    rst_output_path = os.path.join(ucs_path, "doc/manual/ucr-variables.rst")
else:
    rst_output_path = args.rst_output_path

ucrvar_data = {}

def read_config_registry(filename):

    ucrvar_parser = ConfigParser()
    with open(filename, "r", encoding="utf-8", errors="replace") as f:
        ucrvar_parser.read_file(f)

    for ucrvar_name in ucrvar_parser.sections():

        ucrvar_name_escaped = ucrvar_name.replace("/*", "/.*")

        ucrvar_data[ucrvar_name_escaped] = {}
        try:
            ucrvar_data[ucrvar_name_escaped]["de"] = ucrvar_parser.get(ucrvar_name, "Description[de]", raw=True)
            ucrvar_data[ucrvar_name_escaped]["en"] = ucrvar_parser.get(ucrvar_name, "Description[en]", raw=True)
        except (KeyError, NoOptionError):
            print(f"Warning: The description for the following variable is missing: {ucrvar_name} (in {filename})")
            del ucrvar_data[ucrvar_name_escaped]

def collate(text, size):
    """wrap lines which are longer than size
    """
    new_text = []
    split_char = 1
    while split_char > 0:
        comma = str.find(text, ',', size)
        space = str.find(text, ' ', size)
        dot = str.find(text, '.', size)

        split_char = min(max(comma, dot), max(comma, space), max(dot, space))

        if text[:split_char]:
            new_text.append(text[:split_char])
        text = text[split_char+1:].replace('\n', "")

    return new_text

for root, dirs, files in os.walk(ucs_path):

    for directory in dirs:
        if directory in EXCLUDED_DIRECTORIES:
            dirs.remove(directory)

    for name in files:
        if name.endswith(".univention-config-registry-variables"):
            filepath = os.path.join(root, name)
            read_config_registry(filepath)


OUTPUT = \
r"""************
|UCSUCRV|\ s
************

This appendix lists the |UCSUCRV|\ s mentioned in the document.
"""

VAR_DESC = \
r"""
.. envvar:: {}

   {}
"""

for ucrvar_name in sorted(ucrvar_data):
    description = "\n   ".join([s.strip() for s in collate(ucrvar_data[ucrvar_name]["en"], 75)])

    if description[-1] != ".":
        description += "."

    OUTPUT += VAR_DESC.format(ucrvar_name, description)

print(OUTPUT)
with open(rst_output_path, "w") as f:
    f.write(OUTPUT)


