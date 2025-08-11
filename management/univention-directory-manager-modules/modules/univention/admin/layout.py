# SPDX-FileCopyrightText: 2011-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

"""|UDM| classes to define layouts"""

import copy


class ILayoutElement(dict):
    """Describes the layout information for a tab or a groupbox."""

    def __init__(self, label, description='', layout=[]):
        dict.__init__(self)
        self.__setitem__('label', label)
        self.__setitem__('description', description)
        self.__setitem__('layout', copy.copy(layout))

    @property
    def label(self):
        return self['label']

    @property
    def description(self):
        return self['description']

    @property
    def layout(self):
        return self['layout']

    @layout.setter
    def layout(self, value):
        self['layout'] = value

    def replace(self, old, new, recursive=True):
        new_layout = []
        replaced = False
        for item in self.layout:
            if replaced:
                new_layout.append(item)
                continue
            if isinstance(item, str) and item == old:
                new_layout.append(new)
                replaced = True
            elif isinstance(item, tuple | list):
                line = []
                for elem in item:
                    if elem == old:
                        replaced = True
                        line.append(new)
                    else:
                        line.append(elem)
                new_layout.append(line)
            elif isinstance(item, ILayoutElement) and recursive:
                replaced, _layout = item.replace(old, new, recursive)
                new_layout.append(item)
            else:
                new_layout.append(item)
        self.layout = new_layout

        return (replaced, self.layout)

    def remove(self, field, recursive=True):
        new_layout = []
        removed = False
        if self.exists(field):
            for item in self.layout:
                if removed:
                    new_layout.append(item)
                    continue
                if isinstance(item, str) and item != field:
                    new_layout.append(item)
                elif isinstance(item, tuple | list):
                    line = []
                    for elem in item:
                        if elem != field:
                            line.append(elem)
                        else:
                            removed = True
                    new_layout.append(line)
                elif isinstance(item, ILayoutElement) and recursive:
                    removed, _layout = item.remove(field, recursive)
                    new_layout.append(item)
                else:
                    removed = True
            self.layout = new_layout

        return (removed, self.layout)

    def exists(self, field):
        for item in self.layout:
            if isinstance(item, str) and item == field:
                return True
            elif isinstance(item, tuple | list):
                if field in item:
                    return True
            elif isinstance(item, ILayoutElement) and item.exists(field):
                return True

        return False

    def insert(self, position, field):
        if position == -1:
            self.layout.insert(0, field)
            return

        fline = (position - 1) // 2
        fpos = (position - 1) % 2

        currentLine = fline

        if len(self.layout) <= currentLine or currentLine < 0:
            self.layout.append(field)
        else:
            if isinstance(self.layout[currentLine], str):
                if fpos == 0:
                    self.layout[currentLine] = [field, self.layout[currentLine]]
                else:
                    self.layout[currentLine] = [self.layout[currentLine], field]
            else:
                self.layout[currentLine].insert(fpos, field)


class Tab(ILayoutElement):

    def __init__(self, label, description='', advanced=False, layout=[], is_app_tab=False, help_text=None):
        ILayoutElement.__init__(self, label, description, layout)
        self.__setitem__('advanced', advanced)
        self.__setitem__('is_app_tab', is_app_tab)
        self.__setitem__('help_text', help_text)

    @property
    def is_app_tab(self):
        return self['is_app_tab']

    @is_app_tab.setter
    def is_app_tab(self, value):
        self['is_app_tab'] = value

    @property
    def advanced(self):
        return self['advanced']

    @advanced.setter
    def advanced(self, value):
        self['advanced'] = value


class Group(ILayoutElement):
    pass
