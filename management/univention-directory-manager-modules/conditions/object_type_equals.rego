package guardian.conditions

import future.keywords.every
import future.keywords.if
import future.keywords.in

condition("udm:conditions:target_object_type_equals", parameters, condition_data) if {
	parameters.objectType == condition_data.target.old_target.attributes.objectType
} else = false

