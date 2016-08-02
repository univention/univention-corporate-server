import helper
import os
import sys
import shutil
from hashlib import md5
from difflib import context_diff
from distutils.dir_util import copy_tree
from distutils.file_util import copy_file

from pdb import set_trace as dbg

SVN_PATH = 'SVN_REPO'
DUMMY_MOD_DIR = 'management/univention-management-console-module-dummy'
DUMMY_MOD_EXPECTED_PO_PATHS = [
	'univention-ucs-translation-XX/XX/management/univention-management-console-module-dummy/umc/python/dummy/XX.po',
	'univention-ucs-translation-XX/XX/management/univention-management-console-module-dummy/umc/XX.po',
	'univention-ucs-translation-XX/XX/management/univention-management-console-module-dummy/umc/js/XX.po'
]

MAKEFILE_EXPECTED_DIFF = [
	'+ \t$(DESTDIR)/usr/share/locale/XX/LC_MESSAGES/univention-management-console-module-dummy.mo \\\n',
	'+ \t$(DESTDIR)/usr/share/univention-management-console-frontend/js/umc/modules/i18n/XX/dummy.json \\\n',
	'+ \t$(DESTDIR)/usr/share/univention-management-console/i18n/XX/dummy.mo \\\n',
	'+ $(DESTDIR)/usr/share/locale/XX/LC_MESSAGES/univention-management-console-module-dummy.mo: XX/management/univention-management-console-module-dummy/umc/python/dummy/XX.po\n',
	'+ $(DESTDIR)/usr/share/univention-management-console-frontend/js/umc/modules/i18n/XX/dummy.json: XX/management/univention-management-console-module-dummy/umc/js/XX.po\n',
	'+ $(DESTDIR)/usr/share/univention-management-console/i18n/XX/dummy.mo: XX/management/univention-management-console-module-dummy/umc/XX.po\n'
]

TRANSLATION_PKG_NAME = 'univention-ucs-translation-XX'
if __name__ == '__main__':
	# TODO: run whole test in tmp dir
	try:
		shutil.rmtree(SVN_PATH+'/management/univention-management-console-module-dummy')
		shutil.rmtree(TRANSLATION_PKG_NAME)
	except Exception:
		pass

	try:
		helper.call('svn', 'checkout', 'http://forge.univention.org/svn/dev/branches/ucs-4.1/ucs-4.1-1', SVN_PATH)
		helper.call('univention-ucs-translation-build-package', '--source=' + SVN_PATH, '--languagecode=XX', '--locale=fr_FR.UTF-8:UTF-8', '--languagename=TEST0')
		helper.call('univention-ucs-translation-fakemessage', TRANSLATION_PKG_NAME)
	except helper.InvalidCommandError:
		print('Error: Tried to launch invalid command. Exiting.')
		sys.exit(1)
	copy_file(os.path.join(TRANSLATION_PKG_NAME, 'all_targets.mk'), 'all_targets.mk.pre_merge')

	# Add dummy module with new translations
	copy_tree('./dummy_module', SVN_PATH)
	helper.call('univention-ucs-translation-merge', 'XX', SVN_PATH, TRANSLATION_PKG_NAME)
	helper.call('univention-ucs-translation-fakemessage', TRANSLATION_PKG_NAME)

	translation_tree_path = os.path.join(TRANSLATION_PKG_NAME, 'XX', DUMMY_MOD_DIR)
	new_po_paths = helper.get_matching_file_paths(translation_tree_path, '*.po')
	if not set(new_po_paths) == set(DUMMY_MOD_EXPECTED_PO_PATHS):
		print('Test: Failed')
		sys.exit(1)
	with open('all_targets.mk.pre_merge', 'r') as pre, open(os.path.join(TRANSLATION_PKG_NAME, 'all_targets.mk')) as after:
		diff = [line for line in context_diff(pre.readlines(), after.readlines()) if line.startswith('+ ')]

	if set(diff) != set(MAKEFILE_EXPECTED_DIFF):
		dbg()
		print('Test: Failed. Diff didn\'t yield expected result.')
		print(diff)
		sys.exit(1)

	shutil.rmtree(SVN_PATH+'/management/univention-management-console-module-dummy')
	helper.call('univention-ucs-translation-merge', 'XX', SVN_PATH, TRANSLATION_PKG_NAME)

	# Files obsoleted upstream detected?
	new_po_paths = helper.get_matching_file_paths(translation_tree_path, '*.obsolete')
	expected_obsoleted_po_paths = ['{}.obsolete'.format(path) for path in DUMMY_MOD_EXPECTED_PO_PATHS]
	if set(new_po_paths) != set(expected_obsoleted_po_paths):
		print('Test: Failed. Merge didn\'t detect obsoleted po files.')
		#sys.exit(1)

	# Makefile should ne the same as before adding the dummy module
	with open('all_targets.mk.pre_merge', 'rb') as pre_change, open(os.path.join(TRANSLATION_PKG_NAME, 'all_targets.mk'), 'rb') as after:
		if md5(pre_change.read()).hexdigest() != md5(after.read()).hexdigest():
			dbg()
			print('Test: Failed! Makefile was changed.')
			sys.exit(1)
