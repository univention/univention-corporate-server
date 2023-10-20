#!/usr/share/ucs-test/runner python3
## desc: Test comments of atjobs
## tags: [basic]
## packages:
##   - python3-univention-lib
## exposure: safe

from univention.lib import atjobs
from univention.testing import utils


def main():
    comments = {
        'foo\nbar→baz': '\\ ä : \r \n \x00',
        'foo\nbar→': 'blub ä : \r \n \x00',
        'test': 'foobär'.encode('latin1'),
        1: 2,
    }
    expected_comments = {
        'foo\nbar→baz': '\\ ä : \r \n \x00',
        'foo\nbar→': 'blub ä : \r \n \x00',
        'test': 'foobär',
        '1': '2',
    }
    job = atjobs.add('sleep 3', comments=comments,)
    for testjob in atjobs.list(extended=True):
        if testjob.nr == job.nr:
            assert testjob.comments == expected_comments, f'storing comments failed: {testjob.comments!r} != {comments!r}'
            break
    else:
        utils.fail(f'job {job.nr!r} not found in list')


if __name__ == '__main__':
    main()
