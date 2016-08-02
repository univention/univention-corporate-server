import subprocess
import fnmatch
import os
import polib
import logging


class InvalidCommandError(Exception):
	pass


def get_matching_file_paths(path, pattern):
	matched_files_paths = list()
	for dirname, dns, fnames in os.walk(path):
		for fn in fnames:
			matched_files_paths.append(os.path.join(dirname, fn))
	return fnmatch.filter(matched_files_paths, pattern)


def call(*command_parts):
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
		print('Error: Command exited unsuccessfully. Operating System error during command execution.')
		print('Error: {}'.format(exc.strerror))
		raise InvalidCommandError()


#def _entry_is_fuzzy(changed_entry, po_file_path):
#	po_file = polib.pofile(po_file_path)
#	found_change = False
#	for fuzzy in po_file.fuzzy_entries():
#		if fuzzy.occurrences == changed_entry.occurrences:
#			found_change = True
#	return found_change
#
#
#def _remove_fuzzy_flags(po_file_path):
#	po_file = polib.pofile(po_file_path)
#	for fuzzy_entry in po_file.fuzzy_entries():
#		fuzzy_entry.flags.remove('fuzzy')
#	po_file.save()
#
#
#SVN_PATH = 'SVN_REPO'
#def _change_entry_in_source_file(module_path, po_entry):
#	for source_file, line_number in po_entry.occurrences:
#		source_file = os.path.join(SVN_PATH, module_path, source_file)
#		original_source_file = '{}.orig'.format(source_file)
#		os.rename(source_file, original_source_file)
#		with open(source_file, 'w') as changed_js:
#			with open(original_source_file, 'r') as fd:
#				for i, line in enumerate(fd):
#					if i == int(line_number) - 1:
#						logging.info('Changing {} in line {}'.format(source_file, line_number))
#						line = line.replace(po_entry.msgid, 'TEST! {}'.format(po_entry.msgid))
#					changed_js.write(line)
