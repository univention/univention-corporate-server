#!/usr/bin/env python3.9
# -*- coding: utf-8 -*-

"""
Run the following transformation on an already prepared RST document.
For the preparation see https://git.knut.univention.de/groups/univention/-/epics/168#note_53232

The preparations include:

* Transform labels to the schema ``.. _<label>:``.
  The label is all small caps. Colons (:) are transformed to hyphens (-).

* Pandoc uses another hierarchy for the headings that don't conform to the
  Univention style guide. The heading hierarchy is adapted accordingly.

* Pandoc does not know the ``:ref:`` role from Sphinx. Internal references
  are plain RST links. Those references are transformed to ``:ref:`` roles.
"""
import abc
import argparse
import logging
import re
import sys

from os import path
from os import linesep
from typing import List


def read_file(f_name: str) -> List[str]:
    f = open(f_name, "r")
    content = f.readlines()
    f.close()
    return content


def _subst_label(label: str) -> str:
    repl = re.compile(r'([:_])')
    multi_dash = re.compile(r'-{2,}')
    result = repl.sub('-', label)
    return multi_dash.sub('-', result)


def _subst_target(match):
    result = _subst_label(match.group(1))
    return f":ref:`{result}`"


def conform_labels(line: str) -> str:
    """
    Convert the transformed labels to the form we need

    * Replace : with -
    * Avoid multiple dashes in a row
    * make the label lower case
    """
    pattern = re.compile(r'^(.. _)(.+)(:)([\n\r]$)')
    m = pattern.match(line)
    if m:
        result = _subst_label(m.group(2))
        result = f"{m.group(1)}{result.lower()}{m.group(3)}{m.group(4)}"
        return result
    else:
        return line


def _subst_heading(pattern, line, subst, replace) -> str:
    m = pattern.match(line)
    subst_pattern = re.compile(subst)
    if m:
        return subst_pattern.sub(replace, line)
    else:
        return line


def conform_headings(line: str) -> str:
    patterns = {
        "chap": (re.compile(r'^(=+)\S$'), r"=", "*"),
        "sect": (re.compile(r'^(-+)\S$'), r"-", "="),
        "subsect": (re.compile(r'^(~+)\S$'), r"~", "-"),
    }
    new_line = line
    for value in patterns.values():
        pattern = value[0]
        subst = value[1]
        replace = value[2]
        result = _subst_heading(pattern, line, subst, replace)
        if result == line:
            continue
        else:
            new_line = result
    return new_line


def conform_refs(content: str) -> List[str]:
    pattern = re.compile(r"`(.+|.+\n.+|.+\n.+\n.+) <#(.+)>`(__)")
    result, replacements = pattern.subn(r":ref:`\2`", content)

    pattern = re.compile(r":ref:`(.+)`")
    result, replacements = pattern.subn(_subst_target, result)
    logging.info("%s references changes to conform to style guide.", replacements)
    return result


class ReplacementBase(object):
    def __init__(self, content: str):
        self.content = content

    def replace(self):
        pattern = re.compile(
            r"(@@" +
            re.escape(self.keyword) +
            "@@>)(.+|.*\n.*)(</" +
            re.escape(self.keyword) + ">)"
        )
        result, replacements = pattern.subn(self.substitute_pattern, self.content)
        logging.info("%s replacements for the keyword >%s<.", replacements, self.keyword)
        return result

    @property
    @abc.abstractmethod
    def keyword(self) -> str:
        raise NotImplemented()

    @property
    @abc.abstractmethod
    def substitute_pattern(self) -> str:
        raise NotImplemented()


class ReplacementRole(ReplacementBase):
    @property
    def substitute_pattern(self) -> str:
        return rf":{self.role}:`\2`"

    @property
    @abc.abstractmethod
    def keyword(self) -> str:
        raise NotImplemented()

    @property
    @abc.abstractmethod
    def role(self) -> str:
        raise NotImplemented()


class ReplacementEmphasis(ReplacementBase):
    @property
    def keyword(self) -> str:
        return "emphasis"

    @property
    def substitute_pattern(self) -> str:
        return r"*\2*"


class ReplacementForeign(ReplacementEmphasis):
    @property
    def keyword(self) -> str:
        return "foreignphrase"


class ReplacementGuimenu(ReplacementRole):
    @property
    def keyword(self) -> str:
        return "guimenu"

    @property
    def role(self) -> str:
        return "guilabel"


class ReplacementFilename(ReplacementRole):
    @property
    def keyword(self) -> str:
        return "filename"

    @property
    def role(self) -> str:
        return "file"

    def replace(self):
        pattern = re.compile(r'(@@filename@@)(( |\n)class="directory")?>(.+|.*\n.*)(</filename>)')
        result, replacements = pattern.subn(self.substitute_pattern, self.content)
        logging.info("%s replacements for the keyword >%s<.", replacements, self.keyword)
        return result

    @property
    def substitute_pattern(self) -> str:
        return rf":{self.role}:`\4`"


class ReplacementEnvar(ReplacementRole):
    @property
    def keyword(self) -> str:
        return "envar"

    @property
    def role(self) -> str:
        return "envvar"


class ReplacementPackage(ReplacementRole):
    @property
    def keyword(self) -> str:
        return "package"

    @property
    def role(self) -> str:
        return "program"


