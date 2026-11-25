[TOC]

# UDM Authorization using Cerbos

> This document describes the Cerbos-based UDM authorization design and the
> implementation developed so far. It separates implemented mechanisms,
> intended semantics, and outstanding work. The concrete implementation may
> still evolve; in particular, search authorization and some multi-role cases
> are not considered finished.

## Overview

UDM uses Cerbos as its **Policy Decision Point (PDP)**. UDM remains the
**Policy Enforcement Point (PEP)**: it constructs principals and resources,
requests decisions, restricts returned objects and properties, and enforces
writes. Cerbos does not perform LDAP operations or enforce the result itself.

```text
Authenticated user / UDM client
             |
             v
       UDM authorization (PEP)
       - actor and context roles
       - target representations
       - object/property enforcement
             |
             | CheckResources (Cerbos SDK)
             v
          Cerbos (PDP)
       resource policy + role policy
       CEL / LDAP DN functions
             |
             v
       Decisions per action
             |
             v
       UDM filters / allows / rejects
```

The authorization rules are authored in a UDM-specific DSL (`*.policy`) and
compiled into Cerbos YAML. A single policy generation run must produce a
consistent policy tree; generated files should not be edited manually.

### Former Guardian to Cerbos terminology

| Guardian | Cerbos / UDM |
| --- | --- |
| Actor | Principal |
| Target | Resource |
| Role | Principal role with a corresponding Cerbos role policy |
| Permission | Action |
| Capability | DSL grant, compiled into a role-policy rule |
| Context | Request attribute, currently `principal.attr.context_roles` |
| Condition | CEL expression |
| Capability/context registration | Not required as a separate Cerbos management operation |
| Management API | Not needed for file-based policy generation |

The names of UDM roles (including customer-defined roles) are assigned to
principals. Contexts remain **dynamic data on the principal**, not distinct
Cerbos roles per LDAP position. A single principal can have the same role in
multiple positions.

## Authorization model

### Principals and contextual roles

The principal ID is the actor's LDAP DN. The principal has a set of plain role
names and a separate list of context assignments.

```json
{
  "id": "uid=helpdesk,cn=users,dc=example,dc=com",
  "roles": ["udm:default-roles:helpdesk-operator"],
  "attr": {
    "context_roles": [
      {
        "role": "udm:default-roles:helpdesk-operator",
        "position": "ou=bremen,dc=example,dc=com"
      }
    ]
  }
}
```

UDM normalizes role assignments into the principal's role list and contextual
assignments. CEL rules check both the **role name** and the **matching context**.
Merely possessing a context with a matching DN but a different role must not
grant permission.

### Resources

Each UDM module is a distinct Cerbos resource kind; each checked UDM object is
a resource instance:

```text
udm:module:users/user
udm:module:groups/group
udm:module:container/ou
udm:module:container/cn
```

The resource ID is a nonempty DN for object checks. Its attributes include
`dn`, `position`, `properties`, `options`, and, for writes, the `new`
representation. For example:

```json
{
  "kind": "udm:module:users/user",
  "id": "uid=test,cn=users,dc=example,dc=com",
  "attr": {
    "dn": "uid=test,cn=users,dc=example,dc=com",
    "position": "cn=users,dc=example,dc=com",
    "properties": {"firstname": "John"},
    "new": {
      "dn": "uid=test,cn=users,dc=example,dc=com",
      "position": "cn=users,dc=example,dc=com",
      "properties": {"firstname": "Jonathan"}
    }
  }
}
```

For modifications, moves, and renames, the outer representation is the old
state and `attr.new` is the proposed state. For creation there is no real old
state: the resource ID, DN and position must be populated from the proposed
object, rather than an empty `old_dn`. Conditions should not assume that a
historical state exists for a newly created object.

For moves, the source and destination can require different positional
permissions. The design discussed for UDM is to authorize the `move` action
against both the source and destination, while not automatically requiring
`read` at the destination. Verify the installed enforcement code before relying
on this additional check.

### Actions

All UDM actions use the `udm:` prefix, distinguishing them from actions for
other applications sharing the same Cerbos instance.

Object actions:

```text
udm:object:search       udm:object:read
udm:object:create       udm:object:modify
udm:object:rename       udm:object:move
udm:object:remove       udm:object:restore
udm:object:report-create
```

