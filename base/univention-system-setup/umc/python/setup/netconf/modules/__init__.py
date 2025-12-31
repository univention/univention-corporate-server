# SPDX-FileCopyrightText: 2004-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""Univention Setup: network configuration abstract base classes"""

import importlib.util
import logging
import os
import sys
from typing import Any

from univention.management.console.modules.setup.netconf import ChangeSet, Phase, SkipPhase


class RunPhases:
    """
    Handle modules for network configuration.
    <http://lkubuntu.wordpress.com/2012/10/02/writing-a-python-plugin-api/>
    """

    def __init__(self) -> None:
        self.classes: list[Any] = []
        self.phases: list[Phase] = []
        self.logger = logging.getLogger("uss.network.plug")

    def load(self) -> None:
        for module_dir in sys.modules[__name__].__path__:
            for dirpath, _dirnames, filenames in os.walk(module_dir):
                self.logger.debug("Processing '%s'...", dirpath)
                for filename in filenames:
                    name, ext = os.path.splitext(filename)
                    if ext not in (".py",):
                        self.logger.debug("Skipping '%s'", filename)
                        continue
                    try:
                        module = importlib.import_module('%s.%s' % (__name__, name))
                    except ImportError:
                        self.logger.warning("Failed to open '%s'", filename)
                        continue
                    except SyntaxError as ex:
                        self.logger.warning("Failed to import '%s': %s", name, ex)
                        continue
                    for key, value in vars(module).items():
                        if not key.startswith('_'):
                            self.add(key, value)
        self.logger.info("Finished loading %d modules", len(self.classes))

    def add(self, name: str, obj: Any) -> None:
        try:
            Phase._check_valid(obj)
            self.logger.info("Adding phase %s", name)
            self.classes.append(obj)
        except SkipPhase as ex:
            self.logger.debug("Phase '%s' is invalid: %s", name, ex)

    def setup(self, changeset: ChangeSet) -> None:
        for clazz in self.classes:
            self.logger.info("Configuring phase %s...", clazz.__name__)
            try:
                phase = clazz(changeset)
                self.logger.debug("Calling %s.check()...", phase)
                phase.check()
                self.logger.info("Adding phase %s as %02d", phase, phase.priority)
                self.phases.append(phase)
            except SkipPhase as ex:
                self.logger.warning("Phase skipped: %s", ex)

    def pre(self) -> None:
        for phase in sorted(self.phases):
            self.logger.info("Calling %s.pre() at %02d...", phase, phase.priority)
            try:
                phase.pre()
            except Exception as ex:
                self.logger.warning("Failed %s.pre(): %s", phase, ex, exc_info=True)

    def post(self) -> None:
        for phase in sorted(self.phases, reverse=True):
            self.logger.info("Calling %s.post() at %02d...", phase, phase.priority)
            try:
                phase.post()
            except Exception as ex:
                self.logger.warning("Failed %s.post(): %s", phase, ex, exc_info=True)
