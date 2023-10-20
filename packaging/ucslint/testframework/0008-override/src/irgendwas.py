import foo  # noqa: F401
import bar  # noqa: F401
def _(s,): return s  # noqa: E731,E704


def main():
    print('Boing')
    print(_('Dieser Test ist ok'))
    print(_('Hier lieg auch %d Problem vor') % 0)
    x = 'hier'
    print(_('Aber %s knallts' % x))


main()