Property actions:

```text
udm:property:<property>:search
udm:property:<property>:read
udm:property:<property>:write
udm:property:<property>:none
udm:property:<property>:readonly
udm:property:<property>:writeonly
```

`none`, `readonly`, and `writeonly` are **negative permission signals**, not
Cerbos `EFFECT_DENY` decisions. An `EFFECT_ALLOW` on one of those actions tells
UDM to remove the corresponding effective permission. This design allows
property overrides, but has important implications when a principal has
multiple roles.

UDM calculates effective property permissions using this precedence:

```text
none > readonly / writeonly > read / write
```

For example, `write + readonly` means not writable; `read + none` means not
readable. An allow-all role policy must **never** include these negative signals
unless the restriction is deliberate.

The DSL currently expands `write` into `write`, `read`, and `search`, and
`read` into `read` and `search`. These implications are implemented when
compiling policies, not inferred by Cerbos at evaluation time.

## Policy architecture

### Resource policies: technical boundaries and global denies

There is **one Resource Policy per concrete UDM module resource kind**. The
Resource Policy does not enumerate individual properties and does not contain
the bulk of the role-specific DSL rules.

Instead, it contains:

* An `EFFECT_ALLOW` for the internal parent role `udm:super-admin`.
* Only the **object actions actually supported by the UDM module** (as
  determined using `univention.admin.modules.supports()`, with known special
  cases).
* The property wildcard `udm:property:*:*`, which covers both positive and
  negative property permission signals.
* Global, resource-specific `EFFECT_DENY` safeguards, such as the rule
  preventing management of users with `uidNumber == 0`.

Illustrative resource policy (the object-action list varies per module):

```yaml
apiVersion: api.cerbos.dev/v1
resourcePolicy:
  resource: udm:module:users/user
  version: default
  rules:
    - name: deny-uid-number-zero
      # Generated global DENY condition covering old/new state.
      # Omitted here for readability.
      actions: ["udm:*:*:*", "udm:*:*", "udm:*"]
      effect: EFFECT_DENY
      roles: ["*"]
      condition:
        match:
          expr: "..."
    - name: allow-role-policy-actions-users-user
      actions:
        - udm:object:create
        - udm:object:read
        - udm:object:search
        - udm:object:modify
        - udm:property:*:*
      effect: EFFECT_ALLOW
      roles:
        - udm:super-admin
```

The example is schematic, **not a complete deployable policy**. In particular,
use the generator's complete global DENY condition and actual module
capabilities. The generated YAML includes human-readable comments reporting
which object operations the module supports and how many property definitions
it exposes.

The wildcard is intentionally `udm:property:*:*`, **not** `*` or
`udm:property:*`: the property action has four colon-separated components.
Restricting the allowlist to the `udm:` action namespace also avoids accepting
unrelated application actions on UDM resources.

Because Resource Policies are tied to concrete kinds, new UDM modules require
new Resource Policies. Extended attributes do **not** require enumerating a
new property-action rule in those Resource Policies.

### Role policies: effective permissions from the DSL

**Role Policies are the primary output of the UDM DSL compiler.** They express
which actions a role may perform on which UDM resources, with conditions for
positions, named expressions, or values.

Role Policies are an additional constraint: a permission must be allowed by
the relevant Resource Policy *and* by a matching Role Policy. All generated
Role Policies inherit the internal parent role:

```yaml
rolePolicy:
  role: udm:default-roles:helpdesk-operator
  version: default
  parentRoles:
    - udm:super-admin
  variables:
    import:
      - udm_variables
  rules:
    - resource: udm:module:users/user
      allowActions:
        - udm:object:read
        - udm:property:username:read
      condition:
        match:
          expr: V.position_example
```

`V.position_example` represents a generated named CEL variable; the name and
full expression differ in actual output. The internal parent role must never
be assigned directly to an end user.

A single role can be defined in **multiple DSL files**. The generator must
collect its rules and variables across those files and emit **one** Role Policy
per role; otherwise later files overwrite earlier permissions. A cross-file
merge was implemented during development and requires regression tests.

