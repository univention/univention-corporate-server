import foo  # noqa
import bar  # noqa
def _(s): return s  # noqa: E731,E704


def main():
    print('Boing')
    print(_('Dieser Test ist ok'))
    print(_('Hier lieg auch %d Problem vor') % 0)
    x = 'hier'  # noqa


main()
