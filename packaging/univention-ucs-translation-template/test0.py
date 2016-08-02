#!/usr/bin/env python
from difflib import context_diff
from distutils.file_util import copy_file
import logging
import os
import polib
import random
import shutil
import sys
import tools

from pdb import set_trace as dbg


class InvalidCommandError(Exception):
	pass


def _entry_is_fuzzy(changed_entry, po_file_path):
	po_file = polib.pofile(po_file_path)
	found_change = False
	for fuzzy in po_file.fuzzy_entries():
		if fuzzy.occurrences == changed_entry.occurrences:
			found_change = True
	return found_change


def _remove_fuzzy_flags(po_file_path):
	po_file = polib.pofile(po_file_path)
	for fuzzy_entry in po_file.fuzzy_entries():
		fuzzy_entry.flags.remove('fuzzy')
	po_file.save()


def _change_entry_in_source_file(source_pkg_path, po_entry):
	for source_file, line_number in po_entry.occurrences:
		source_file_path = os.path.join(source_pkg_path, source_file)
		original_source_file = '{}.orig'.format(source_file_path)
		os.rename(source_file_path, original_source_file)
		with open(source_file_path, 'w') as changed_source, open(original_source_file, 'r') as fd:
				for i, line in enumerate(fd):
					if i == int(line_number) - 1:
						logging.info('Changing %s in line %s', source_file, line_number)
						line = line.replace(po_entry.msgid, 'TEST! {}'.format(po_entry.msgid))
					changed_source.write(line)
		os.unlink(original_source_file)

SVN = 'SVN_TEST0'
TRANSLATION_PKG_NAME = 'univention-ucs-translation-XX'
# TODO: get latest public branch
if __name__ == '__main__':
	logging.basicConfig(level='DEBUG')
	static_seed = random.getrandbits(128)
	logging.debug('seed for this test: %s', str(static_seed))
	rand = random.Random(static_seed)
	# TODO: run whole test in tmp dir
	try:
		#shutil.rmtree(SVN)
		shutil.rmtree(TRANSLATION_PKG_NAME)
	except Exception:
		pass

	try:
		tools.call('svn', 'checkout', 'http://forge.univention.org/svn/dev/branches/ucs-4.1/ucs-4.1-1', SVN)
		tools.call('univention-ucs-translation-build-package', '--source={}'.format(SVN), '--languagecode=XX', '--locale=fr_FR.UTF-8:UTF-8', '--languagename=TEST0')
		tools.call('univention-ucs-translation-fakemessage', TRANSLATION_PKG_NAME)
	except InvalidCommandError:
		print('Error: Tried to launch invalid command. Exiting.')
		sys.exit(1)

	# Choose js files to manipulate
	changes = list()
	for file_path_pattern in ('*umc*js*.po', '*umc*python*.po'):
		po_paths = tools.get_matching_file_paths(TRANSLATION_PKG_NAME, file_path_pattern)

		i = int()
		while i < 3:
			random_po_path = rand.choice(po_paths)
			po_paths.remove(random_po_path)
			copy_file(random_po_path, '{}.pre_change'.format(random_po_path))
			random_po = polib.pofile(random_po_path)
			if not random_po:
				logging.debug('Choose empty PO file: %s', random_po_path)
				continue
			i += 1
			random_entry = rand.choice(random_po)
			source_pkg_path = os.path.join(SVN, '/'.join(random_po_path.split('/')[2:4]))
			_change_entry_in_source_file(source_pkg_path, random_entry)
			changes.append((random_po_path, random_entry))

	tools.call('univention-ucs-translation-merge', 'XX', SVN, TRANSLATION_PKG_NAME)

	for po_path, changed_entry in changes:
		if _entry_is_fuzzy(changed_entry, po_path):
			logging.info('Fuzzy entries correctly flagged after first merge.')
		else:
			logging.info('Test failure: There should be fuzzy entries for this change.')
			logging.info('PO file: %s', po_path)
			sys.exit(1)
		_remove_fuzzy_flags(po_path)

	tools.call('svn', 'revert', '--recursive', SVN)
	tools.call('univention-ucs-translation-merge', 'XX', SVN, TRANSLATION_PKG_NAME)

	for po_path, changed_entry in changes:
		if not _entry_is_fuzzy(changed_entry, po_path):
			print('Test: Failed! No fuzzy entries on second merge.')
			sys.exit(1)
		logging.info('Fuzzy entires correctly flagged after second merge.')
		_remove_fuzzy_flags(po_path)

	for po_path, _ in changes:
		failures = False
		with open(po_path, 'rb') as fd, open('{}.pre_change'.format(po_path), 'rb') as fd_pre:
			def _ignore_date(line):
				return not line.startswith('"POT-Creation-Date')
			original = filter(_ignore_date, fd_pre.readlines())
			result = filter(_ignore_date, fd.readlines())
			if original != result:
				failures = True
				logging.info('Test: PO files not identical after last merge: %s', po_path)
	if failures:
		logging.info('Test failed.')
		sys.exit(1)
