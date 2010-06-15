#!/usr/bin/perl

use GDBM_File;
tie(my %STORE, 'GDBM_File', "/var/www/freebusy/cache/pfbcache.db",
&GDBM_WRCREAT, 0644) || die "Cannot create GDBM
file /var/www/freebusy/cache/pfbcache.db";
untie(%STORE);

