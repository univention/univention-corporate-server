package guardian.conditions

import future.keywords.if

target_position_from_context_check_dn_position(dn, positions, scope) if {
	scope == "base"
	some i
	regex.match(concat("", [`(?i)^[a-z]+=[^,]+,`, positions[i], `$`]), dn)
}

target_position_from_context_check_dn_position(dn, positions, scope) if {
	scope == "subtree"
	some i
	endswith(lower(dn), lower(positions[i]))
}

condition("udm:conditions:target_position_from_context", parameters, condition_data) if {
	positions := [
    	position | concat(
        	":",
            [
            	condition_data.extra_args.actor_roles[i].context.app_name,
                condition_data.extra_args.actor_roles[i].context.namespace_name,
                condition_data.extra_args.actor_roles[i].context.name
            ]
        ) == parameters.position;
        position := condition_data.extra_args.actor_roles[i].context.value
    ]
	# print(positions)
	target_position_from_context_check_dn_position(condition_data.target.old.attributes.dn, positions, parameters.scope)
} else := false

# For Rego Playground (https://play.openpolicyagent.org):
#
# result := condition(
# 	"udm:conditions:target_position_from_context",
# 	{
# 		"position": "udm:contexts:position",
# 		"scope": "subtree",
# 	},
# 	{
# 		"actor": {"roles": [
# 			{
# 				"app_name": "udm",
# 				"namespace_name": "default-roles",
# 				"name": "udm:default-roles:organizational-unit-admin",
#                 "context": {
#                 	"app_name": "udm",
#                     "namespace_name": "default-roles",
#                     "name": "udm:contexts:position",
#                 }
# 			},
# 		]},
# 		"target": {"old": {"attributes": {"dn": "uid=testuser,ou=bremen,cn=users,dc=ucs,dc=test"}}},
#         "extra_args": {"actor_roles": [
#         	{
#             	"app_name": "udm",
# 				"namespace_name": "default-roles",
# 				"name": "udm:default-roles:organizational-unit-admin",
#                 "context": {
#                 	"app_name": "udm",
#                     "namespace_name": "contexts",
#                     "name": "position",
#                     "value": "ou=bremen,cn=users,dc=ucs,dc=test"
#                 }
#             }
#         ]}
# 	},
# )
