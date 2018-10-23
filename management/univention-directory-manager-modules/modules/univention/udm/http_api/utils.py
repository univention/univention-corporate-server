from __future__ import absolute_import, unicode_literals
import logging
from univention.config_registry import ConfigRegistry

try:
	from typing import Any, Dict, List, Optional, Text, Tuple
	import flask.app.Flask
except ImportError:
	pass


LOG_MESSAGE_FORMAT ='%(asctime)s %(levelname)-7s %(module)s.%(funcName)s:%(lineno)d  %(message)s'
LOG_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'

ucr = ConfigRegistry()
ucr.load()
_logger = None


def get_logger(app):  # type: (flask.app.Flask) -> logging.Logger
	global _logger
	if not _logger:
		flask_rp_logger = logging.getLogger('flask_restplus')
		gunicorn_logger = logging.getLogger('gunicorn')
		udm_logger = logging.getLogger('univention')
		for handler in app.logger.handlers:
			handler.setLevel(logging.DEBUG)
			handler.setFormatter(logging.Formatter(LOG_MESSAGE_FORMAT, LOG_DATETIME_FORMAT))
			flask_rp_logger.addHandler(handler)
			gunicorn_logger.addHandler(handler)
			udm_logger.addHandler(handler)
		app.logger.setLevel(logging.DEBUG)
		flask_rp_logger.setLevel(logging.DEBUG)
		gunicorn_logger.setLevel(logging.DEBUG)
		udm_logger.setLevel(logging.DEBUG)
		_logger = app.logger
	return _logger
