# SPDX-FileCopyrightText: 2018-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

from __future__ import annotations

import importlib
import os.path
from glob import glob
from typing import TYPE_CHECKING, Any, cast


if TYPE_CHECKING:
    from collections.abc import Iterator


class Plugin(type):
    """Meta class for plugins."""

    def __new__(mcs: type[Plugin], name: str, bases: tuple[type, ...], attrs: dict[str, Any]) -> Plugin:
        new_cls = cast(Plugin, super().__new__(mcs, name, bases, attrs))
        Plugins.add_plugin(new_cls)
        return new_cls


class Plugins:
    """Register `Plugin` subclasses and iterate over them."""

    _plugins: list[Plugin] = []
    _imported: dict[str, bool] = {}

    def __init__(self, python_path: str) -> None:
        """
        :param str python_path: fully dotted Python path that the plugins will
                be found below
        """
        self.python_path = python_path
        self._imported.setdefault(python_path, False)

    @classmethod
    def add_plugin(cls, plugin: Plugin) -> None:
        """
        Called by `Plugin` meta class to register a new `Plugin` subclass.

        :param type plugin: a `Plugin` subclass
        """
        cls._plugins.append(plugin)

    def __iter__(self) -> Iterator[Plugin]:
        """
        Iterator for registered `Plugin` subclasses.

        :return: `Plugin` subclass
        """
        self.load()
        for plugin in self._plugins:
            if plugin.__module__.startswith(self.python_path):
                yield plugin

    def load(self) -> None:
        """Load plugins."""
        if self._imported.get(self.python_path):
            return
        base_module = importlib.import_module(self.python_path)
        assert base_module.__file__
        base_module_dir = os.path.dirname(base_module.__file__)
        path = os.path.join(base_module_dir, '*.py')
        for pymodule in glob(path):
            pymodule_name = os.path.basename(pymodule)[:-3]  # without .py
            importlib.import_module(f'{self.python_path}.{pymodule_name}')
        self._imported[self.python_path] = True
