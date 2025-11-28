#!/usr/bin/python3
# Univention UCS
# SPDX-FileCopyrightText: 2025 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

import mmap
import re
# import shlex
import subprocess
from argparse import ArgumentParser


parser = ArgumentParser(description="check connecector log for Tracebacks")
parser.add_argument('-v', dest='verbose', help='verbose', action='count', default=0)
parser.add_argument('-x', dest='exclude', help='exclude DNs from file', action='store')
parser.add_argument("dn", nargs='*', help="Active Directory DN to resync")
options = parser.parse_args()

re_modtype = re.compile(b".*('dn': '[^']*').*(, 'modtype': '[\\w]*').*")

with open(options.dn[0], "r+b", buffering=0) as f:
    with mmap.mmap(f.fileno(), 0, flags=mmap.MAP_POPULATE | mmap.MAP_PRIVATE, prot=mmap.PROT_READ) as mm:
        mm.madvise(mmap.MADV_SEQUENTIAL)
        # mm.madvise(mmap.MADV_WILLNEED)
        line = mm.readline()
        while line:
            i = line.find(b'Resync rejected dn:')
            if i != -1:
                rejdn = line[i + 20:].decode('UTF-8').rstrip()
                if options.exclude:
                    result = subprocess.run(["grep", "-q", rejdn.replace('\\', '\\\\'), options.exclude], check=False)
                    if result.returncode == 0:
                        line = mm.readline()
                        continue
                print("\n# Resync: " + rejdn)
                line = mm.readline()
                while line:
                    if b'Resync rejected dn:' in line:
                        break
                    elif b'Unknown Exception' in line or b'During handling of the above exception' in line or b'Traceback' in line:
                        while line != b'\n':
                            print(line.decode('UTF-8'), end='')
                            line = mm.readline()
                        print()
                    elif b'ERROR' in line:
                        print(line.decode('UTF-8'), end='')
                        line = mm.readline()
                    elif b'object_from_element: ' in line:
                        if options.verbose > 0:
                            print(line.decode('UTF-8'), end='')
                        line = mm.readline()
                    elif b'old_ad_object: ' in line:
                        if options.verbose > 1:
                            print(line.decode('UTF-8'), end='')
                        line = mm.readline()
                    elif b'get_ucs_object: ' in line:
                        print(line.decode('UTF-8'), end='')
                        line = mm.readline()
                    elif b'sync to ucs: ' in line:
                        print(line.decode('UTF-8'), end='')
                        line = mm.readline()
                    elif b'object_out : ' in line:
                        if options.verbose > 0:
                            mt = re_modtype.match(line)
                            if mt:
                                print(line[:line.find(b'object_out : ')].decode('UTF-8'), end='')
                                print(mt[1].decode('UTF-8'), end='')
                                print(mt[2].decode('UTF-8'))
                        line = mm.readline()
                    elif b'sync to ucs was not successful' in line:
                        print(line.decode('UTF-8'), end='')
                        break
                    elif b'rejected change with id' in line:
                        print(line.decode('UTF-8'), end='')
                        break
                    else:
                        line = mm.readline()
                print()
            # elif b'_ignore_object: Do not ignore' in line:
            #     print(line.decode('UTF-8'))
            #     line = mm.readline()
            # elif b'object_from_element: ' in line:
            #     print(line.decode('UTF-8'))
            #     line = mm.readline()
            elif b'sync to ucs: ' in line:
                if options.verbose > 0:
                    print(line.decode('UTF-8'), end='')
                line = mm.readline()
            else:
                line = mm.readline()
