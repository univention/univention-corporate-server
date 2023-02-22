#!/usr/bin/python2.4
import foo  # noqa: F401
import bar  # noqa: F401


def main():
    print('Boing')
    print(_('Dieser Test ist ok'))  # noqa: F821
    print(_('Hier lieg auch %d Problem vor') % 0)  # noqa: F821
    x = 'hier'  # noqa: F841


main()
