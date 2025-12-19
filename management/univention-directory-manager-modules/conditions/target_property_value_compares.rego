package guardian.conditions

import future.keywords.if

target_property_value_compares_param_check(parameters, condition_data) if {
    parameters.operator == "=="
   	parameters.value == condition_data.target.old.attributes.properties[parameters.property]
}

target_property_value_compares_param_check(parameters, condition_data) if {
    parameters.operator == "!="
   	parameters.value != condition_data.target.old.attributes.properties[parameters.property]
}

target_property_value_compares_param_check(parameters, condition_data) if {
    parameters.operator == "==-i"
   	lower(parameters.value) == lower(condition_data.target.old.attributes.properties[parameters.property])
}

target_property_value_compares_param_check(parameters, condition_data) if {
    parameters.operator == "!=-i"
   	lower(parameters.value) != lower(condition_data.target.old.attributes.properties[parameters.property])
}

target_property_value_compares_param_check(parameters, condition_data) if {
    parameters.operator == "regex-match"
   	regex.match(parameters.value ,condition_data.target.old.attributes.properties[parameters.property])
}

target_property_value_compares_param_check(parameters, condition_data) if {
    parameters.operator == "regex-nomatch"
   	not regex.match(parameters.value ,condition_data.target.old.attributes.properties[parameters.property])
}

target_property_value_compares_param_check(parameters, condition_data) if {
    parameters.operator == "regex-match-i"
   	regex.match(concat("", ["(?i)", parameters.value]) ,condition_data.target.old.attributes.properties[parameters.property])
}

target_property_value_compares_param_check(parameters, condition_data) if {
    parameters.operator == "regex-nomatch-i"
   	not regex.match(concat("", ["(?i)", parameters.value]) ,condition_data.target.old.attributes.properties[parameters.property])
}

condition("udm:conditions:target_property_value_compares", parameters, condition_data) if {
    target_property_value_compares_param_check(parameters, condition_data)
} else = false

# For Rego Playground (https://play.openpolicyagent.org):
#
# result := condition(
#             "udm:conditions:target_property_value_compares",
#             {
#                 "operator": "regex-match",
#                 "property": "testproperty",
#                 "value": `^[^@]+@[^@]+\.[^@]+$`
#             },
#             {
#                 "target": {
#                     "old": {
#                         "attributes": {
#                             "testproperty": "foo@example.com"
#                         }
#                     }
#                 }
#             }
# )
