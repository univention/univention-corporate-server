[TOC]

# UDM Authorization using Cerbos

## Cerbos policies

Cerbos provides different kinds of policies: resource policies, derived roles, role policies, and principal policies.

The challenge is, to find the one, which fits best for our use case.

Cerbos makes the resource the primary owner of permissions, whereas Guardian makes the role the primary owner.

The role concept in Cerbos is a static one: All roles and resources are described.
Guardian had a dynamic one, where roles were defined arbitrarily and contexts added dynamically.

Guardian was RBAC with ABAC extension.
Cerbos allows to implement various policy design patterns (action-led, role-led, attribute-led/ABAC, IdP-role-centric/RBAC) - none of them are the exact OOTB thing we need.

### Mapping Guardian → Cerbos Terminology

| Guardian                | Cerbos                      |
| ----------------------- | --------------------------- |
| Role                    | IdP role / static role      |
| Actor                   | Principal                   |
| Target                  | Resource                    |
| Permission              | Action                      |
| Capability              | Resource Rule               |
| Context                 | principal.attr.contextRoles |
| Condition               | CEL                         |
| Capability Registration | not applicable              |
| Management API          | not applicable              |

Cerbos uses the term `role` for two things:
1. `static` or `Identity Provider role`
which is the role name given by e.g. UDM (attribute `guardianRole`) the IdP - these names are invented by us/customers.

These are the static roles for the outside.

2. derived Roles
which is a internal concept, for naming conditions attached to roles - usable by resource policies.
Not usable from the outside.

### Resource policies

The root of all policies is the resource policy (we must define them):

* resource policies answer the question: "Who may(potentially) perform which actions on this type of resource?"
* resource policies can grant actions based on wildcards
* resource policies can add scopes and scope-permissions (see later)
* resource policies must import known derived roles, they want to use/extend. → **that makes it harder/nearly impossible for our customers to write them**
* a resource policy containing rules to `DENY` access to an action is **final**. One cannot add a role policy which afterwards allows these actions again.
* **there can only be exactly 1 resource policy for each resource kind**
* this one resource policy must contain all the rules (or outsource them into derived roles) in one defintion (file)!
* it must define which roles or derived roles are candidates for the resource
→ **that means, if a customers creates a new role, we must extend our resource definition!** (if no role policies are used, see later why not)

**Consequences for UDM**:

* We either have to generate resource policies from all the information we know about the rules - that is more complicated - or define the resource policy for each UDM module with a global `rules: *; effect_ ALLOW` and further restrict it via role policies (or derived roles?)

* We can't separate the rule creation into 2 steps anymore, like before, where we create everything regarding the UDM modules in one step (at package installation) and the cusomter or default policy rules in a second step.

* We have to regenerate all rules, in a atomic state, whenever there is a new extended attribute/option, module, UDM module Debian package installation, or change in the policies
→ UDM has to be the central place to create these definitions

* We can't allow customers to write cerbos rules on themself but always use our UDM specific DSL policy description. There is a small chance, that they could write role policies on top of everything.

**Open questions**:

* resource policies can dynamically generate `ouput` (CEL expressions) on `conditionNotMet` or `ruleActivated`. Can we use this to detect if we in general could display UI elements for the current user: it would yield a condition-not-met answer instead of a no-permissions-anser.

### Role policies
> Role policies are ABAC policies in which you specify a number of resources, each with a set of allowable actions that the role can carry out on the resource.

> In the simple case, they allow you to author permissions from the view of an IdP role, rather than for a given resource.

> Role policies are not standalone. They apply as an additive constraint on top of resource policies, so an action is only allowed if it is permitted by both the role policy and a matching resource policy.
> A role policy cannot grant access that the resource policy does not already allow, which means a resource policy is always required.

