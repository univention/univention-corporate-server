# -*- coding: utf-8 -*-
import warnings
warnings.warn('univention_baseconfig is deprecated by univention.config_registry', PendingDeprecationWarning)
del warnings

from univention.config_registry import *
baseConfig = ConfigRegistry
