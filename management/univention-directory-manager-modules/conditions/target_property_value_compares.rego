package guardian.conditions

import future.keywords.if

condition("udm:conditions:target_property_value_compares", parameters, condition_data) if {
    parameters.operator = "==" {
        parameters.value == condition_data.target.properties[parameters.property]
    }
    parameters.operator = "!=" {
        parameters.value != condition_data.target.properties[parameters.property]
    }
    parameters.operator = "regex-match" {
        re_match(parameters.value, condition_data.target.properties[parameters.property])
    }
    parameters.operator = "regex-nomatch" {
        not re_match(parameters.value, condition_data.target.properties[parameters.property])
    }
    parameters.operator = "==-i" {
        lower(parameters.value) == lower(condition_data.target.properties[parameters.property])
    }
    parameters.operator = "!=-i" {
        lower(parameters.value) != lower(condition_data.target.properties[parameters.property])
    }
    parameters.operator = "regex-match-i" {
        re_match(lower(parameters.value), lower(condition_data.target.properties[parameters.property]))
    }
    parameters.operator = "regex-nomatch-i" {
        not lower(re_match(parameters.value), lower(condition_data.target.properties[parameters.property]))
    }
} else = false