* role policies exists for restricting concrete principal roles
* role policies are an **additive constraint on top of resource policies**: an action must be permitted by both the resource policy and a matching role policy. (https://github.com/cerbos/cerbos/issues/2955 is a feature request to relax this)

The rights are restricted by the role policy - if a matching role policy exists for that principal role.
Actions not listed in the role policy's `allowActions` are implicitly denied for that role.

use when:
> Use role policies when permissions should be defined from the IdP role's perspective

> Simple allowlist semantics (list what's allowed, everything else denied)
> When you want to avoid explicit DENY rules

* Role policies only narrow permissions: "Given that this role is allowed by the resource policy, are there additional restrictions?"

This allows multiple roles to share the same resource policy while each role can have its own restrictions.

* role policies can inherit from other roles

> A parent role can be either an arbitrary IdP role or the name of another role policy within the system. Parent role resolution is recursive.

**Consequences for UDM**:

* Sounds like a ideal concept for UDM! In practice I could not make it working.
The audit logs couldn't tell me why exactly it was denied.
It probably has to do with the context-position based conditions in combination with the actions.
Or with multi-role assignments and the context-positions condition evaluation using `principal.role` work different in role rules than in resource rules.
Or whatever.

* It would add a overhead in the resource policy definition, as a "useless" fallback must grant all actions which are provided by the resource

* Additionally: We must write all rules in a atomic step, and replace the full directory with all rules for UDM, otherwise we will run into the vulnerability described below (which I could trigger with a permantent request reapplying). Alternatively disallow automatic role reloads and trigger it manually.

* it's not possible to expand resource-kinds with '\*' in a role policy; therefor all UDM modules must be specified e.g. for domain admin based rules. (requires re-generation on every module installation)

* `resource` in a role policy can't be a list - not possible to write re-usable rule

**Security considerations**:

There is a small timeframe where all the resource policies are written to disk and cerbos loaded them.
Then our custom roles are added as role policies from the rules specified by customers (or our default ones).
In the time frame between that, if my service does a request for a simple "domain user" with no special rules assigned, gets granted ALL permissions on all UDM modules because the role-rules are not there yet.
The same applies to the time window on Debian package upgrades/listener module processing, where the role-policies are removed for a short amount of time.

**Open questions** (only relevant if we could use the concept):

* Does the policy inheritance allow us to have pre-defined policies for each UDM module, with certain names like `users-user-read-all`, `user-user-write-all`?
* If yes, can this be used as API for customers to base their customizations on? But then those would be exposed as roles, not as "reusable privileges"

### Derived roles (named conditions)
Derived roles are for context-sensitive classification (owner, same-OU, department-member, etc.).
and help with computing context, not structuring permissions.

Derived roles can extend a `manager` to a `manager_of_bremen`.
Derived roles have names (`manager_of_bremen`) , but those names are internal and can't be assigned to the role attribute of the principal.

> Defining a derived role only creates a named condition

**Restrictions**:

* The resource policy must reference all derived roles, otherwise they wouldn't have an effect.

**Consequences for UDM**:

* It can only be used for our re-usable pattern for the generic `OU-admin@context-position` concept - the condition logic can be inserted there and re-used in the resource rules.

* When we extend that as CEL function, this saves only a `contextPosition.underneathOf(resourcePosition)` line - but adds the complexity to adjust all rules and specify the correct import path

* UDM auto-generated the resource policies. We wouldn't know the names of the (derived or IdP) roles which are written by customers.

* If we want to use derived roles for more than that, our apps would define all possible static IdP roles and customers can't do that anymore.

* Derived roles also apply only conditions to the whole resource. Our conditions are based on the granted action.
→ The derived roles are not useable for us.

### Scoped policies

* suitable for tenants
* resource and principal policies have an optional scope
* can be hierarchical, `.`-separated
* must be specified in the check request in the resource and principal
* e.g. we could have a scope `acme.bremen` the resource `ou=bremen,dc=base` would need to specify this scope.
* lenient scope can relax that each scope must be know by a resource policy

**Restrictions**:

There can't be multiple scopes for one principal e.g. located in Bremen and Berlin.

**Consequences for UDM**:
→ This would be nice for our OU admin.
But as there could be OU admins for multiple OUs, it's not suitable.
Also the OU admins might not be located in the OU itself. Therefor - where to know the scope from?
Maybe that is the Guardian-context information in the role?

### Principal policies

Cerbos supports principal policies to allow certain actions on resources for specific principals.
In UDM this would mean: `access by dn="uid=fbest,cn=users,…" to objectType="users/user" grant …`.

This is more a safetey mechanism intended for exceptional cases.

**Consequences for UDM**:

* At this point, we don't need this.
* → is it somehow a useful use case for our customers in the future?

### PlanResources

[PlanResources](https://www.cerbos.dev/blog/filtering-database-results-with-cerbos-query-plans) help to reduce the filterset.

From a request like `PlanResources(principal, kind="udm:module:users/user", action="object:search")` Cerbos can respond with a document with the possible rules for the principal,
which can be used to create a LDAP filter and search base+scope.
This solves performance problems of searching for all objects in UDM but at the end the role is only allowed to read users from a single OU.

**Consequences for UDM**:

* we could pre-filter with this, but afterwards everything still needs to go through as we cannot convert property-based (ABAC) restrictions into filters.

* requires that each UDM module is a own resource (well, everything else like a generic udm:module kind also makes no sense)

* Worth to consider thinking about *what* is a resource in UDM?

Each UDM object is a resource.
But what makes the kind of the resource?
Currently: the UDM object type.
But it could also be the position where the object lies in the directory tree.
And the resource consists of multiple representations e.g. a current object state or a modify old-new-comparision state.

Would it make sense to design certin OUs / LDAP containers as ressource (additionally or instead of the UDM object type).
Those would then be easy to filter via plan resources.

## Implementation of the concept in UDM

### resource policy offers ALLOW to writeonly/readonly/none - inner conflict

This could be the cause why role policies don't work for us.
The resource policy granted ALLOW for the actions `writeonly`, `readonly`, `none` by default
but the role policy did not.

maybe evaluate this in the language and then remove the wildcard and replace with all other things

if all the actions are requested, is the DENY/ALLOW per action?
    then it could work.

what if zufällig readonly/writeonly/none is granted? then the actual permissions get broken

derived roles must DENY those

### Limit: at maximum 500 actions can be checked

> cerbos.sdk.model.CerbosRequestException: number of actions (594) exceeds configured limit (500)

On a demo system with quite a lot of customer extended attributes defined, I reached into the limits when just searching for `users/user` objects.

```bash
$ udm settings/extended_attribute list | grep DN | wc -l
108
```

The requested actions are: `All UDM properties * {'read', 'write', 'none', 'writeonly'}`

We can:

1. compile Cerbos on our own and raise the limits, or ask upstream to do this

2. If we are able to reduce this to `{'read', 'none'}` we probably don't come into the limits anymore.
This would require that `write` doesn't include implicit `read`, making `writeonly` superfluous and forces customers to explicitly define read and write.

But this might get into conflict if multiple roles are assigned to the user:

> If the principal has multiple roles and at least one of their roles evaluates to have `EFFECT_ALLOW` for the action, the overall effect is `EFFECT_ALLOW`.

TODO: draw the concrete conflicting situation

This would only be solvable by extending all un-restrictive rules with more and more conditions e.g. regarding the position?
This is hard to manage, even with exposing derived-roles!

### Limit: at maximum 50 items can be checked

CheckResources has a maximum of 50 items!
That is important for testing, we should make sure to always have more than 50 objects in the tests!

### LDAP DN comparisons

For the position based context evaluation we need correct LDAP DN comparisions with a given LDAP scope of `base`, `onelevel`, `subtree`.
I could create a best-effort sometimes working solution for now, like:

```yaml
condition:
  match:
    expr: request.principal.attr.contextRoles.exists(cr, cr.role == "udm:default-roles:organizational-unit-admin"
      && (request.resource.attr.position == cr.position || request.resource.attr.position.endsWith(","
      + cr.position)))
```

**Solution:** We need to write such a CEL extension function in Go, using a Go LDAP library, as cerbos is compiled without support for non-native Go libraries.

### grpc vs HTTP client

The grpc client requires us to convert the whole object representation into a byte-serializeable format.
For a dynamic structure like UDM objects that's a lot of difficult transformation and also time-consuming on the client side (the data came from LDAP, we decoded it correctly to encode them again?!).

**Solution:** Use the HTTP client. Besides cerbos suggests to use the gRPC client.

### not enough sufficient rule metadata

With local guardian we could annotate each rule with a name and a description.
Cerbos provides resource descriptions, resouces rule names but no resources rule description, role rule names/descriptions, etc.

**Solution:** put the origin of the rule into the `metadata.annotations` free form field of the resource defintions and use YAML comments for the descriptions and names.

### get more use-cases and write tests for them!

Cerbos allows to make nice test definitions with simple YAML files shipped.
We should make use of it for the existing use-cases.

We should have a list of more real customer use cases, model them and write test cases for it!

### virtual UDM modules

`computers/computer` is just a virtual/non-existing object type of `computers/{domaincontroller_master,*}`-module.
It is unclear, what problems we might face with virtual modules.

### Rule renewal / package integration / distribution

Every package which provides a UDM module, extened attribute or similar, must invoke a re-generation of the rules on installation and de-installation.
Therefor the data must be distributed in the whole domain via our registration mechanism.

The complexity for this is high, and we shouldn't offer access to our internal formats as API, which rely on the current way in which we integrade authorization in UDM.

To be flexible here, we should
create a debhelper for Debian packages providing UDM modules/extended attributes that cause the correct things on installation/removal:
`debian/rules` with `--with udm-module` and `--with udm-policy` any maybe `X-Provides-UDM-Module` debian control flags are enough to trigger the complete logic in a generic wrapper.

### Changes in comparison with Guardian

#### Cerbos has no "target role" concept
Guardian required that also the roles of resources (targets) were added to the object.
(e.g. in the portal use-case we theorized about matching tiles via a rule at the target).
Cerbos doesn't have this concept.

→ This improves much of the performance in UDM as the target roles must not be searched for every object.

#### no `new_target` / `old_target` representation

Guardian has a concept that the principal representation contained a `old_target`, and `new_target` - for all action checks.
And conditions were globally registered and required to check against one of these keys.
It was always unclear, to which of the keys the condition applied - especially as many use cases like search and get doesn't have old/new values but only current states.

Cerbos doesn't have such a concept.

In the PoC we replaced this by `request.resources.attrs` containing the current / OLD representation and `request.resources.attrs.new` contains the updated object state on modifications.

TODO: we could also define 2 resources (even schematized): one for search/get and one for modifications/create/move/etc. (see also "Plan resources"!).

### file and line counts

We compile the resource rules from 143 lines in `/usr/share/univention-directory-manager-modules/policies/udm-default-authorization-roles.policy`.

The compiled Guardian YAML files had `24.362` lines.
in
```
# find /usr/share/univention-guardian-server/policies/udm -type f | wc -l
116
# wc -l $(find /usr/share/univention-guardian-server/policies/udm -type f)
  4577 insgesamt
```

using role policies it would bloat up to `21236` lines, as all resources would need to be defined with all actions.

## Architecture

UDM implements attribute-based access control (ABAC) using Cerbos as the Policy Decision Point (PDP).

Cerbos evaluates authorization policies and returns authorization decisions. UDM remains the Policy Enforcement Point (PEP) and is responsible for enforcing those decisions, filtering objects and properties, and preventing information disclosure.

The overall architecture is:

```text
User
  |
  v
UDM (PEP)
  |
  | CheckResources / PlanResources
  v
Cerbos (PDP)
  |
  v
ALLOW / DENY decisions
```

Cerbos is responsible only for policy evaluation.

UDM is responsible for:

* Object filtering
* Property filtering
* LDAP access
* Old/New state comparison
* Information disclosure prevention
* Effective permission calculation
* Enforcement of write restrictions

### Authorization Model

The authorization model consists of:

* Principals
* Resources
* Actions
* Policies
* Conditions

#### Principals

The principal represents the authenticated actor.

Example:

```json
{
  "id": "uid=helpdesk,cn=users,dc=example,dc=com",
  "roles": [
    "udm:default-roles:helpdesk-operator"
  ],
  "attr": {
    "contextRoles": [
      {
        "role": "udm:default-roles:helpdesk-operator",
        "position": "ou=bremen,dc=example,dc=com"
      }
    ]
  }
}
```

The `contextRoles` attribute contains role-specific contextual information.

Unlike the previous Guardian implementation, contexts are not globally registered.

Contexts are dynamic request attributes.

### Resources

Each UDM module is represented as its own Cerbos resource kind.

Examples:

```text
udm:module:users/user
udm:module:groups/group
udm:module:mail/domain
udm:module:container/ou
```

This allows:

* Module-specific policies
* Future usage of PlanResources
* Efficient LDAP filter generation

A resource additionally contains attributes describing the target object.

Example:

```json
{
  "kind": "udm:module:users/user",
  "id": "uid=test,cn=users,dc=example,dc=com",
  "attr": {
    "dn": "uid=test,cn=users,dc=example,dc=com",
    "position": "cn=users,dc=example,dc=com",
    "properties": {
      "firstname": "John",
      "lastname": "Doe"
    }
  }
}
```

### Actions

All actions are prefixed with `udm:`.

#### Object actions

```text
udm:object:read
udm:object:search
udm:object:create
udm:object:modify
udm:object:rename
udm:object:move
udm:object:remove
udm:object:restore
udm:object:report-create
```

#### Property actions

```text
udm:property:<property>:read
udm:property:<property>:write

udm:property:<property>:readonly
udm:property:<property>:writeonly
udm:property:<property>:none
```

Examples:

```text
udm:property:firstname:read
udm:property:firstname:write

udm:property:password:writeonly
udm:property:guardianRoles:none
```

Property actions are queried explicitly by UDM.

This allows UDM to determine whether a specific property should be visible or writable.

### Resource Policies

Resource policies describe both the technical capabilities of a UDM resource and the authorization rules defined in the UDM authorization DSL.

They are generated automatically by:

```text
univention-configure-udm-authorization
```

One resource policy exists for every UDM module.

Example:

```yaml
resourcePolicy:
  resource: "udm:module:users/user"
```

The generator combines all authorization rules from the DSL into these resource policies.

Each generated rule specifies:

* the object or property actions it grants
* the roles or derived roles it applies to
* optional authorization conditions, such as

  * position-based scope restrictions
  * named DSL conditions
  * value-based (CEL) constraints

Each DSL grant is compiled into an individual Cerbos rule. This keeps conditions local to the actions they protect and avoids unintentionally restricting unrelated actions.

Besides the generated authorization rules, the resource policies also contain:

* the technical wildcard action definitions supported by the resource
* global deny rules
* technical administrator rules

Resource policies therefore become the single source of truth for authorization decisions.

### Derived Roles

Position-based role contexts are represented as Cerbos Derived Roles.

For every distinct combination of

* parent role
* context type
* scope

the generator creates one derived role.

Example:

```yaml
derivedRoles:
  definitions:
    - name: organizational-unit-admin-position-subtree
      parentRoles:
        - udm:default-roles:organizational-unit-admin
```

The derived role evaluates whether the authenticated principal possesses the required contextual role, for example by checking

```cel
request.principal.attr.contextRoles.exists(...)
```

Derived roles encapsulate only reusable role-context evaluation.

They do **not** grant permissions themselves.

Permissions remain defined exclusively by the resource policies, which reference the derived roles where required.

This separation keeps contextual role evaluation reusable while allowing authorization conditions that depend on individual actions (for example value comparisons) to remain attached directly to the corresponding resource-policy rule.

### Context-based Authorization

Several default roles are scoped to LDAP positions.

Examples:

* Organizational Unit Administrator
* Helpdesk Operator
* Linux Client Manager

A role context is represented as:

```json
{
  "role": "udm:default-roles:organizational-unit-admin",
  "position": "ou=bremen,dc=example,dc=com"
}
```

Conditions are translated into CEL expressions.

Example:

```cel
request.principal.attr.contextRoles.exists(cr,
  cr.role == "udm:default-roles:organizational-unit-admin" &&
  (
    request.resource.attr.position == cr.position ||
    request.resource.attr.position.endsWith("," + cr.position)
  )
)
```

Supported LDAP search scopes:

* base
* onelevel
* subtree
* not children
* not base+one

### Old and New State

For create and modify operations UDM provides both states.

Example:

```json
{
  "attr": {
    "dn": "uid=test,cn=users,dc=example,dc=com",
    "position": "cn=users,dc=example,dc=com",
    "properties": {
      "firstname": "John",
      "lastname": "Doe"
    },
    "new": {
      "dn": "uid=test,cn=users,dc=example,dc=com",
      "position": "cn=users,dc=example,dc=com",
      "properties": {
        "firstname": "Jonathan",
        "lastname": "Doesit"
      },
    }
  }
}
```

Policies may compare old and new values.

This replaces Guardian's old-target/new-target model.

### Property Override Semantics

Cerbos evaluates individual actions.

UDM computes effective property permissions.

The following precedence is applied:

```text
none
  > readonly / writeonly
    > read / write
```

Examples:

```text
write + readonly
  => readonly

read + none
  => none

writeonly + read
  => writeonly
```

This logic is intentionally implemented inside UDM and not inside Cerbos.

### Policy Generation

Policy generation is performed by:

```text
univention-configure-udm-authorization generate
```

Responsibilities:

* Discover all UDM modules and their properties
* Parse the UDM authorization DSL
* Compile DSL rules into Cerbos resource-policy rules
* Generate reusable derived roles for contextual role evaluation
* Merge generated authorization rules with the technical resource policies
* Write the complete policy tree atomically

The generator performs the complete compilation in memory before writing the resulting policy tree. This guarantees that Cerbos never observes a partially generated set of policies.

The generated resource policies contain both the technical description of each UDM resource and the authorization rules compiled from the DSL. Context-based role evaluation is extracted into reusable derived roles, while grant-specific conditions remain attached to the individual resource-policy rules that they protect.

### Policy Directory Layout

Policies are stored below:

```text
/usr/share/univention-guardian-server/policies/udm/
```

The directory structure follows the Cerbos policy layout conventions:

```text
derived_roles/
  *.yaml

resource_policies/
  udm/
    users-user.yaml
    groups-group.yaml
    container-ou.yaml
    ...

    users-user_test.yaml
    groups-group_test.yaml
    ...

    testdata/
      principals.yaml
      resources.yaml
```

The `resource_policies/udm/` directory contains one generated resource policy for every UDM module.
The `role_policies/` directory is retained for optional manually maintained Cerbos role policies. Role policies are not generated from the UDM authorization DSL and are not part of the primary authorization model.

The complete generated policy tree is created in a temporary location and moved into place atomically. Generated content may therefore be recreated at any time and must not be modified manually.

### Why Cerbos?

Compared to the previous Guardian-based implementation:

* No management API
* No permission registration
* No capability registration
* No context registration
* No database-backed policy objects
* Native policy-as-code
* Native CEL conditions
* Native YAML policies
* Better support for future PlanResources usage

The responsibility split is clearer:

```text
Cerbos
  = Policy Decision Point

UDM
  = Policy Enforcement Point
```

This significantly reduces architectural complexity while preserving the flexibility required for UDM-specific authorization use cases.
