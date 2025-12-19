package guardian.conditions

import future.keywords.if

condition("udm:conditions:target_object_type_equals", parameters, condition_data) if {
	parameters.objecttype == condition_data.target.old.attributes.objecttype
} else = false