Multiple grants for the same `(role, resource, action)` are alternative paths
to permission and must be combined using `condition.match.any` (logical OR).
Conditions within a single grant (position, `if`, `values`) are combined with
`all` (logical AND). Actions with the same final condition can be grouped into
a single rule. An unconditional grant for an action makes conditional
alternatives for that action redundant.

This separation is important: grouping only by resource can accidentally
extend a `modify` permission to positions where only `read` was intended.

### Domain administrator

The domain administrator is also represented by a Role Policy and uses the
same parent role. Unlike ordinary roles, it is generated independently of
the DSL. It permits only **positive** actions:

```yaml
rolePolicy:
  role: udm:default-roles:domain-administrator
  version: default
  parentRoles: [udm:super-admin]
  rules:
    - resource: "udm:module:*"
      allowActions:
        - "udm:object:*"
        - "udm:property:*:search"
        - "udm:property:*:read"
        - "udm:property:*:write"
```

The Resource Policy still restricts object actions to operations available in
the concrete UDM module. The example `resource: "udm:module:*"` is the current
generator's Role Policy pattern; Resource Policies themselves remain
module-specific.

An extra role can still grant a negative property signal to a principal who
also has the domain-administrator role. Cerbos merges permissions across roles;
UDM's negative-action interpretation is separate. This is a **known semantic
issue**, not something solved merely by omitting negative actions from the
domain-administrator Role Policy.

### CEL variables and LDAP DN comparisons

Position and context conditions use exported CEL variables (such as
`V.position_...`) from `variables/udm_variables.yaml`. The principal context
list is normalized into `V.udm_assignments` where available.

LDAP positions must be compared as LDAP DNs rather than by string suffix or
case-sensitive string equality. The custom Cerbos `ldapDN()` extension handles
DN-aware comparisons. Supported DSL positional scopes include:

| DSL scope | Intended relationship |
| --- | --- |
| `base` | Equal DN |
| `one` / `onelevel` | One level below the base |
| `sub` / `subtree` | Base or a descendant |
| `children` | Descendant, excluding base |
| `ancestors` | Ancestor, excluding the referenced DN |
| `hierarchy` | Base, ancestors, and descendants |

Generated conditions may use methods such as `matchOneLevel()` and
`matchSubtree()`. When authoring context-based rules, verify the direction of
each comparison; `ancestors` and `hierarchy` are particularly easy to reverse.

Derived Roles remain a Cerbos feature, but **they are not the central context
mechanism in this implementation**. Context checks are attached to the
corresponding role-policy rules via CEL variables.

### Value conditions and implicit actions

Consider:

```text
grant properties="guardianMemberRoles" permission="write" values="$newValue$.all(r, r == 'udm:default-roles:domain-user')"
```

The `values` expression restricts the **explicit** `write` permission, not
other grants in the same `to` clause. It must not leak into a separate
`read`/`search` grant. The compiler also distinguishes actions implied by
`write`: derived `read` and `search` actions do not inherit a condition on
`$newValue$`, since ordinary read requests have no proposed new value.

Tests should cover both directions: valid and invalid proposed values, reads
without `attr.new`, and multiple grants or conditions for the same action.

## Policy generation and deployment

The generator is:

```text
univention-configure-udm-authorization
```

Typical use:

```bash
univention-configure-udm-authorization generate
univention-configure-udm-authorization generate --unstrict
univention-configure-udm-authorization generate --exclude-tests
```

Strict checking is the intended default; `--unstrict` relaxes it. The generator
reads installed `.policy` files, introspects available UDM modules, produces
Resource Policies and Role Policies, exports CEL variables, and constructs a
new generated policy tree. The directory replacement should be atomic so
Cerbos never observes a partially written policy set.

The current host policy root used by the generator is:

```text
/usr/share/univention-guardian-server/policies/udm/
```

A representative generated layout is:

```text
resource_policies/
  udm/
    users-user.yaml
    groups-group.yaml
    ...
role_policies/
  udm-default-roles-domain-administrator.yaml
  ...
variables/
  udm_variables.yaml
derived_roles/          # Only if needed by generated policies
_tests/                # Installed-policy suites, unless excluded
  <suite>/
    *_test.yaml
    testdata/
      principals.yaml
      resources.yaml
```

### Test infrastructure

The packaging location for immutable test suites is:

