# Files

## [base64.c](base64.c)
Base64 encoding and decoding methods.

## [cache.c](cache.c)
LDAP entries are cached here.
If a modification takes place, the new LDAP entry is compared with the cache entry, and both, old and new entries, are passed to the handler modules.
This is the version using LMDB.

## [cache_lowlevel.c](cache_lowlevel.c)
The low-level function to serialize the C structures as used in memory into a binary representation `unparse_entry()` for the database and back `parse_entry()`.

## [change.c](change.c)
The name change might be misleading.
This is more of an abstraction layer to run handlers (and do a few more tweaks such as updating the schema beforehand).
Functions generally take LDAP entries or DNs as input.

## [filter.c](filter.c)
Functions to match LDAP filters to cache entries.
Currently, we don't use any schema information.
However, to do this properly, we'd need to.

## [handlers.c](handlers.c)
The Python handlers (and possibly, C and Shell handlers in the future) are initialized and run here.

## [network.c](network.c)
An asynchronous notifier client API.

## [notifier.c](notifier.c)
The name notifier might be misleading.
The main function `notifier_listener()` uses the listener network API ([network.c](network.c)) to receive updates from a notifier and calls the `change()` functions.

## [signals.c](signals.c)
Signal handlers are initialized and defined here.

## [dump_signals.c](dump_signals.c)
Dummy signal handlers for command line tools.

## [utils.c](utils.c)
Some low-level functions like working with UTF-8 strings.

## [transfile.c](transfile.c)
Functions to write a transaction log for cascading listeners.

## [main.c](main.c)
The listener daemon.

## [demo.c](demo.c)
Demo program for the notifier client API.

## [dump.c](dump.c)
Tool to dump the cache.


# Cache
Stores LDAP attributes and values of replicated objects to provide them
as *old* when *handler(dn, new, old)* is called the next time for the same dn.

## On disk representation
On disk the entries are stored in a key-value-database.
The *distiguished name* (DN) is used as the look-up key.
Actually this is a bug, as the DN is not normalized based on the LDAP schema, but always converted to lower-case.

Each entry is stored as a sequence of `(struct cache_entry_header, key, value)` records:
```c
struct cache_entry_header {
	u_int16_t type;
	u_int32_t key_size;
	u_int32_t data_size;
};
```

* `type`
  `1` encodes an attribute, while `2` encodes a module name.

* `key_size`
  The number of bytes directly following after the header belonging to the key.
  For attributes, the `key` is the attribute name.
  For modules, the `key` is the module name.

* `data_size`
  The number of bytes following after the key belonging to the value.
  For attributes, the `value` is a attribute value.
  For modules, the length is always `0` to encode `NULL`.

The number of entries is not stored explicitly.
The buffer returned as the database-value must be parsed completely to its end.


## In memory representation
In memory entries are represented as
```c
struct _CacheEntry {
	CacheEntryAttribute **attributes;
	int attribute_count;
	char **modules;
	int module_count;
} typedef CacheEntry;
```

* `attributes`
  Array of `attribute_count` pointers to `struct _CacheEntryAttribute`.

* `attribute_count`
  Number of entries in `attributes`.

* `modules`
  Array of `module_count` pointers to C-strings naming the modules, which handle the entry.
  This is mostly used for `handle()` to be called on delete.

* `module_count`
  Number of entries in `modules`.

Attributes are represented as
```c
struct _CacheEntryAttribute {
	char *name;
	char **values;
	int *length;
	int value_count;
} typedef CacheEntryAttribute;
```

* `name`
  The name of the attribute.

* `values`
  Array of `value_count` pointers to buffers, whose corresponding length is stored in `length`.

* `length`
  Array of `value_count` integers, which specify the corresponding buffer length of `values`.

* `value_count`
  Number of entries in `values` and `length`.

[cache_entry.c](cache_entry.c) implements several functions to modify and manage those structures.

## Berkeley Database (BDB)
Used until UCS-4.1-x.
Is is a simple key-value-store, which is used to map the DN to the sequence of records.
The *distiguished name* (DN) is used as the look-up key.

## Lightning Memory-Mapped Database ([LMDB](https://symas.com/lmdb/))
Used since UCS-4.2-0.
It uses multiple sorted key-value-stored to map the DN to the sequence of records.
The database contains 3 sub-tables to store the tree hierarchically:

	mdb_stat -a /var/lib/univention-directory-listener/cache/

### Main DB
used internally by LMDB only.

### id2dn
Each LDAP/cache-DN entry is mapped to a unique ID which is stored in this sub-database.
This is necessary because LMDB limits the key size to 511 bytes by default.
The mapping structure is organized like a tree of RDNs, which improves lookup performance compared to a plain list of DNs.
The actual cache data for the entry itself is stored in the [id2entry](#id2entry) sub-database.

The `id2dn` sub-database is used to store the tree with it nodes and edges between them.
Each node gets a unique ID, for which the database contains *multiple* entries of the following structure:

```c
struct subDN {
	unsigned long id;
	enum { NODE=0, LINK=1 } type;
	char data[0];
};
```

#### NODE
A node is represented as `type=NODE`.
For any *non-root-node* it includes reference to its parent node as `id`.
`data` contains the full DN.

#### LINK
For any *non-leaf-node* a value with `type=LINK` will reference the direct child node `id`.
`data` contains the relative DN of the child.

`key=0` is the root of the LDAP tree, e.g. ''.

	mdb_dump -p /var/lib/univention-directory-listener/cache/ -s id2dn

A DN lookup starts with the right-most (base) RDN:

1.	The search starts at the root with `key=0`.

2.	For the base RDN a key-value-pair mapping `key=0` to `value=(id, LINK, rdn)` exists, which is returned due to the clever use of `mdb_dupsort()`:
	It allows the *same key* to match to *multiple values* and will return the best match, where `type=LINK` and `rdn` matches the searched RDN.

3.	The returned `id` matches the next level of the tree.

4.	There the search continues with the next RDN.

### id2entry
Each LDAP/cache-DN entry has a unique ID.
The ID is allocated on insert of a new DN into [id2dn](#id2dn).
The key is that ID and the value is the data - in our case the serialized cache entry.

`id=0` is the `CacheMasterEntry` entry, which is used to store the Notifier- and Schema-ID of the listener.

	mdb_dump -p /var/lib/univention-directory-listener/cache/ -s id2entry

# Dependencies

*	[main.c](main.c)
	*	[signals.c](signals.c)
	*	[notifier.c](notifier.c)
		*	[network.c](network.c)
		*	[change.c](change.c)
			*	[cache.c](cache.c)
				*	[cache_lowlevel.c](cache_lowlevel.c)
				*	[cache_entry.c](cache_entry.c)
			*	[handlers.c](handlers.c)
				*	[filter.c](filter.c)
				*	[cache_entry.c](cache_entry.c)
		*	[transfile.c](transfile.c)

*	[dump.c](dump.c)
	*	[cache.c](cache.c)
		*	[cache_lowlevel.c](cache_lowlevel.c)
		*	[cache_entry.c](cache_entry.c)
	*	[base64.c](base64.c)
	*	[dump_signals.c](dump_signals.c)

*	[demo.c](demo.c)
	*	[network.c](network.c)

*	[verify.c](verify.c)
	*	[cache.c](cache.c)
		*	[cache_lowlevel.c](cache_lowlevel.c)
		*	[cache_entry.c](cache_entry.c)
	*	[dump_signals.c](dump_signals.c)
