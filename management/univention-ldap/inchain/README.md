# slapo-inchain

`slapo-inchain` is an OpenLDAP overlay prototype implementing Microsoft Active Directory's recursive membership matching rule:

```text
LDAP_MATCHING_RULE_IN_CHAIN / LDAP_MATCHING_RULE_TRANSITIVE_EVAL
OID: 1.2.840.113556.1.4.1941
```

It allows filters such as:

```ldap
(<dn-valued-attribute>:1.2.840.113556.1.4.1941:=<DN>)
```

The overlay rewrites the filter to an equality OR over the asserted DN and all recursively found parent DNs in the current database suffix.

Examples:

```ldap
(member:1.2.840.113556.1.4.1941:=uid=alice,ou=users,dc=example,dc=com)
(member:inChainMatch:=uid=alice,ou=users,dc=example,dc=com)
(uniqueMember:1.2.840.113556.1.4.1941:=uid=alice,ou=users,dc=example,dc=com)
(owner:1.2.840.113556.1.4.1941:=cn=some-object,dc=example,dc=com)
```

The attribute must have Distinguished Name syntax (OID: `1.3.6.1.4.1.1466.115.121.1.12`).

By default, all DN-syntax attributes are accepted. An allowlist can be configured with repeated `inchain-attr` / `olcInChainAttr` values.
In production, always set an explicit inchain-attr allowlist limited to attributes that have an equality index -
leaving the default (all DN-syntax attributes accepted) means an unindexed attribute nobody intended to expose can still trigger full subtree scans.

Unsupported cases:

- no attribute description in the extensible match
- `dnAttributes` flag
- non-DN-syntax attributes
- the in-chain matching rule anywhere below `NOT`
- invalid DN assertion values

## ACL behaviour

Default:

```conf
inchain-ignore-acls FALSE
```

Internal recursive searches use the original operation identity. This means the chain expansion respects the caller's LDAP permissions. If an intermediate group or its membership attribute is not searchable/readable according to ACLs, that path is invisible to the user.

Privileged mode:

```conf
inchain-ignore-acls TRUE
```

Internal recursive searches use the current database `rootdn`. Since `rootdn` is not subject to OpenLDAP ACL restrictions, this can reveal hidden membership relationships through search result truth values. Enable this only if that behaviour is explicitly intended.

The option requires the database to define a `rootdn`.

## Configuration: slapd.conf

```conf
moduleload inchain.so

database mdb
suffix "dc=example,dc=com"
rootdn "cn=admin,dc=example,dc=com"

overlay inchain

# attibute allowlist (if omitted, all DN-syntax attributes are accepted, security risk!)
# inchain-attr member
# inchain-attr uniqueMember

inchain-max-depth 16
inchain-max-nodes 1024
inchain-max-searches 256
inchain-ignore-acls FALSE
```

## Configuration: cn=config

```ldif
dn: cn=module{0},cn=config
changetype: modify
add: olcModuleLoad
olcModuleLoad: inchain.la

dn: olcOverlay=inchain,olcDatabase={1}mdb,cn=config
objectClass: olcOverlayConfig
objectClass: olcInChainConfig
olcOverlay: inchain
olcInChainMaxDepth: 16
olcInChainMaxNodes: 1024
olcInChainMaxSearches: 256
olcInChainIgnoreACLs: FALSE
```

Optional allowlist:

```ldif
olcInChainAttr: member
olcInChainAttr: uniqueMember
```

## Current database suffix handling

There is no `inchain-base` / `olcInChainBase` setting.

The overlay uses the current backend's normalized suffix, for example `be->be_nsuffix[0]`, as the base for internal recursive searches. Configure the overlay separately per database where you want the rule to be available.

## Indexing

Create equality indexes for the DN-valued membership attributes you expect to query:

```conf
index member eq
index uniqueMember eq
```

For `cn=config`:

```ldif
olcDbIndex: member eq
olcDbIndex: uniqueMember eq
```

Without an equality index, each recursion step may become expensive (DoS risk!).

## Build

Place this directory in an OpenLDAP source checkout, for example:

```text
openldap/contrib/slapd-modules/inchain/
```

Then build:

```sh
make LDAP_SRC=../../..
```

Install:

```sh
make LDAP_SRC=../../.. install DESTDIR=/tmp/pkg
```

You may need to adjust `LDAP_SRC`, `LDAP_BUILD`, `moduledir`, or distribution-specific compiler/linker flags.

## Error handling

The overlay returns:

- `LDAP_INAPPROPRIATE_MATCHING` for unsupported attributes or unsupported extensible-match forms
- `LDAP_INVALID_DN_SYNTAX` for invalid DN assertion values
- `LDAP_ADMINLIMIT_EXCEEDED` for depth, node, or internal-search limits
- `LDAP_UNWILLING_TO_PERFORM` when `inchain-ignore-acls TRUE` is configured but the database has no `rootdn`, or when the matching rule is used anywhere below `NOT`
- backend search errors from internal recursive searches unchanged

## Safety limits

Defaults:

```text
inchain-max-depth    16
inchain-max-nodes    1024
inchain-max-searches 256
inchain-ignore-acls  FALSE
```

`inchain-max-depth` protects against very deep chains.

`inchain-max-nodes` protects against very large group graphs.

`inchain-max-searches` protects against excessive internal recursive searches.

Cycles are handled by tracking normalized DNs already seen during expansion.