```text
/usr/share/univention-directory-manager-modules/cerbos-tests/
```

Each immediate subdirectory represents a suite, containing Cerbos
`*_test.yaml` files, optional `testdata/principals.yaml` and
`testdata/resources.yaml`, and optionally one or more `*.policy` files.

* A suite **without** its own `.policy` files tests the generated policies from
  the installed DSL configuration. These suites may be copied into `_tests/`
  in a generated bundle.
* A suite **with** its own `.policy` files is generated and compiled in an
  isolated temporary tree. Its DSL files must not be copied into a production
  bundle.

The host-side `test` command was developed to reproduce the previous
`run-cerbos-tests` script's behavior:

```bash
univention-configure-udm-authorization test
univention-configure-udm-authorization test --unstrict
```

The test command generates temporary policy trees and invokes `cerbos compile`
with policy tests; strict evaluation is the default. It does not modify the
active installation.

Build-time testing is deferred: We can't execute docker during package builds.

`generate --exclude-tests` omits the packaged test suites from generated
bundles. The exact command-line options and runtime selection should be
checked against the version of the generator deployed on the host.

Useful test scenarios include:

* Multiple grants for the same resource/action with different positions.
* One role split across multiple `.policy` files, including same-resource
  actions and imported CEL variables.
* `values` constraints that must not affect unrelated actions or implicit
  reads.
* Domain-administrator positive permissions and global DENY conditions.
* Contextless principals, contexts for a different role, and multiple OUs.
* DN spelling variations and the `+` character in LDAP DNs.
* Negative property actions and principals with several assigned roles.

**A passing Cerbos policy test is not a full LDAP/UDM integration test.** It
cannot verify HTTP behavior, search-result redaction, LDAP exceptions, or
whether UDM really executes the checks before sensitive operations.

## Runtime enforcement and performance

UDM asks Cerbos for object actions and property actions, then calculates the
readable or writable property set. Negative property signals override
positive ones in UDM's post-processing. The Cerbos HTTP SDK adapter is a thin
client wrapper; it does not replicate authorization logic.

Cerbos's per-request action limit requires attention on modules with many
extended attributes. Action queries are deduplicated and large checks must be
batched without changing the effective result. The first read-path optimization
(`V1`) stopped requesting property `write` when reading an object, relying on
the DSL compiler to emit explicit `read` for a `write` grant. Negative signals
remain necessary for property filtering.

The resource-policy wildcard reduces policy size and regeneration churn; it
does **not** itself reduce the number of actions requested for each read.

## Search authorization: design and unresolved work

`search` is intended to represent authorization of an LDAP **query**, not
merely a weaker form of object `read`. A complete flow has three layers:

1. Check permission to perform the requested search on a given module, base,
   scope and LDAP filter.
2. Check which returned objects may be read.
3. Filter returned properties according to their property permissions.

Search-filter attributes may appear under UDM property names or raw LDAP
attribute names. The proposed implementation parses the LDAP filter using
`univention.admin.filter.parse()` and `walk()`, then resolves LDAP attribute
names through the module mapping. `objectClass` can be a special case; the
handling of other unmapped attributes needs an explicit security policy.

An authorization check for the **base DN alone is not enough** to prove an
entire `subtree` search is within an allowed area. Scope and search-base
conditions must be considered together. Filtering results after LDAP execution
also does not eliminate disclosure via timing, search counts, or pagination.

### Non-disclosure behavior of LDAP searches

The previous implementation intentionally distinguishes these cases:

| Case | Required observable result |
| --- | --- |
| Search base missing | `NO_SUCH_OBJECT` / UDM `noObject` |
| Search base exists but is not visible | Same `NO_SUCH_OBJECT` / `noObject` |
| Search base visible, but the query/filter is not permitted | Empty result (subject to existing API options) |
| Search permitted, but no returned objects are visible | Empty result |
| Search permitted and results visible | Filtered results |

The base-visibility check must run **before** rejecting a query based on its
filter or scope. Returning a different exception for an unreadable base than
for a nonexistent base would create an information-disclosure channel.
Behavioral compatibility needs UDM REST and LDAP integration tests, not just
Cerbos policy tests.

Search semantics, filter-attribute mapping, and the separation of module-level
search availability from permission to read an individual result remain areas
for further development.

