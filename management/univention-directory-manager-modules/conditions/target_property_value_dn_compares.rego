package guardian.conditions

import future.keywords.if

condition("udm:conditions:target_property_value_dn_compares", parameters, condition_data) if {
    # parameters.operator = "==" {
    #     parameters.dn == condition_data.target.properties[parameters.property]
    # }
    # parameters.operator = "!=" {
    #     parameters.dn != condition_data.target.properties[parameters.property]
    # }
    # parameters.operator = "subtree" {
    #     false
    # }
    # parameters.operator = "onelevel" {
    #     false
    # }
    # parameters.operator = "==-i" {
    #     lower(parameters.dn) == lower(condition_data.target.properties[parameters.property])
    # }
    # parameters.operator = "!=-i" {
    #     lower(parameters.dn) != lower(condition_data.target.properties[parameters.property])
    # }
    # parameters.operator = "subtree-i" {
    #     false
    # }
    # parameters.operator = "onelevel-i" {
    #     false
    # }
    "a" == "a"
} else = false
