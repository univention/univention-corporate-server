#
# Univention Directory Reports
#  token classes
#
# SPDX-FileCopyrightText: 2007-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only


class Token:

    def __init__(self, name=None, attrs={}, data=None):
        self.name = name
        self.attrs = attrs
        self.data = data

    def __repr__(self):
        return '<%s %r %r %d>' % (type(self).__name__, self.name, self.attrs, len(self.data or ''))

    def __bool__(self):
        return self.name is not None

    __nonzero__ = __bool__


class TextToken(Token):

    def __init__(self, text=''):
        Token.__init__(self, name='<empty>', data=text)

    def __str__(self):
        return self.data


class TemplateToken(Token):

    def __init__(self, name, attrs={}):
        Token.__init__(self, name, attrs)

    def __str__(self):
        attrs = ''
        for key, value in self.attrs.items():
            attrs += '%s="%s" ' % (key, value)
        return '<@%s %s@>' % (self.name, attrs[: -1])


class IContextToken(TemplateToken, list):

    def __init__(self, name, attrs, closing):
        TemplateToken.__init__(self, name, attrs)
        list.__init__(self)
        self.closing = closing
        self.objects = []

    def clear(self):
        while self.__len__():
            self.pop()

    def __str__(self):
        content = ''
        for item in self:
            content += str(item)
        return TemplateToken.__str__(self) + content + '<@/%s@>' % self.name


class ResolveToken(IContextToken):

    def __init__(self, attrs={}, closing=False):
        IContextToken.__init__(self, 'resolve', attrs, closing)


class QueryToken(IContextToken, list):

    def __init__(self, attrs={}, closing=False):
        IContextToken.__init__(self, 'query', attrs, closing)


class HeaderToken(IContextToken, list):

    def __init__(self, attrs={}, closing=False):
        IContextToken.__init__(self, 'header', attrs, closing)


class FooterToken(IContextToken, list):

    def __init__(self, attrs={}, closing=False):
        IContextToken.__init__(self, 'footer', attrs, closing)


class AttributeToken(TemplateToken):

    def __init__(self, attrs={}, value=''):
        TemplateToken.__init__(self, 'attribute', attrs)
        self.value = value


class PolicyToken(TemplateToken):

    def __init__(self, attrs={}, value=''):
        TemplateToken.__init__(self, 'policy', attrs)
        self.value = value


class DateToken(TemplateToken):

    def __init__(self, attrs={}, value=''):
        TemplateToken.__init__(self, 'date', attrs)
        self.value = value
