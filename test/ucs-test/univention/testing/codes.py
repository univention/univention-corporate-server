# vim: set fileencoding=utf-8 ft=python sw=4 ts=4 :
"""Public interface for test resultes."""
__all__ = ['TestCodes']


class TestCodes(object):

	"""Public interface for test resultes."""
	RESULT_OKAY = 0
	RESULT_FAIL = 1
	RESULT_SKIP = 77

	__REASONS = {  # EOFS name code message color
		None: ('E', 'REASON_UNKNOWN', 'Test failed', 'RED'),
		77: ('S', 'REASON_SKIP', 'Test skipped', 'BLUE'),
		100: ('O', 'REASON_OKAY', 'Test passed', 'GREEN'),
		101: ('O', 'REASON_FIXED_EXPECTED', 'Test passed', 'GREEN'),
		102: ('O', 'REASON_FIXED_UNEXPECTED', 'Test passed', 'GREEN'),
		110: ('F', 'REASON_FAIL', 'Test failed', 'RED'),
		111: ('F', 'REASON_FAIL_UNEXPECTED', 'Test failed', 'RED'),
		120: ('F', 'REASON_FAIL_TRANSIENT', 'Test failed', 'RED'),
		121: ('F', 'REASON_FAIL_EXPECTED', 'Test failed', 'RED'),
		122: ('E', 'REASON_UNAVAILABLE', 'Test failed', 'RED'),
		130: ('S', 'REASON_IMMATURE', 'Test failed', 'RED'),
		131: ('S', 'REASON_VERSION_MISMATCH', 'Test skipped (wrong version)', 'BLUE'),
		132: ('S', 'REASON_VERSION_TOO_OLD', 'Test skipped (version too old)', 'BLUE'),
		133: ('S', 'REASON_VERSION_TOO_NEW', 'Test skipped (version too new)', 'BLUE'),
		134: ('S', 'REASON_ROLE_MISMATCH', 'Test skipped (role mismatch)', 'BLUE'),
		135: ('S', 'REASON_JOIN', 'Test skipped (system not joined)', 'BLUE'),
		136: ('S', 'REASON_JOINED', 'Test skipped (system is joined)', 'BLUE'),
		137: ('S', 'REASON_INSTALL', 'Test skipped (missing software)', 'BLUE'),
		138: ('S', 'REASON_INSTALLED', 'Test skipped (conflicting software)', 'BLUE'),
		139: ('S', 'REASON_DANGER', 'Test skipped (too dangerous)', 'BLUE'),
		140: ('E', 'REASON_INTERNAL', 'Test failed', 'RED'),
		141: ('S', 'REASON_ABORT', 'Test failed', 'RED'),
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
