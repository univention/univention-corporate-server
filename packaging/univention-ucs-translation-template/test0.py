#!/usr/bin/env python
import os
import fnmatch
import random
import subprocess
import sys
import shutil
import polib
import logging
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


def _change_generated_fuzzy_entries(changed_entry, po_file_path):
	po_file = polib.pofile(po_file_path)
	found_change = False
	for fuzzy in po_file.fuzzy_entries():
		if fuzzy.occurrences == changed_entry.occurrences:
			found_change = True
		else:
			print('DBG: fuzzy entry not produced by test.')
			sys.exit(1)
	return found_change


def _remove_fuzzy_flags(po_file_path):
	po_file = polib.pofile(po_file_path)
	for fuzzy_entry in po_file.fuzzy_entries():
		fuzzy_entry.flags.remove('fuzzy')
	po_file.save()


def _change_entry_in_source_file(module_path, po_entry):
	for source_file, line_number in po_entry.occurrences:
		source_file = os.path.join('svn_repo', module_path, source_file)
		original_source_file = '{}.orig'.format(source_file)
		os.rename(source_file, original_source_file)
		with open(source_file, 'w') as changed_js:
			with open(original_source_file, 'r') as fd:
				for i, line in enumerate(fd):
					if i == int(line_number) - 1:
						logging.info('Changing {} in line {}'.format(source_file, line_number))
						line = line.replace(po_entry.msgid, 'TEST! {}'.format(po_entry.msgid))
					changed_js.write(line)


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
	module_path = '/'.join(choosen_po_path.split('/')[2:4])
	choosen_po = polib.pofile(choosen_po_path)
	random_entry = random.choice(choosen_po)

	_change_entry_in_source_file(module_path, random_entry)
	_call('univention-ucs-translation-merge', 'XX', 'svn_repo', TRANSLATION_PKG_NAME)

	if _change_generated_fuzzy_entries(random_entry, choosen_po_path):
		print('Test: Success: fuzzy entries found!')
	else:
		print('FAILED: There should be fuzzy entries for this change.')

	_remove_fuzzy_flags(choosen_po_path)
	_call('svn', 'revert', '--recursive', 'svn_repo/management/univention-management-console-module-passwordchange')
	_call('univention-ucs-translation-merge', 'XX', 'svn_repo', TRANSLATION_PKG_NAME)

	_remove_fuzzy_flags(choosen_po_path)
	# Should be same as build + fakemassage
	# TODO: Test for this..
