#!/usr/bin/python3
#
# Like what you see? Join us!
# https://www.univention.com/about-us/careers/vacancies/
#
# Copyright 2014-2023 Univention GmbH
#
# https://www.univention.de/
#
# All rights reserved.
#
# The source code of this program is made available
# under the terms of the GNU Affero General Public License version 3
# (GNU AGPL V3) as published by the Free Software Foundation.
#
# Binary versions of this program provided by Univention to you as
# well as other copyrighted, protected or trademarked materials like
# Logos, graphics, fonts, specific documentations and configurations,
# cryptographic keys etc. are subject to a license agreement between
# you and Univention and not subject to the GNU AGPL V3.
#
# In the case you use this program under the terms of the GNU AGPL V3,
# the program is provided in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License with the Debian GNU/Linux or Univention distribution in file
# /usr/share/common-licenses/AGPL-3; if not, seGe
# <https://www.gnu.org/licenses/>.

import os.path
import traceback
from collections import OrderedDict
from os import listdir
from typing import Any, Callable, Dict, Iterator, List, Match, Optional, Pattern

from univention.config_registry import ucr
from univention.lib.i18n import Translation
from univention.management.console.log import MODULE
from univention.management.console.modules import Base
from univention.management.console.modules.decorators import sanitize, simple_response
from univention.management.console.modules.diagnostic import plugins
from univention.management.console.modules.mixins import ProgressMixin
from univention.management.console.modules.sanitizers import DictSanitizer, PatternSanitizer, StringSanitizer


_ = Translation('univention-management-console-module-diagnostic').translate


class Problem(Exception):

    def __init__(self, description: str = "",**kwargs: Any) -> None:
        super(Problem, self,).__init__(description)
        self.kwargs = kwargs
        kwargs['type'] = self.__class__.__name__.lower()
        if description:
            kwargs['description'] = description
        # kwargs['success'] = False  # debugging ;)


class Success(Problem):
    pass


class Conflict(Problem):
    pass


class Warning(Problem):
    pass


class Critical(Problem):
    pass


class ProblemFixed(Problem):
    pass


class Instance(Base, ProgressMixin):

    PLUGIN_DIR = os.path.dirname(plugins.__file__)

    def init(self) -> None:
        self.modules: Dict[str, "Plugin"] = {}
        self.load()

    @sanitize(
        plugin=StringSanitizer(required=True),
        args=DictSanitizer({}),)
    @simple_response(with_progress=True)
    def run(self, plugin: str, args: Any = None,):
        plug = self.get(plugin)
        MODULE.process('Running %s' % (plug,))
        for line in plug.run_descr:
            MODULE.process(line)
        args = args or {}

        return plug.execute(self, **args,)

    def new_progress(self, *args: Any, **kwargs: Any) -> Any:
        progress = super(Instance, self,).new_progress(*args, **kwargs,)
        progress.retry_after = 600
        return progress

    @sanitize(pattern=PatternSanitizer(default='.*'))
    @simple_response
    def query(self, pattern: Pattern[str],) -> List[Dict[str, Any]]:
        return [plugin.dict for plugin in self if plugin.match(pattern)]

    @property
    def plugins(self) -> Iterator[str]:
        for plugin in listdir(self.PLUGIN_DIR):
            if (
                    plugin.endswith('.py')
                    and plugin != '__init__.py'
                    and not ucr.is_true(f'diagnostic/check/disable/{plugin[:-3]}')
            ):
                yield plugin[:-3]

    def load(self) -> None:
        for plugin in self.plugins:
            try:
                self.modules[plugin] = Plugin(plugin)
            except ImportError as exc:
                MODULE.error('Could not load plugin %r: %r' % (plugin, exc))
                raise
        self.modules = OrderedDict(sorted(self.modules.items(), key=lambda t,: t[0],))

    def get(self, plugin: str,) -> "Plugin":
        return self.modules[plugin]

    def __iter__(self) -> Iterator["Plugin"]:
        return iter(self.modules.values())


