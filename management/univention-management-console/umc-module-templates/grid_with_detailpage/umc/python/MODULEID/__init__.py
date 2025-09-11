#!/usr/bin/python3
#
# Univention Management Console module:
#   MODULEDESC
#
# SPDX-FileCopyrightText: YEAR Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import uuid

from univention.lib.i18n import Translation
from univention.management.console.base import Base
from univention.management.console.log import MODULE
from univention.management.console.modules.decorators import sanitize
from univention.management.console.modules.sanitizers import StringSanitizer


_ = Translation('PACKAGENAME').translate


class Instance(Base):

    # list of dummy entries
    entries = [{'id': str(uuid.uuid4()), 'name': x[0], 'color': x[1]} for x in [
        ['Zackary Cavaco', 'Blue'],
        ['Shon Hodermarsky', 'Green'],
        ['Jude Nachtrieb', 'Green'],
        ['Najarian', 'Blue'],
        ['Oswaldo Lefeld', 'Blue'],
        ['Vannessa Kopatz', 'Orange'],
        ['Marcellus Hoga', 'Orange'],
        ['Violette Connerty', 'Orange'],
        ['Lucina Jeanquart', 'Blue'],
        ['Mose Maslonka', 'Green'],
        ['Emmie Dezayas', 'Green'],
        ['Douglass Glaubke', 'Green'],
        ['Deeann Delilli', 'Blue'],
        ['Janett Cooch', 'Orange'],
        ['Ike Collozo', 'Orange'],
        ['Tamala Pecatoste', 'Orange'],
        ['Shakira Cottillion', 'Blue'],
        ['Colopy', 'Blue'],
        ['Vivan Noggles', 'Green'],
        ['Shawnda Hamalak', 'Blue'],
    ]]

    def init(self):
        # this initialization method is called when the module process is created
        super().init()

    def colors(self, request):
        """Returns a list of all existing colors."""
        MODULE.info('MODULEID.colors: options: %r', request.options)
        allColors = {x['color'] for x in Instance.entries}
        allColors = [{'id': x, 'label': x} for x in allColors]
        allColors.append({'id': 'None', 'label': _('All colors')})
        MODULE.info('MODULEID.colors: result: %r', allColors)
        self.finished(request.id, allColors)

    def query(self, request):
        """
        Searches for entries in a dummy list

        request.options = {}
        'name' -- search pattern for name (default: '')
        'color' -- color to match, 'None' for all colors (default: 'None')

        return: [ { 'id' : <unique identifier>, 'name' : <display name>, 'color' : <name of favorite color> }, ... ]
        """
        MODULE.info('MODULEID.query: options: %r', request.options)
        color = request.options.get('color', 'None')
        pattern = request.options.get('name', '')
        result = [x for x in Instance.entries if (color in ('None', x['color'])) and x['name'].find(pattern) >= 0]
        MODULE.info('MODULEID.query: results: %r', result)
        self.finished(request.id, result)

    @sanitize(StringSanitizer())
    def get(self, request):
        """
        Returns the objects for the given IDs

        request.options = [ <ID>, ... ]

        return: [ { 'id' : <unique identifier>, 'name' : <display name>, 'color' : <name of favorite color> }, ... ]
        """
        MODULE.info('MODULEID.get: options: %r', request.options)
        ids = set(request.options)
        result = [x for x in Instance.entries if x['id'] in ids]
        MODULE.info('MODULEID.get: results: %r', result)
        self.finished(request.id, result)
