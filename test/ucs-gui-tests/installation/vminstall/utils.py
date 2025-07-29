#!/usr/bin/python2.7
#
# Python VNC automate
#
# SPDX-FileCopyrightText: 2016-2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import subprocess


# TODO: Use the pycountry library here. (Adds additional dependency...)
def iso_639_1_to_iso_639_2(language_code):
    return {'en': 'eng', 'de': 'deu', 'fr': 'fra'}.get(language_code)


def iso_639_1_to_english_name(language_code):
    return {'en': 'English', 'de': 'German', 'fr': 'French'}.get(language_code)


def execute_through_ssh(password, command, ip):
    p = subprocess.Popen((
        'sshpass',
        '-p', password,
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        'root@%s' % (ip,),
        command,
    ), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, _ = p.communicate()
    if p.returncode:
        p = subprocess.Popen((
            'ps', 'aux',
        ), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout_ps, _ = p.communicate()
        raise Exception(p.returncode, stdout, stdout_ps)


def copy_through_ssh(password, source_file, target_file):
    subprocess.check_call((
        'sshpass',
        '-p', password,
        'scp',
        '-r',
        '-o', 'StrictHostKeyChecking=no',
        source_file, target_file,
    ))


def remove_old_sshkey(ip):
    subprocess.check_call((
        'ssh-keygen',
        '-R',
        ip,
    ))
