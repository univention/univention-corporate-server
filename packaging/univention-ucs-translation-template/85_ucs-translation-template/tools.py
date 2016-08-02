import subprocess
import fnmatch
import os


from pdb import set_trace as dbg

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
