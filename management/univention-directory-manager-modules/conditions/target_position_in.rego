package guardian.conditions

import future.keywords.if

target_position_in_check_dn_position(dn, position, scope) if {
    scope == "base"
    regex.match(concat("", [`(?i)^[a-z]+=[^,]+,`, position, `$`]), dn)
}

target_position_in_check_dn_position(dn, position, scope) if {
    scope == "subtree"
    endswith(lower(dn), lower(position))
}

condition("udm:conditions:target_position_in", parameters, condition_data) if {
    target_position_in_check_dn_position(condition_data.target.old.attributes.dn, parameters.position, parameters.scope)
} else = false

# For Rego Playground (https://play.openpolicyagent.org):
#
# result := condition(
#             "udm:conditions:target_position_in",
#             {
#                 "position": "cn=users,dc=ucs,dc=test",
#                 "scope": "subtree",
#             },
#             {
#                 "target": {
#                     "old": {
#                         "attributes": {
#                             "dn": "uid=testuser,cn=ou,cn=users,dc=ucs,dc=test"
#                         }
#                     }
#                 }
#             }
# )