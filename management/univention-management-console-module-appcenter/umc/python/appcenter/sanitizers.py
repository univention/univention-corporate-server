from univention.management.console.modules.sanitizers import Sanitizer, PatternSanitizer, MappingSanitizer, StringSanitizer, DictSanitizer, BooleanSanitizer
import univention.config_registry
import univention.management.console as umc


_ = umc.Translation('univention-management-console-module-appcenter').translate


class AnySanitizer(Sanitizer):
	def _sanitize(self, value, name, further_args):
		any_given = any([value] + further_args.values())
		if not any_given:
			self.raise_formatted_validation_error(_('Any of %r must be given') % ([name] + further_args.keys()), name, value)
		return any_given

class NoDoubleNameSanitizer(StringSanitizer):
	def _sanitize(self, value, name, further_arguments):
		from constants import COMPONENT_BASE
		ucr = univention.config_registry.ConfigRegistry()
		ucr.load()
		if '%s/%s' % (COMPONENT_BASE, value) in ucr:
			self.raise_validation_error(_("There already is a component with this name"))
		return value

basic_components_sanitizer = DictSanitizer({
		'server' : StringSanitizer(required=True, minimum=1),
		'prefix' : StringSanitizer(required=True),
		'maintained' : AnySanitizer(required=True, may_change_value=False, further_arguments=['unmaintained']),
		'unmaintained' : BooleanSanitizer(required=True),
	},
	allow_other_keys=False,
)

advanced_components_sanitizer = DictSanitizer({
		'server' : StringSanitizer(),
		'prefix' : StringSanitizer(),
		'maintained' : BooleanSanitizer(),
		'unmaintained' : BooleanSanitizer(),
		'enabled' : BooleanSanitizer(required=True),
		'name' : StringSanitizer(required=True, regex_pattern='^[A-Za-z0-9\-\_\.]+$'),
		'description' : StringSanitizer(),
		'username' : StringSanitizer(),
		'password' : StringSanitizer(),
		'version' : StringSanitizer(regex_pattern='^((([0-9]+\\.[0-9]+|current),)*([0-9]+\\.[0-9]+|current))?$')
	}
)

add_components_sanitizer = advanced_components_sanitizer + DictSanitizer({
		'name' : NoDoubleNameSanitizer(required=True, regex_pattern='^[A-Za-z0-9\-\_\.]+$'),
	}
)

