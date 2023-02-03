import foo  # noqa: F401
import bar  # noqa: F401
def _(s): return s  # noqa: E731


def main():
    print('Boing')
    print(_('Dieser Test ist ok'))
    print(_('Hier lieg auch %d Problem vor') % 0)
    x = 'hier'  # noqa


main()
