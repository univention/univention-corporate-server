#!/usr/bin/env python
import os
import fnmatch
import random
import subprocess
import sys
import shutil
import polib
from pdb import set_trace as dbg


class InvalidCommandError(Exception):
	pass


def _get_matching_file_paths(path, pattern):
	"""Recursively walk through path and match file paths with pattern,
	return matches"""
	matched_files_paths = list()
	for dirname, dns, fnames in os.walk(path):
		for fn in fnames:
			matched_files_paths.append(os.path.join(dirname, fn))
	return fnmatch.filter(matched_files_paths, pattern)


def _call(*command_parts):
	if not command_parts:
		raise InvalidCommandError()
	try:
		subprocess.check_call([part for part in command_parts])
	except subprocess.CalledProcessError as exc:
		print('Error: Subprocess exited unsuccessfully. Attempted command:')
		print(' '.join(exc.cmd))
		raise InvalidCommandError()
	except AttributeError as exc:
		print('Command must be a string like object.')
		raise InvalidCommandError()
	except OSError as exc:
		print('Error: {}'.format(exc.strerror))
		print('Error: failed to start subprocess.')
		raise InvalidCommandError()


def _change_msgid_in_source_file(source_file, line_number, msgid):
	new_source_file = '{}.changed'.format(source_file)
	with open(new_source_file, 'w') as changed_js:
		with open(source_file, 'r') as fd:
			for i, line in enumerate(fd):
				if i == int(line_number) - 1:
					line = line.replace(msgid, 'TEST! {}'.format(msgid))
				changed_js.write(line)
	os.rename(new_source_file, source_file)


TRANSLATION_PKG_NAME = 'univention-ucs-translation-XX'
if __name__ == '__main__':
	# _call('svn', 'checkout', 'http://forge.univention.org/svn/dev/branches/ucs-4.1/ucs-4.1-1/management/univention-management-console-module-passwordchange/', 'svn_repo')
	try:
		shutil.rmtree('svn_repo')
		shutil.rmtree(TRANSLATION_PKG_NAME)
	except Exception:
		pass

	try:
		_call('svn', 'checkout', 'http://forge.univention.org/svn/dev/branches/ucs-4.1/ucs-4.1-1/management/univention-management-console-module-passwordchange/', 'svn_repo/management/univention-management-console-module-passwordchange')
		_call('univention-ucs-translation-build-package', '--source=svn_repo', '--languagecode=XX', '--locale=fr_FR.UTF-8:UTF-8', '--languagename=TEST0')
		_call('univention-ucs-translation-fakemessage', TRANSLATION_PKG_NAME)
	except InvalidCommandError:
		print('Error: Tried to launch invalid command. Exiting.')
		sys.exit(1)

	# Choose js files to manipulate
	js_po_files = _get_matching_file_paths(TRANSLATION_PKG_NAME, '*umc*js*.po')
	choosen_po_path = random.choice(js_po_files)
	choosen_po_module_path = '/'.join(choosen_po_path.split('/')[2:4])
	choosen_po = polib.pofile(choosen_po_path)
	random_entry = random.choice(choosen_po)

	for source_file, line_number in random_entry.occurrences:
		source_file = os.path.join('svn_repo', choosen_po_module_path, source_file)
		_change_msgid_in_source_file(source_file, line_number, random_entry.msgid)
	_call('univention-ucs-translation-merge', 'XX', 'svn_repo', TRANSLATION_PKG_NAME)

	# fuzzy?
	choosen_po = polib.pofile(choosen_po_path)
	found_change = False
	for fuzzy_entry in choosen_po.fuzzy_entries():
		if list(*fuzzy_entry.occurrences) == list(*random_entry.occurrences):
			found_change = True
		else:
			print('DBG: fuzzy entry not produced by test.')
			sys.exit(1)
		fuzzy_entry.flags.remove('fuzzy')
	choosen_po.save()

	if found_change:
		print('Test: Success: fuzzy entries found!')

	_call('svn', 'revert', '--recursive', 'svn_repo/management/univention-management-console-module-passwordchange')
	_call('univention-ucs-translation-merge', 'XX', 'svn_repo', TRANSLATION_PKG_NAME)

	choosen_po = polib.pofile(choosen_po_path)
	for fuzzy_entry in choosen_po.fuzzy_entries():
		fuzzy_entry.flags.remove('fuzzy')
	choosen_po.save()
