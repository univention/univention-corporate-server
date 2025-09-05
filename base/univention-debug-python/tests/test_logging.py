#!/usr/bin/python3
# SPDX-FileCopyrightText: 2024-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import importlib
import logging
import os
import re
import sys

import pytest

import univention.debug as ud
import univention.debug2 as ud2


PROCESS = 25
TRACE = 5


def normalize_logformat(log):
    replacements = {
        # structured date
        re.compile(r'20\d{2}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}[+-]\d{2}:\d{2}', re.M): '2025-01-01T00:00:00.000000+00:00',
        re.compile(r'logging.process:\d+'): 'logging.process:1',
        re.compile(f'pid={os.getpid()}'): 'pid=12345',
        re.compile(r'Traceback \(most recent call last\):(.|\n)*?NameError: name .+ is not defined'): '<TRACEBACK>',
        re.compile(r'Stack \(most recent call last\):(.|\n)*?, i, stack_info=True\)'): '<STACK>',
        re.compile(r'test_logging\.[a-z_]+:\d+'): 'test_module.test_function:1',
        # legacy
        re.compile(r'^\d{2}.\d{2}.\d{2} \d{2}:\d{2}:\d{2}\.\d{3}', re.M): '01.01.25 00:00:00.000',
        re.compile(f': {os.getpid()}:'): ': 12345:',
    }

    def replace_all(line):
        for pattern, replacement in replacements.items():
            line = pattern.sub(replacement, line)
        return line
    return replace_all(log).strip()


# IMPORTANT: order: must be at first
def test_logging_handler_changed():
    m = logging.getLogger('MAIN')
    f = logging.getLogger('foo')
    assert type(m) is logging.Logger
    import univention.logging

    assert type(m) is univention.logging.Logger
    assert type(f) is logging.Logger
    univention.logging.extendLogger('foo', univention_debug_category='MAIN')
    assert type(f) is univention.logging.Logger


# IMPORTANT: order: must be at second
def test_log_structured_with_time(tmp_path):
    import univention.logging as ul
    tmplog = tmp_path / 'log'
    tmplog.touch()
    logger = logging.getLogger('bar')
    handler = logging.FileHandler(str(tmplog))
    logger.addHandler(handler)
    handler.setFormatter(ul.StructuredFormatter(with_date_prefix=True))
    handler.addFilter(ul.SyslogPrefix())
    logger.setLevel(logging.TRACE)

    logger = ul.Structured(logger)
    logger.critical('message', foo='bar')
    logger.error('message', foo='bar')
    logger.exception('message', foo='bar')  # noqa: LOG004
    logger.warning('message', foo='bar')
    logger.process('message', foo='bar')
    logger.info('message', foo='bar')
    logger.debug('message', foo='bar')
    logger.trace('message', foo='bar')
    logger.getChild('blah').error('message', foo='bar')
    assert logger.root
    log = normalize_logformat(tmplog.read_text())
    expected = '''
<2>2025-01-01T00:00:00.000000+00:00 CRITICAL [         -] message\t| pid=12345 logname=bar func=test_module.test_function:1 foo=bar
<3>2025-01-01T00:00:00.000000+00:00    ERROR [         -] message\t| pid=12345 logname=bar func=test_module.test_function:1 foo=bar
<3>2025-01-01T00:00:00.000000+00:00    ERROR [         -] message\t| pid=12345 logname=bar func=test_module.test_function:1 foo=bar
<4>2025-01-01T00:00:00.000000+00:00  WARNING [         -] message\t| pid=12345 logname=bar func=test_module.test_function:1 foo=bar
<5>2025-01-01T00:00:00.000000+00:00  PROCESS [         -] message\t| pid=12345 logname=bar func=test_module.test_function:1 foo=bar
<6>2025-01-01T00:00:00.000000+00:00     INFO [         -] message\t| pid=12345 logname=bar func=test_module.test_function:1 foo=bar
<7>2025-01-01T00:00:00.000000+00:00    DEBUG [         -] message\t| pid=12345 logname=bar func=test_module.test_function:1 foo=bar
<7>2025-01-01T00:00:00.000000+00:00    TRACE [         -] message\t| pid=12345 logname=bar func=test_module.test_function:1 foo=bar
<3>2025-01-01T00:00:00.000000+00:00    ERROR [         -] message\t| pid=12345 logname=bar.blah func=test_module.test_function:1 foo=bar
'''.strip()
    assert log == expected


