# Test matrix requirements for full coverage

Attribute values:
* ASCII alphanumeric
* ASCII special
* ASCII New-line
* ASCII double slashes (//)
* UTF-8 umlaut chars
* UTF-8 special chars e.g. smileys
* Chars to be escaped in a LDAP filter: ( ) = :
* Chars to be escaped in LDAP DN: + = ,
* very long (limit reaching)
* muliple consecutive, leading or trailing spaces in DN / attribute
* NULL bytes
* binary (jpegPhoto)
* ~Empty [not allowed]~

Attribute value position:
* RDN
* parent DN
* forward reference attribute (e.g. uniqueMember)
* backward reference attribute (e.g. memberOf)

Type Attribute value: [Reference attributes]
* multi value
* single value

Differing input DN representation:
* exact / normalized
* different casing (`cn=Foo`)
* OWS: `cn = foo`
* name aliases `commonName = foo`
* multi valued RDN order arrangement

Actions:
* search
* read (=search scope=base)
* (compare)
* create
* modify
* rename
* rename change only case
* remove
* remove subtree / recursive
* move
* move subtree
* modify + rename
* modify + move
* modify + move subtree
* move to recyclebin
* restore to original position
* restore to different destination
* create + remove + recreate

Error conditions:
* target object does not exists [all]
* destination object does not exists [search, create, move, move subtree, restore to {original, different}, ]
* no permissions exists for action [all]
* no {read,write} permissions exists for target object [all]
* no {read,write} permissions exists for destination object [search, create, move, move subtree, restore to {original, different}, ]
* only partital write permissions exists [...]

Concurrency:
* yes
* no

Services:
* UDM CLI
* UDM REST API
* UMC


Connector Sync modes:
* read
* write
* sync
