import univention.management  # noqa: F401


def test_import():
    # we only test basic import of a no-op module here currently
    # as UMC imports univention.admin and we cannot add this as build
    # dependency, otherwise we would have a cyclic build dependencies
    # a real approach to add unit tests here, would probablby mock away
    # univention.admin
    import univention.management.console
    assert univention.management.console