with open('tests/legacy.log') as fd, open('tests/structured.log') as fd2:
    EXPECTED_LEGACY = fd.read().strip()
    EXPECTED_STRUCTURED = fd2.read().strip()
    EXPECTED = {
        'ud': (EXPECTED_LEGACY, EXPECTED_STRUCTURED),
        'ud2': (EXPECTED_LEGACY, EXPECTED_STRUCTURED),
    }


@pytest.mark.parametrize('strucutured', [True, False])
@pytest.mark.parametrize('debug_backend', ['ud', 'ud2'])
def test_logging(tmp_path, debug_backend, strucutured):
    if debug_backend == 'ud2':
        logging.getLogger('LDAP').destroy()
        sys.modules.pop('univention.logging')
        sys.modules['univention.debug'] = ud2
    else:
        sys.modules.pop('univention.logging', None)
    import univention.logging as ul
    ul = importlib.reload(ul)
    tmplog = tmp_path / 'log'
    tmplog.touch()
    ul.basicConfig(
        filename=str(tmplog),
        level=logging.INFO,
        log_pid=True,
        univention_debug_flush=True,
        univention_debug_function=False,
        do_exit=True,
        use_structured_logging=strucutured,
    )
    logger = logging.getLogger('LDAP')
    logger.univention_debug_handler.set_structured(strucutured)
    logger.error('logger.error("msg")')
    logger.warning('logger.warning("msg")')
    logger.log(PROCESS, 'logger.process("msg")')
    logger.info('logger.info("msg")')
    logger.debug('logger.debug("msg")')  # not shown
    logger.set_log_pid(True)
    child = logger.getChild('foo')
    child.error('logger.getChild("foo").error("msg")')
    child.getChild('bar').error('logger.getChild("foo").getChild("bar").error("msg")')
    logger.critical('logger.critical("msg")')
    logger.set_ud_level(ud.ERROR)
    logger.warning('no warning displayed')  # not shown
    child.warning('no warning displayed')  # not shown
    logger.set_log_pid(False)
    logger.setLevel(logging.DEBUG)
    logger.reopen()
    logger.debug('logger.debug(" after reopen with some spaces ")')
    ud.debug(ud.LDAP, ud.ERROR, 'ud.debug(ud.LDAP, ud.ERROR, "msg")')
    ud.debug(ud.LDAP, ud.WARN, 'ud.debug(ud.LDAP, ud.WARN, "msg")')
    ud.debug(ud.LDAP, ud.PROCESS, 'ud.debug(ud.LDAP, ud.PROCESS, "msg")')
    ud.debug(ud.LDAP, ud.INFO, 'ud.debug(ud.LDAP, ud.INFO, "msg")')
    ud.debug(ud.LDAP, ud.ALL, 'ud.debug(ud.LDAP, ud.ALL, "msg")')
    ud.debug(ud.LDAP, ud.TRACE, 'ud.debug(ud.LDAP, ud.TRACE, "msg")')
    ud.debug(ud.LDAP, 99, 'ud.debug(ud.LDAP, 99, "msg")')
    ud.debug(ud.LDAP, -1, 'ud.debug(ud.LDAP, -1, "msg")')  # not shown
    logger.setLevel(logging.NOTSET + 1)
    logger.log(9, 'logger.log(9, "msg")')
    logger.log(5, 'logger.log(5, "msg")')
    logger.log(4, 'logger.log(4, "msg")')
    logger.log(3, 'logger.log(3, "msg")')
    logger.log(2, 'logger.log(2, "msg")')
    logger.log(1, 'logger.log(1, "msg")')
    logger.log(100, 'logger.log(100, "msg")')
    logger.info({'msg': 'logger.info({"msg": "msg"})'})
    logger.info({'msg': 'logger.info({"msg": "msg %s"}, "addition")'}, '%s')
    logger.info({'msg': 'logger.info({"msg": "msg"}, "foo": "bar")', 'foo': 'bar'})
    logger.info('logger.info("msg", extra={"foo": "bar"})', extra={'foo': 'bar'})
    logger.info('logger.info("msg %s", "addition", extra={"foo": "bar"})', '%s', extra={'foo': 'bar'})
    logger.info('contains null (\x00) byte')
    logger.univention_debug_handler.formatter.add_full_tracebacks = True
    for i in [False, True]:
        logger.univention_debug_handler.formatter.add_full_tracebacks = i
        try:
            foobar()
        except NameError:
            logger.exception('logger.exception("full_tb=%s")', i)
            child.exception('child.exception("full_tb=%s")', i)
        logger.info('logger.info("full_tb=%s", stack_info=True)', i, stack_info=True)

    logger.univention_debug_handler.close()

    actual = normalize_logformat(tmplog.read_text())
    expected = EXPECTED[debug_backend][int(strucutured)].lstrip()
    print('\n' + repr(actual).replace(r'\n', '\n').strip("'"))

    # uncomment to update!
    if strucutured:
        open('tests/structured.log', 'w').write(actual)
    else:
        open('tests/legacy.log', 'w').write(actual)
    assert actual == expected


