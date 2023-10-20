# For umc/python/updater/__init__.py::HookManager


def test_hook(*args, **kwargs):
    print('2ND_TEST_HOOK:', args, kwargs)
    return ('Result', 2)


def register_hooks():
    return [
        ('test_hook', test_hook),
    ]
