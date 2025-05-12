package guardian.conditions

import future.keywords.if

condition("udm:conditions:target_position_in", parameters, condition_data) if {
    # TODO: evaluate "*"
    # TODO: evaluate "$CONTEXT"?
    parameters.scope = "base" {
        parameters.position + condition_data.target.ldap_base == condition_data.target.position
    }
    parameters.scope = "subtree" {
        endswith(condition_data.target.position, parameters.position + condition_data.target.ldap_base)
    }
} else = false