@pytest.mark.parametrize(
    'ud_level,log_level',
    [
        (ud.ERROR, logging.ERROR),
        (ud.WARN, logging.WARNING),
        (ud.PROCESS, PROCESS),
        (ud.INFO, logging.INFO),
        (ud.ALL, logging.DEBUG),
        (ud.TRACE, TRACE),
        (100, logging.NOTSET),
    ],
)
def test_loglevel_mapping_exact(ud_level, log_level):
    from univention.logging import _map_level_to_ud, _map_ud_to_level

    assert _map_ud_to_level(ud_level) == log_level
    assert _map_level_to_ud(log_level) == ud_level


@pytest.mark.parametrize(
    'ud_level,log_level',
    [
        (x, y)
        for z, y in [
            (range(6, 20), 4),
            ([20], 3),
            (range(21, 30), 3),
            ([30], 3),
            (range(31, 40), 3),
            ([40], 2),
            (range(41, 50), 2),
            ([50], 2),
            (range(51, 60), 2),
            ([60], 1),
            (range(61, 70), 1),
            ([70], 1),
            (range(71, 80), 1),
            ([80], 0),
            (range(81, 90), 0),
            ([90], 0),
            (range(91, 100), 0),
            ([100], 0),
        ]
        for x in z
    ],
)
def test_loglevel_mapping_ud(ud_level, log_level):
    from univention.logging import _map_ud_to_level

    assert _map_ud_to_level(ud_level) == log_level


@pytest.mark.parametrize(
    'log_level,ud_level',
    [
        (0, 100),
        (1, 79),
        (2, 59),
        (3, 39),
        (4, 19),
    ]
    + [
        (x, y)
        for z, y in [
            (range(TRACE, logging.DEBUG), ud.ALL + 1),
            (range(logging.DEBUG, logging.INFO), ud.ALL),
            (range(logging.INFO, PROCESS), ud.INFO),
            (range(PROCESS, logging.WARNING), ud.PROCESS),
            (range(logging.WARNING, logging.ERROR), ud.WARN),
            ([100], ud.ERROR),
        ]
        for x in z
    ]
    + [
        (x, y)
        for y, z in [
            (ud.ERROR, range(logging.ERROR + 1, 101)),
        ]
        for x in z
    ],
)
def test_loglevel_mapping_logging(log_level, ud_level):
    from univention.logging import _map_level_to_ud

    assert _map_level_to_ud(log_level) == ud_level


@pytest.mark.xfail(reason='setLevel is broken')
def test_repr():
    logger = logging.getLogger('ADMIN')
    logger.setLevel(logging.DEBUG)
    assert repr(logger.univention_debug_handler) == '<DebugHandler[ADMIN](DEBUG)>'
    assert repr(logger) == '<univention.logging.Logger ADMIN (DEBUG)>'
