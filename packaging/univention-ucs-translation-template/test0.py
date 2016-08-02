#!/usr/bin/env python
from hashlib import md5
import logging
import os
import polib
import random
import shutil
import sys
import tools

# DBG:
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
# TODO: get latest public branch
if __name__ == '__main__':
	# TODO: run whole test in tmp dir
	try:
		shutil.rmtree('svn_repo')
		shutil.rmtree(TRANSLATION_PKG_NAME)
	except Exception:
		pass

	try:
		tools.call('svn', 'checkout', 'http://forge.univention.org/svn/dev/branches/ucs-4.1/ucs-4.1-1/management/univention-management-console-module-passwordchange/', 'svn_repo/management/univention-management-console-module-passwordchange')
		tools.call('univention-ucs-translation-build-package', '--source=svn_repo', '--languagecode=XX', '--locale=fr_FR.UTF-8:UTF-8', '--languagename=TEST0')
		tools.call('univention-ucs-translation-fakemessage', TRANSLATION_PKG_NAME)
	except InvalidCommandError:
		print('Error: Tried to launch invalid command. Exiting.')
		sys.exit(1)

	# Choose js files to manipulate
	js_po_files = tools.get_matching_file_paths(TRANSLATION_PKG_NAME, '*umc*js*.po')
	choosen_po_path = random.choice(js_po_files)
	choosen_po_pre_changes_path = '{}.pre-change'.format(choosen_po_path)
	shutil.copy(choosen_po_path, choosen_po_pre_changes_path)
	module_path = '/'.join(choosen_po_path.split('/')[2:4])
	choosen_po = polib.pofile(choosen_po_path)
	random_entry = random.choice(choosen_po)

	_change_entry_in_source_file(module_path, random_entry)
	tools.call('univention-ucs-translation-merge', 'XX', 'svn_repo', TRANSLATION_PKG_NAME)

	if not _entry_is_fuzzy(random_entry, choosen_po_path):
		print('FAILED: There should be fuzzy entries for this change.')
		sys.exit(1)
	logging.info('Fuzzy entries correctly flagged after first merge.')

	_remove_fuzzy_flags(choosen_po_path)
	tools.call('svn', 'revert', '--recursive', 'svn_repo/management/univention-management-console-module-passwordchange')
	tools.call('univention-ucs-translation-merge', 'XX', 'svn_repo', TRANSLATION_PKG_NAME)
	if not _entry_is_fuzzy(random_entry, choosen_po_path):
		print('Test: Failed! No fuzzy entries on second merge.')
		sys.exit(1)
	logging.info('Fuzzy entires correctly flagged after second merge.')

	_remove_fuzzy_flags(choosen_po_path)
	with open(choosen_po_pre_changes_path, 'rb') as pre_change, open(choosen_po_path, 'rb') as after:
		if md5(pre_change.read()).hexdigest() != md5(after.read()).hexdigest():
			print('TEST: FAILED!')
			sys.exit(1)
