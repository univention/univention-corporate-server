#!/usr/share/ucs-test/runner python3
## desc: Basic check of univention.lib.atjobs
## bugs: [36809]
## tags: [basic]
## packages:
##   - python3-univention-lib
## exposure: dangerous

import datetime
from subprocess import PIPE, Popen

from univention.lib import atjobs
from univention.testing import strings, utils


def get_output(cmd,):
    p = Popen(cmd, stdout=PIPE, stderr=PIPE,)
    return (b'%s\n%s' % p.communicate()).decode('UTF-8')


def print_job(job, msg='',):
    print(f'{msg}{job!r}\nNumber: {job.nr!r}\nCommand: {job.command!r}\nComments: {job.comments!r}\nExecTime: {job.execTime!r}\nOwner: {job.owner!r}')


def main():
    # save old job list
    old_atq_output = get_output('atq')

    job_number = None
    job_command = 'echo %s' % (strings.random_name())
    job_comments = {}
    for _i in range(10):
        job_comments[strings.random_name()] = strings.random_string(length=30)

    try:
        job = atjobs.add(job_command, execTime=(datetime.datetime.now() + datetime.timedelta(days=3)), comments=job_comments,)
        job_number = job.nr
        print_job(job, '\nCreated atjob ',)

        for testjob in atjobs.list(extended=True):
            if testjob.nr == job.nr:
                print_job(testjob, '\nFound job ',)
                if testjob.command.strip() != job_command:
                    utils.fail(f'Jobs differ: {testjob.command!r}  <==>  {job_command!r}')
                if testjob.comments != job_comments:
                    utils.fail(f'Jobs differ: {testjob.comments!r}  <==>  {job_comments!r}')
                if testjob.execTime != job.execTime:
                    utils.fail(f'Jobs differ: {testjob.execTime!r}  <==>  {job.execTime!r}')
                if testjob.owner != job.owner:
                    utils.fail(f'Jobs differ: {testjob.owner!r}  <==>  {job.owner!r}')

                testjob2 = atjobs.load(testjob.nr, extended=True,)
                print_job(testjob2, '\nExplicitely loaded job ',)
                if testjob2.command.strip() != job_command:
                    utils.fail(f'Jobs differ: {testjob2.command!r}  <==>  {job_command!r}')
                if testjob2.comments != job_comments:
                    utils.fail(f'Jobs differ: {testjob2.comments!r}  <==>  {job_comments!r}')
                if testjob2.execTime != job.execTime:
                    utils.fail(f'Jobs differ: {testjob2.execTime!r}  <==>  {job.execTime!r}')
                if testjob2.owner != job.owner:
                    utils.fail(f'Jobs differ: {testjob2.owner!r}  <==>  {job.owner!r}')
                break
        else:
            utils.fail(f'job {job.nr!r} not found in list')
    finally:
        atjobs.remove(job_number)

        new_atq_output = get_output('atq')
        if old_atq_output != new_atq_output:
            print('old_atq_output = %r' % (old_atq_output))
            print('new_atq_output = %r' % (new_atq_output))
            utils.fail('old and new atq output differ! remove() may have failed')


if __name__ == '__main__':
    main()