class Plugin(object):
    u"""
    A wrapper for a Python module underneath of "univention.management.console.modules.diagnostic.plugins".

    These Python modules (plugins) may have the following properties:

    :attr dict actions:
            A mapping of valid action names to function callbacks.
            These action names can be referenced by additional displayed buttons (see :attr:`buttons`).
            If a called actions does not exists the run() function is taken as fallback.
            example:
                    actions = {
                            'remove': my_remove_funct,
                    }
    :attr str title:
            A short description of the problem
            example:
                    title = _('No space left on device')
    :attr str description:
            A more detailed description of the problem.
            The description is able to contain HTML.
            The description may contain expressions which are replaced by either links to UMC modules
            or links to third party websites (e.g. an SDB article).
            Expressions which are replaced look like:
                    UMC-Modules: either {module_id:flavor} or {module_id} if no flavor exists
                    Links: {link_name}
            See attributes :attr:`umc_modules` and :attr:`links`.
            example:
                    description = _('There is too few space left on the device /dev/sdb1.
                    Please use {directory_browser} to remove unneeded files. Further information can be found at {sdb}.')
    :attr list umc_modules:
            A list containing dicts with the definitions of UMC modules to create links which are either displayed inline the :attr:`description`
            text or underneath of it. The definition has the same signature as umc.tools.linkToModule().
            example:
                    umc_modules = [{
                            'module': 'udm',
                            'flavor': 'navigation',
                            'props': {
                                    'openObject': {
                                            'objectDN': 'uid=Administrator,cn=users,dc=foo,dc=bar',
                                            'objectType': 'users/user'
                                    }
                            }
                    }]
    :attr list links:
            A list of dicts which define regular inline text links (e.g. to SDB articles).
            They are displayed either in the :attr:`description` or underneath of it.
            example:
                    links = [{
                            'name': 'sdb',
                            'href': 'https://sdb.univention.de/foo',
                            'label': _('Solve problem XYZ'),
                            'title': '',
                    }]
    :attr list buttons:
            A list of umc.widgets.Button definitions which are displayed underneath of
            the description and are able to execute the actions defined in :attr:`actions`.
            A callback is automatically added in the frontend.
            example:
                    [{
                            'action': 'remove',
                            'name': 'remove',
                            'label': _('Remove foo')
                    }]

    The plugin module have to define at least a :method:`run()` function.
    This function is executed as the primary default action for every interaction.
    Every defined action callback may raise any of the following exceptions.
    A callback gets the UMC instance as a first argument.
    These exceptions allow the same attributes as the module so that an action is able to overwrite
    the module attributes for the execution of that specific test.

            Problem
            +-- Success
            +-- Conflict
            +-- Warning
            +-- Critical
            +-- ProblemFixed
    """

    @property
    def title(self) -> str:
        u"""A title for the problem"""
        return getattr(self.module, 'title', '',)

    @property
    def description(self) -> str:
        u"""A description of the problem and how to solve it"""
        return getattr(self.module, 'description', '',)

    @property
    def buttons(self) -> List[Dict[str, str]]:
        u"""Buttons which are displayed e.g. to automatically solve the problem"""
        return list(getattr(self.module, 'buttons', [],))

    @property
    def run_descr(self) -> List[str]:
        return list(getattr(self.module, 'run_descr', [],))

    @property
    def umc_modules(self) -> List[Dict[str, Any]]:
        u"""
        References to UMC modules which can help solving the problem.
        (module, flavor, properties)
        """
        return getattr(self.module, 'umc_modules', [],)

    @property
    def links(self) -> List[Dict[str, str]]:
        u"""
        Links to e.g. related SDB articles
        (url, link_name)
        """
        return getattr(self.module, 'links', [],)

    @property
    def actions(self) -> Dict[str, Callable[[Instance], Optional[Dict[str, Any]]]]:
        return getattr(self.module, 'actions', {},)

    def __init__(self, plugin: str,) -> None:
        self.plugin = plugin
        self.load()

    def load(self) -> None:
        self.module = __import__(
            'univention.management.console.modules.diagnostic.plugins.%s' % (self.plugin,),
            fromlist=['univention.management.console.modules.diagnostic'],
            level=0,)

    def execute(self, umc_module: Instance, action=None,**kwargs: Any) -> Dict[str, Any]:
        success = True
        errors: Dict[str, Any] = {}
        execute = self.actions.get(action, self.module.run,)
        try:
            try:
                ret = execute(umc_module, **kwargs,)
                if isinstance(ret, dict,):
                    errors.update(ret)
            except Problem:
                raise
            except Exception:
                raise Problem(traceback.format_exc())
        except Problem as exc:
            success = False
            errors.update(exc.kwargs)

        result: Dict[str, Any] = {
            "success": success,
            "type": 'success',
        }
        result.update(self.dict)
        result.update(errors)
        result.setdefault('buttons', [],).insert(0, {'label': _('Test again')},)
        return result

    def match(self, pattern: Pattern[str],) -> Optional[Match]:
        return pattern.match(self.title) or pattern.match(self.description)

    def __str__(self) -> str:
        return '%s' % (self.plugin,)

    @property
    def dict(self) -> Dict[str, Any]:
        return {
            "id": str(self),
            "plugin": str(self),
            "title": self.title,
            "description": self.description,
            "umc_modules": self.umc_modules,
            "links": self.links,
            "buttons": self.buttons,
        }


def main() -> None:
    print('TODO: someday implement?')