class ReplacementApplication(ReplacementPackage):
    @property
    def keyword(self) -> str:
        return "application"


class ReplacementCommand(ReplacementRole):
    @property
    def keyword(self) -> str:
        return "command"

    @property
    def role(self) -> str:
        return self.keyword


class ReplacementLiteral(ReplacementBase):
    @property
    def keyword(self) -> str:
        return "literal"

    @property
    def substitute_pattern(self) -> str:
        return r"``\2``"


class ReplacementProperty(ReplacementLiteral):
    @property
    def keyword(self) -> str:
        return "property"


class ReplacementUserinput(ReplacementLiteral):
    @property
    def keyword(self) -> str:
        return "userinput"


class ReplacementWordasword(ReplacementBase):
    @property
    def keyword(self) -> str:
        return "wordasword"

    @property
    def substitute_pattern(self) -> str:
        return r"\2"


class ReplacementUri(ReplacementLiteral):
    @property
    def keyword(self) -> str:
        return "uri"


class ReplacementSystemitem(ReplacementBase):
    @property
    def keyword(self) -> str:
        return "systemitem"

    @property
    def substitute_pattern(self) -> str:
        return r"``\2``"

    def replace(self):
        pattern = re.compile(r'@@systemitem@@( |\n)class=".+">(.+)</systemitem>')
        result, replacements = pattern.subn(self.substitute_pattern, self.content)
        logging.info("%s replacements for the keyword >%s<.", replacements, self.keyword)
        return result


class ReplacementFigure(ReplacementBase):
    @property
    def keyword(self) -> str:
        return "figure"

    def replace(self):
        pattern = re.compile(
            r'@@figure@@ id="(.+)">\n' +
            r'@@graphic@@ scalefit=".+" width=".+"\n' +
            r'fileref="(.+)"/> ?</figure>'
        )

        result, replacements = pattern.subn(self._substitute, self.content)
        logging.info("%s replacements for the keyword >%s<.", replacements, self.keyword)
        return result

    @staticmethod
    def _substitute(match):
        figure_path_pattern = re.compile(r"(illustrations50)/(.+)[-_](en|EN)\.png")
        figure_path = figure_path_pattern.sub(r"/images/\2.*", match.group(2))
        return f".. _{match.group(1)}:{linesep}{linesep}.. figure:: {figure_path}{linesep}"


def transform_keywords(content: str) -> List[str]:
    keywords = {
        "envar": ReplacementEnvar,
        "guimenu": ReplacementGuimenu,
        "emphasis": ReplacementEmphasis,
        "package": ReplacementPackage,
        "application": ReplacementApplication,
        "command": ReplacementCommand,
        "filename": ReplacementFilename,
        "literal": ReplacementLiteral,
        "wordasword": ReplacementWordasword,
        "systemitem": ReplacementSystemitem,
        "userinput": ReplacementUserinput,
        "uri": ReplacementUri,
        "figure": ReplacementFigure,
        "foreignphrase": ReplacementForeign,
        "property": ReplacementProperty,
#        "phrase": ,
#        "option": ,
#        "function": ,
#        "replaceable": ,
#        "u:": ,
#        "keycap": ,
#        "mousebutton": ,
#        "biblioref":,
    }
    result = content
    for replace in keywords.values():
        inst = replace(result)
        result = inst.replace()
    return result


def conform_codeblock(content: str) -> str:
    pattern = re.compile(r".. code:: sh")
    result, replacements = pattern.subn(r".. code-block:: console", content)
    logging.info("%s replacements for mal-formed code blocks.", replacements)
    return result


def remove_whitespaces(content: str) -> str:
    pattern = re.compile(r"^ +$", re.MULTILINE)
    result, replacements = pattern.subn(r"", content)
    logging.info("%s white space lines removed.", replacements)
    return result


def main(f_name: str):
    content = read_file(f_name)
    content = list(map(conform_labels, content))
    content = list(map(conform_headings, content))
    content_str = "".join(content)
    content_str = conform_refs(content_str)
    content_str = transform_keywords(content_str)
    content_str = conform_codeblock(content_str)
    content_str = remove_whitespaces(content_str)
    print(content_str)


if __name__ == "__main__":
    loglevel: int = logging.WARNING

    parser = argparse.ArgumentParser(
        description="After preparing the RST file according to "
                    "https://git.knut.univention.de/groups/univention/-/epics/168#note_53232"
                    " this script runs all the post processing to reduce manual work."
    )

    parser.add_argument(
        "-f", "--file",
        dest="filename",
        action="store",
        help="The RST file that needs the post processing.",
        type=str,
    )
    parser.add_argument(
        "-v", "--verbose",
        dest="verbose",
        default=False,
        action="store_true",
        help="Set loglevel to info"
    )
    parser.add_argument(
        "-d", "--debug",
        dest="debug",
        default=False,
        action="store_true",
        help="Set loglevel to debug"
    )

    if len(sys.argv) == 1:
        logging.error("The filename -f is missing.")
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if args.verbose:
        loglevel = logging.INFO
    elif args.debug:
        loglevel = logging.DEBUG

    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

    if path.exists(args.filename):
        filename = path.abspath(args.filename)
        logging.info("Work on file %s.", filename)
        main(filename)
