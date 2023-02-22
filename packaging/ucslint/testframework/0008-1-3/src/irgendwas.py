#!/usr/bin/env python
def _(s):
    return s


def main():
    print('Boing')
    print(_('Dieser Test ist ok'))
    print(_('Hier lieg auch %d Problem vor') % 0)
    x = 'hier'
    print(_('Aber %s knallts' % x))
    # _('Im Kommentar %s aber nicht' % x)
    print(_('foo %s bar' % x))
    print(_('foo %s \'bar' % x))  # noqa: Q003
    print(_("foo %s bar" % x))
    print(_("foo %s \"bar" % x))
    print(_('''foo %s bar''' % x))
    print(_("""foo %s bar""" % x))
    print(_('''foo %s \'''bar''' % x))
    print(_("""foo %s \"""bar""" % x))
    print(_('''foo %s bar'''))
    print(_(r"foo %s bar" % x))
    print(_(u'foo %s bar' % x))
    print(_(ur'foo %s bar' % x))  # noqa: E999
    print(_('foo %s bar'
            %
            x))


main()
