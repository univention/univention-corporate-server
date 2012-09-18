# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 et :
"""Public interface for test resultes."""
__all__ = ['TestCodes']


class TestCodes(object):
	"""Public interface for test resultes."""
	RESULT_OKAY = 0
	RESULT_FAIL = 1
	RESULT_SKIP = 77

	__REASONS = {  # EOFS name code message color
			None: ('E', 'REASON_UNKNOWN', 'Unknown', 'MAGENTA'),
			77: ('S', 'REASON_SKIP', 'Skipped', 'BLUE'),
			100: ('O', 'REASON_OKAY', 'Test passed', 'GREEN'),
			101: ('O', 'REASON_FIXED_EXPECTED', 'Fixed expected', 'GREEN'),
			102: ('O', 'REASON_FIXED_UNEXPECTED', 'Fixed unexpected', 'GREEN'),
			110: ('F', 'REASON_FAIL', 'Test failed', 'RED'),
			111: ('F', 'REASON_FAIL_UNEXPECTED', 'Unfixed', 'RED'),
			120: ('F', 'REASON_FAIL_TRANSIENT', 'Transient error', 'YELLOW'),
			121: ('F', 'REASON_FAIL_EXPECTED', 'Unfixed expected', 'YELLOW'),
			122: ('E', 'REASON_UNAVAILABLE', 'Unavailable', 'YELLOW'),
			130: ('S', 'REASON_IMMATURE', 'Immature', 'WHITE'),
			131: ('S', 'REASON_VERSION_MISMATCH', 'Wrong version', 'BLUE'),
			132: ('S', 'REASON_VERSION_TOO_OLD', 'Version too old', 'BLUE'),
			133: ('S', 'REASON_VERSION_TOO_NEW', 'Version too new', 'BLUE'),
			134: ('S', 'REASON_ROLE_MISMATCH', 'Role mismatch', 'BLUE'),
			135: ('S', 'REASON_JOIN', 'System not joined', 'BLUE'),
			136: ('S', 'REASON_JOINED', 'System is joined', 'BLUE'),
			137: ('S', 'REASON_INSTALL', 'Missing software', 'BLUE'),
			138: ('S', 'REASON_INSTALLED', 'Conflicting software', 'BLUE'),
			139: ('S', 'REASON_DANGER', 'Too dangerous', 'BLUE'),
			140: ('E', 'REASON_INTERNAL', 'Internal error', 'MAGENTA'),
			141: ('S', 'REASON_ABORT', 'Aborted', 'MAGENTA'),
			}
	MESSAGE = {}
	MAX_MESSAGE_LEN = 0
	COLOR = {}
	EOFS = {  # Error Okay Failure Skip
			RESULT_OKAY: 'O',
			RESULT_FAIL: 'F',
			RESULT_SKIP: 'S',
			}
	for (code, (eofs, name, msg, color)) in __REASONS.items():
		locals()[name] = code
		MESSAGE[code] = msg
		if len(msg) > MAX_MESSAGE_LEN:
			MAX_MESSAGE_LEN = len(msg)
		COLOR[code] = color
		EOFS[code] = eofs
	del __REASONS
	del code, eofs, name, msg, color
