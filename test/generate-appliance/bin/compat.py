# SPDX-FileCopyrightText: 2014-2023 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/

__all__ = [
    "BooleanOptionalAction",
]

try:
    from argparse import BooleanOptionalAction  # Py3.9+
except ImportError:
    from argparse import Action, ArgumentParser, Namespace  # noqa: F401
    from typing import Any, Optional  # noqa: F401

    # <https://github.com/python/cpython/blob/3.9/Lib/argparse.py#L862>
    class BooleanOptionalAction(Action):  # type: ignore[no-redef]
        def __init__(self, option_strings, dest, default=None, type=None, choices=None, required=False, help=None, metavar=None):
            # type: (str, str, Optional[bool], Any, Any, bool, Optional[str], Optional[str]) -> None
            _option_strings = []
            for option_string in option_strings:
                _option_strings.append(option_string)

                if option_string.startswith('--'):
                    option_string = '--no-' + option_string[2:]
                    _option_strings.append(option_string)

            if help is not None and default is not None:
                help += " (default: %(default)s)"

            Action.__init__(self, option_strings=_option_strings, dest=dest, nargs=0, default=default, type=type, choices=choices, required=required, help=help, metavar=metavar)

        def __call__(self, parser, namespace, values, option_string=None):
            # type: (ArgumentParser, Namespace, Any, Optional[str]) -> None
            if option_string is not None and option_string in self.option_strings:
                setattr(namespace, self.dest, not option_string.startswith('--no-'))

        def format_usage(self):
            # type: () -> str
            return ' | '.join(self.option_strings)
