__all__ = ['TestCodes']

class TestCodes(object):
	RESULT_OKAY = 0
	RESULT_FAIL = 1
	RESULT_SKIP = 77

	__REASONS = { # name code message color
			None: ('REASON_UNKNOWN', 'Unknown', 'MAGENTA'),
			100: ('REASON_OKAY', 'Test passed', 'GREEN'),
			101: ('REASON_FIXED_EXPECTED', 'Fixed expected', 'GREEN'),
			102: ('REASON_FIXED_UNEXPECTED', 'Fixed unexpected', 'GREEN'),
			110: ('REASON_FAIL', 'Test failed', 'RED'),
			111: ('REASON_FAIL_UNEXPECTED', 'Unfixed', 'RED'),
			120: ('REASON_FAIL_TRANSIENT', 'Transient error', 'YELLOW'),
			121: ('REASON_FAIL_EXPECTED', 'Unfixed expected', 'YELLOW'),
			122: ('REASON_UNAVAILABLE', 'Unavailable', 'YELLOW'),
			130: ('REASON_IMMATURE', 'Immature', 'WHITE'),
			131: ('REASON_VERSION_MISMATCH', 'Wrong version', 'BLUE'),
			132: ('REASON_VERSION_TOO_OLD', 'Version too old', 'BLUE'),
			133: ('REASON_VERSION_TOO_NEW', 'Version too new', 'BLUE'),
			134: ('REASON_ROLE_MISMATCH', 'Role mismatch', 'BLUE'),
			135: ('REASON_JOIN', 'System not joined', 'BLUE'),
			136: ('REASON_JOINED', 'System is joined', 'BLUE'),
			137: ('REASON_INSTALL', 'Missing software', 'BLUE'),
			138: ('REASON_INSTALLED', 'Conflicting software', 'BLUE'),
			139: ('REASON_DANGER', 'Too dangerous', 'BLUE'),
			140: ('REASON_INTERNAL', 'Internal error', 'MAGENTA'),
			}
	MESSAGE = {}
	MAX_MESSAGE_LEN = 0
	COLOR = {}
	for (code, (name, msg, color)) in __REASONS.items():
		locals()[name] = code
		MESSAGE[code] = msg
		if len(msg) > MAX_MESSAGE_LEN:
			MAX_MESSAGE_LEN = len(msg)
		COLOR[code] = color
	del __REASONS
	del code, name, msg, color