## Security considerations and known limitations

* **Atomic policy replacement:** The final generated policy tree must replace
  the previous tree as a unit. An intermediate state with broad Resource
  Policies but missing Role Policies is unsafe.
* **Internal parent role:** `udm:super-admin` must not be
  assigned to real users. Its Resource Policy privileges are broad by design.
* **Global DENY rules:** These remain in Resource Policies and must be tested
  against all relevant actions, including creation and changes to `attr.new`.
* **Multiple roles:** A principal may receive negative property signals from
  a second role even when the domain-administrator Role Policy contains only
  positive actions. This needs a deliberate semantic solution in UDM.
* **Multi-file DSL definitions:** No role should be silently overwritten by a
  later file. Keep tests for rule merging, action-specific conditions, and
  variable collisions.
* **Search side channels:** Base visibility, query authorization and result
  redaction must maintain the intended LDAP exception semantics.
* **DN and state representation:** Compare DNs via `ldapDN()` and ensure the
  correct old/new DN and position for `create`, `move`, and `rename`.
* **Large requests:** Both action-count and resource-count limits need
  reliable batching and merging.
* **Generated data is not a customer API:** Customers should author UDM DSL
  policies. Generated Cerbos YAML is an implementation artifact.

## Other Cerbos facilities considered

**Derived Roles** are useful for reusable conditions, but the current design
uses Role Policies with CEL variables to express role-specific contextual
permissions. **Scoped policies** were considered for LDAP OUs; one principal
may have multiple independent OU assignments, so Cerbos's single hierarchical
scope is not a direct replacement. **Principal Policies** may be useful for
exceptional identities but are not part of the ordinary UDM DSL model.

**PlanResources** may eventually help narrow LDAP searches before fetching
objects. It cannot replace enforcement of arbitrary UDM property conditions or
all post-search filtering. This remains a performance/design opportunity, not
part of the basic authorization guarantee.

## Related upstream Cerbos issues

These upstream issues describe improvements that would make UDM's authorization
use cases easier to express or maintain. They are proposals, not assumptions
about features available in our deployed Cerbos version.

**[#3492](https://github.com/cerbos/cerbos/issues/3492) - Contextual role assignments and scoped permissions.**
UDM needs multiple assignments of the same role with independent contexts (for
example, different OUs or schools). Currently, UDM carries these assignments in
principal attributes and generates role-specific CEL conditions. The discussion
explores first-class contextual role assignments, multiple principal scopes,
derived roles in role policies, and reusable parameterized conditions.

**[#3473](https://github.com/cerbos/cerbos/issues/3473) - Raise the 500-actions-per-resource limit.**
UDM can exceed 500 actions when evaluating permissions for modules with many
extended attributes (714 in the reported example). Although
`server.requestLimits.maxActionsPerResource` is configurable, its maximum is
hard-capped at 500 by the internal `requestItemsMax` constant, which also caps
`maxResourcesPerRequest`. Raising that constant (for example, to 4000) requires
a custom Cerbos build; splitting requests remains a workaround.

**[#3269](https://github.com/cerbos/cerbos/issues/3269) - List roles through the Admin API.**
A role-listing endpoint would let UDM present available roles as selectable
options in administrative user interfaces instead of maintaining a separate
role inventory.

**[#3268](https://github.com/cerbos/cerbos/issues/3268) - Names and metadata on individual rules.**
Allow rule names and per-rule metadata in Role and Principal Policies. This
would preserve DSL descriptions, source files and line numbers directly in
generated policies instead of relying on YAML comments.

**[#3267](https://github.com/cerbos/cerbos/issues/3267) - Improve policy-concept documentation.**
Clarify the relationships between IdP roles, Derived Roles, Resource Policies,
Role Policies and scopes, with more practical examples and links to deeper
explanations. This would make the policy design choices less ambiguous.

**[#3210](https://github.com/cerbos/cerbos/issues/3210) - Extensible CEL functions.**
Support application-specific CEL operations, especially correct LDAP DN
equality and scope comparisons. UDM currently needs a custom Cerbos build for
its `ldapDN()` extension; an extension mechanism would reduce that maintenance
burden and could support other normalized values such as MAC addresses.
