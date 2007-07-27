# -*- perl -*-

package Mysql;

use 5.004;
use strict;

require Carp;
require DynaLoader;
require Exporter;
require DBI;
require Mysql::Statement;
require DBD::mysql;

use vars qw($QUIET @ISA @EXPORT @EXPORT_OK $VERSION $db_errstr);

$db_errstr = '';
$QUIET  = 0;
@ISA    = qw(DBI); # Inherits Exporter and DynaLoader via DBI
$VERSION = '1.2401';

# @EXPORT is a relict from old times...
@EXPORT = qw(
	     CHAR_TYPE
	     INT_TYPE
	     REAL_TYPE
	    );
@EXPORT_OK = qw(
		DATE_TYPE
		TIME_TYPE
	       );

my $FETCH_map = {
    'HOST' => '_host',
    'DATABASE' => 'database'
};

sub FETCH ($$) {
    my($self, $key) = @_;
    if ($key eq 'COMPATIBILITY') {
	return $self->{'COMPATIBILITY'};
    }
    if (exists($FETCH_map->{$key})) {
	$key = $FETCH_map->{$key};
    }
    my($dbh) = $self->{'dbh'};
    $dbh->{$key};
}

sub STORE ($$$) {
    my($self, $key, $val) = @_;
    if ($key eq 'COMPATIBILITY') {
	$self->{'COMPATIBILITY'} = $val;
    } else {
	$self->{'dbh'}->{$key} = $val;
    }
}

sub connect ($;$$$$) {
    my($class, $host, $db, $user, $password) = @_;
    my($self) = { 'host' => ($host || ''),
		  'user' => $user,
		  'password' => $password,
		  'db' => $db,
	          'driver' => 'mysql',
	          'COMPATIBILITY' => 1 };
    bless($self, $class);
    $self->{'drh'} = DBI->install_driver($self->{'driver'});
    if ($db) {
	my $dsn = "DBI:mysql:database=$db;host=$host";
	my $dbh = $class->SUPER::connect($dsn, $user, $password);
	if (!$dbh) {
	    $db_errstr = $DBI::errstr;
	    return undef;
	}
	$self->{'dbh'} = $dbh;
	$dbh->{'CompatMode'} = 1;
	$dbh->{'PrintError'} = !$Mysql::QUIET;
    }
    $self;
}

sub DESTROY {
    my $self = shift;
    my $dbh = $self->{'dbh'};
    if ($dbh) {
	local $SIG{'__WARN__'} = sub {};
	$dbh->disconnect();
    }
}

sub selectdb ($$) {
    my($self, $db) = @_;
    my $dsn = "DBI:mysql:database=$db:host=" . $self->{'host'};
    my $dbh = DBI->connect($dsn, $self->{'user'}, $self->{'password'});
    if (!$dbh) {
	$db_errstr = $self->{'errstr'} = $DBI::errstr;
	$self->{'errno'} = $DBI::err;
	undef;
    } else {
	if ($self->{'dbh'}) {
	    local $SIG{'__WARN__'} = sub {};
	    $self->{'dbh'}->disconnect();
	}
	$self->{'dbh'} = $dbh;
	$self->{'db'} = $db;
	$self;
    }
}

sub listdbs ($) {
    my($self) = shift;
    my $drh = $self->{'drh'};
    my $host = $self->{'host'};
    my @dbs;
    if ($host) {
	@dbs = $drh->func($host, "", $self->{'user'},
			  $self->{'password'}, "_ListDBs");
    } else {
	@dbs = $drh->func("", "", $self->{'user'},
			  $self->{'password'}, "_ListDBs");
    }
    $db_errstr = $drh->errstr();
    @dbs;
}

sub listtables ($) {
    my($self) = shift;
    map { $_ =~ s/^(.*)\.//; $_ } $self->{'dbh'}->tables();
}

sub quote ($$) {
    my($self) = shift;
    my $obj = (ref($self) && $self->{'dbh'}) ?
	$self->{'dbh'} : 'DBD::mysql::db';
    $obj->quote(shift);
}

sub errmsg ($) {
    my $self = shift;
    if (!ref($self)) {
	$DBI::errstr || $db_errstr;
    } elsif ($self->{'dbh'}) {
	$self->{'dbh'}->errstr();
    } else {
	$self->{'drh'}->errstr();
    }
}

sub errno ($) {
    my $self = shift;
    if (!ref($self)) {
	$DBI::err;
    } elsif ($self->{'dbh'}) {
	$self->{'dbh'}->err();
    } else {
	$self->{'drh'}->err();
    }
}

sub listfields ($$) {
    my($self, $table) = @_;
    $self->query("LISTFIELDS $table");
}

sub query ($$) {
    my($self, $statement) = @_;
    my $dbh = $self->{'dbh'};
    my $sth = $dbh->prepare($statement);
    if (!$sth) {
	$db_errstr = $dbh->errstr();
	return undef;
    }
    $sth->{'PrintError'} = !$Mysql::QUIET;
    my $result = $sth->execute();
    if (!$result) {
	$db_errstr = $sth->errstr();
	return undef;
    }
    $sth->{'CompatMode'} = 1;
    bless($sth, ref($self) . "::Statement");
    undef $db_errstr;
    $sth;
}

sub shutdown ($) {
    my($self) = shift;
    if ($self->{'dbh'}) {
	$self->{'dbh'}->admin('shutdown', 'admin');
    } else {
	$self->{'drh'}->func('shutdown', $self->{'host'}, $self->{'user'},
			     $self->{'password'}, 'admin');
    }
}

sub createdb ($$) {
    my($self, $db) = @_;
    if ($self->{'dbh'}) {
	$self->{'dbh'}->admin('createdb', $db, 'admin');
    } else {
	$self->{'drh'}->func('createdb', $db, $self->{'host'},
			     $self->{'user'}, $self->{'password'}, 'admin');
    }
}

sub dropdb ($$) {
    my($self, $db) = @_;
    if ($self->{'dbh'}) {
	$self->{'dbh'}->admin('dropdb', $db, 'admin');
    } else {
	$self->{'drh'}->func('dropdb', $db, $self->{'host'},
			     $self->{'user'}, $self->{'password'}, 'admin');
    }
}

sub host     ($) { shift->{'host'} }
sub database ($) { shift->{'db'} }
sub info ($) { shift->{'dbh'}->{'info'} }
sub sock ($) { shift->{'dbh'}->{'sock'} }
sub sockfd ($) { shift->{'dbh'}->{'sockfd'} }


sub AUTOLOAD {
    my $meth = $Mysql::AUTOLOAD;
    my $converted = 0;

    my $class;
    if ($meth =~ /(.*)::(.*)/) {
	$meth = $2;
	$class = $1;
    } else {
	$class = "main";
    }


    TRY: {
	my $val = DBD::mysql::constant($meth, @_ ? $_[0] : 0);
	if ($! == 0) {
	    eval "sub $Mysql::AUTOLOAD { $val }";
	    return $val;
	}

	if (!$converted) {
	    $meth =~ s/_//g;
	    $meth = lc($meth);
	    $converted = 1;
	}

	if (defined &$meth) {
	    no strict 'refs';
	    *$meth = \&{$meth};
	    return &$meth(@_);
	} elsif ($meth =~ s/(.*)type$/uc($1)."_TYPE"/e) {
	    # Try to determine the type that was requested by
	    # translating inttype to INT_TYPE Not that I consider it
	    # good style to write inttype, but we once allowed it,
	    # so...
	    redo TRY;
	}
    }

  Carp::croak("$Mysql::AUTOLOAD: Not defined in $class and not"
	      . " autoloadable (last try $meth)");
}


sub gethostinfo ($) { shift->{'dbh'}->{'hostinfo'} }
sub getprotoinfo ($) { shift->{'dbh'}->{'protoinfo'} }
sub getserverinfo ($) { shift->{'dbh'}->{'serverinfo'} }
sub getserverstats ($) { shift->{'dbh'}->{'stats'} }


Mysql->init_rootclass();

sub CHAR_TYPE { DBD::mysql::FIELD_TYPE_STRING() }
sub INT_TYPE { DBD::mysql::FIELD_TYPE_LONG() }
sub REAL_TYPE { DBD::mysql::FIELD_TYPE_DOUBLE() }
sub DATE_TYPE { DBD::mysql::FIELD_TYPE_DATE() }
sub TIME_TYPE { DBD::mysql::FIELD_TYPE_TIME() }


package Mysql::dr;
@Mysql::dr::ISA = qw(DBI::dr);

package Mysql::db;
@Mysql::db::ISA = qw(DBI::db);

package Mysql::st;
@Mysql::st::ISA = qw(Mysql::Statement);

1;
__END__

=head1 NAME

Msql / Mysql - Perl interfaces to the mSQL and mysql databases

=head1 SYNOPSIS

  use Msql;

  $dbh = Msql->connect($host);
  $dbh = Msql->connect($host, $database);

      or

  use Mysql;

  $dbh = Mysql->connect(undef, $database, $user, $password);
  $dbh = Mysql->connect($host, $database, $user, $password);

      or

  $dbh = Msql1->connect($host);
  $dbh = Msql1->connect($host, $database);


  $dbh->selectdb($database);
	
  @arr = $dbh->listdbs;
  @arr = $dbh->listtables;
	
  $quoted_string = $dbh->quote($unquoted_string);
  $error_message = $dbh->errmsg;
  $error_number = $dbh->errno;   # MySQL only

  $sth = $dbh->listfields($table);
  $sth = $dbh->query($sql_statement);
	
  @arr = $sth->fetchrow;	# Array context
  $firstcol = $sth->fetchrow;	# Scalar context
  @arr = $sth->fetchcol($col_number);
  %hash = $sth->fetchhash;
	
  $sth->dataseek($row_number);

  $sth->as_string;

  @indices = $sth->listindices                   # only in mSQL 2.0
  @arr = $dbh->listindex($table,$index)          # only in mSQL 2.0
  ($step,$value) = $dbh->getsequenceinfo($table) # only in mSQL 2.0

  $rc = $dbh->shutdown();
  $rc = $dbh->createdb($database);
  $rc = $dbh->dropdb($database);

=head1 OBSOLETE SOFTWARE

As of Msql-Mysql-modules 1.19_10 M(y)sqlPerl is no longer a separate module.
Instead it is emulated using the DBI drivers. You are strongly encouraged
to implement new code with DBI directly. See L<COMPATIBILITY NOTES>
below.

=head1 DESCRIPTION

This package is designed as close as possible to its C API
counterpart. The manual that comes with mSQL or MySQL describes most things
you need. Due to popular demand it was decided though, that this interface
does not use StudlyCaps (see below).

As of March 1998, the Msql and Mysql modules are obsoleted by the
DBI drivers DBD::mSQL and DBD::mysql, respectively. You are strongly
encouraged to implement new code with the DBI drivers. In fact,
Msql and Mysql are currently implemented as emulations on top of
the DBI drivers.

Internally you are dealing with the two classes C<Msql> and
C<Msql::Statement> or C<Mysql> and C<Mysql::Statement>, respectively.
You will never see the latter, because you reach
it through a statement handle returned by a query or a listfields
statement. The only class you name explicitly is Msql or Mysql. They
offer you the connect command:

  $dbh = Msql->connect($host);
  $dbh = Msql->connect($host, $database);

    or

  $dbh = Mysql->connect($host, undef, $user, $password);
  $dbh = Mysql->connect($host, $database, $user, $password);

    or

  $dbh = Msql1->connect($host);
  $dbh = Msql1->connect($host, $database);


This connects you with the desired host/database. With no argument or
with an empty string as the first argument it connects to the UNIX
socket, which has a much better performance than
the TCP counterpart. A database name as the second argument selects
the chosen database within the connection. The return value is a
database handle if the connect succeeds, otherwise the return value is
undef.

You will need this handle to gain further access to the database.

   $dbh->selectdb($database);

If you have not chosen a database with the C<connect> command, or if
you want to change the connection to a different database using a
database handle you have got from a previous C<connect>, then use
selectdb.

  $sth = $dbh->listfields($table);
  $sth = $dbh->query($sql_statement);

These two work rather similar as descibed in the mSQL or MySQL manual. They
return a statement handle which lets you further explore what the
server has to tell you. On error the return value is undef. The object
returned by listfields will not know about the size of the table, so a
numrows() on it will return the string "N/A";

  @arr = $dbh->listdbs();
  @arr = $dbh->listtables;

An array is returned that contains the requested names without any
further information.

  @arr = $sth->fetchrow;

returns an array of the values of the next row fetched from the
server. Be carefull with context here! In scalar context the method
behaves different than expected and returns the first column:

  $firstcol = $sth->fetchrow; # Scalar context!

Similar does

  %hash = $sth->fetchhash;

return a complete hash. The keys in this hash are the column names of
the table, the values are the table values. Be aware, that when you
have a table with two identical column names, you will not be able to
use this method without trashing one column. In such a case, you
should use the fetchrow method.

  @arr = $sth->fetchcol($colnum);

returns an array of the values of each row for column $colnum.  Note that
this reads the entire table and leaves the row offset at the end of the
table; be sure to use $sth->dataseek() to reset it if you want to
re-examine the table.

  $sth->dataseek($row_number);

lets you specify a certain offset of the data associated with the
statement handle. The next fetchrow will then return the appropriate
row (first row being 0).

=head2 No close statement

Whenever the scalar that holds a database or statement handle loses
its value, Msql chooses the appropriate action (frees the result or
closes the database connection). So if you want to free the result or
close the connection, choose to do one of the following:

=over 4

=item undef the handle

=item use the handle for another purpose

=item let the handle run out of scope

=item exit the program.

=back

=head2 Error messages

Both drivers, Msql and Mysql implement a method -E<gt>errmsg(), which
returns a textual error message. Mysql additionally supports a method
-E<gt>errno returning the corresponding error number.

Usually you do fetch error messages with

    $errmsg = $dbh->errmsg();

In situations where a $dbh is not available (for example when
connect() failed) you may instead do a

    $errmsg = Msql->errmsg();
        or
    $errmsg = Mysql->errmsg();
        or
    $errmsg = Msql1->errmsg();


=head2 The C<-w> switch

With Msql and Mysql the C<-w> switch is your friend! If you call your perl
program with the C<-w> switch you get the warnings from -E<gt>errmsg on
STDERR. This is a handy method to get the error messages from the msql
server without coding it into your program.

If you want to know in greater detail what's going on, set the
environment variables that are described in David's manual. David's
debugging aid is excellent, there's nothing to be added.

By default errors are printed as warnings. You can suppress this
behaviour by using the PrintError attribute of the respective handles:

    $dbh->{'dbh'}->{'PrintError'} = 0;


=head2 -E<gt>quote($str [, $length])

returns the argument enclosed in single ticks ('') with any special
character escaped according to the needs of the API.

For mSQL this means, any single tick within the string is escaped with
a backslash and backslashes are doubled. Currently (as of msql-1.0.16)
the API does not allow to insert NUL's (ASCII 0) into tables. The quote
method does not fix this deficiency.

MySQL allows NUL's or any other kind of binary data in strings. Thus
the quote method will additionally escape NUL's as \0.

If you pass undefined values to the quote method, it returns the
string C<NULL>.

If a second parameter is passed to C<quote>, the result is truncated
to that many characters.

=head2 NULL fields

NULL fields in tables are returned to perl as undefined values.

=head2 Metadata

Now lets reconsider the above methods with regard to metadata.

=head2 Database Handle

As said above you get a database handle with the connect() method.
The database handle knows about the socket, the host, and the database
it is connected to.

You get at the three values with the methods

  $scalar = $dbh->sock;
  $scalar = $dbh->host;
  $scalar = $dbh->database;

Mysql additionally supports

  $scalar = $dbh->user;
  $scalar = $dbh->sockfd;

where the latter is the file descriptor of the socket used by the
database connection. This is the same as $dbh->sock for mSQL.

=head2 Statement Handle

Two constructor methods return a statement handle:

  $sth = $dbh->listfields($table);
  $sth = $dbh->query($sql_statement);

$sth knows about all metadata that are provided by the API:

  $scalar = $sth->numrows;    
  $scalar = $sth->numfields;  

  @arr  = $sth->table;       the names of the tables of each column
  @arr  = $sth->name;        the names of the columns
  @arr  = $sth->type;        the type of each column, defined in msql.h
	                     and accessible via Msql::CHAR_TYPE,
	                     &Msql::INT_TYPE, &Msql::REAL_TYPE or
                             &Mysql::FIELD_TYPE_STRING,
                             &Mysql::FIELD_TYPE_LONG, ...
  @arr  = $sth->isnotnull;   array of boolean
  @arr  = $sth->isprikey;    array of boolean
  @arr  = $sth->isnum;       array of boolean
  @arr  = $sth->length;      array of the possibble maximum length of each
                             field in bytes
  @arr  = $sth->maxlength;   array of the actual maximum length of each field
                             in bytes. Be careful when using this attribute
                             under MsqlPerl: The server doesn't offer this
                             attribute, thus it is calculated by fetching
                             all rows. This might take a long time and you
                             might need to call $sth->dataseek.

Mysql additionally supports

  $scalar  = $sth->affectedrows  number of rows in database affected by query
  $scalar  = $sth->insertid      the unique id given to a auto_increment field.
  $string  = $sth->info()        more info from some queries (ALTER TABLE...)
  $arrref  = $sth->isblob;       array of boolean

The array methods (table, name, type, is_not_null, is_pri_key, length,
affected_rows, is_num and blob) return an array in array context and
an array reference (see L<perlref> and L<perlldsc> for details) when
called in a scalar context. The scalar context is useful, if you need
only the name of one column, e.g.

    $name_of_third_column = $sth->name->[2]

which is equivalent to

    @all_column_names = $sth->name;
    $name_of_third_column = $all_column_names[2];

=head2 New in mSQL 2.0

The query() function in the API returns the number of rows affected by
a query. To cite the mSQL API manual, this means...

  If the return code is greater than 0, not only does it imply
  success, it also indicates the number of rows "touched" by the query
  (i.e. the number of rows returned by a SELECT, the number of rows
  modified by an update, or the number of rows removed by a delete).

As we are returning a statement handle on selects, we can easily check
the number of rows returned. For non-selects we behave just the same
as mSQL-2.

To find all indices associated with a table you can call the
C<listindices()> method on a statement handle. To find out the columns
included in an index, you can call the C<listindex($table,$index)>
method on a database handle.

There are a few new column types in mSQL 2. You can access their
numeric value with these functions defined in the Msql package:
IDENT_TYPE, NULL_TYPE, TEXT_TYPE, DATE_TYPE, UINT_TYPE, MONEY_TYPE,
TIME_TYPE, IDX_TYPE, SYSVAR_TYPE.

You cannot talk to a 1.0 server with a 2.0 client.

You cannot link to a 1.0 library I<and> to a 2.0 library I<at the same
time>. So you may want to build two different Msql modules at a time,
one for 1.0, another for 2.0, and load whichever you need. Check out
what the C<-I> switch in perl is for.

Everything else seems to remain backwards compatible.

=head2 @EXPORT

For historical reasons the constants CHAR_TYPE, INT_TYPE, and
REAL_TYPE are in @EXPORT instead of @EXPORT_OK. This means, that you
always have them imported into your namespace. I consider it a bug,
but not such a serious one, that I intend to break old programs by
moving them into EXPORT_OK.

=head2 Displaying whole tables in one go

A handy method to show the complete contents of a statement handle is
the as_string method. This works similar to the msql monitor with a
few exceptions:

=over 2

=item the width of a column

is calculated by examining the width of all entries in that column

=item control characters

are mapped into their backslashed octal representation

=item backslashes

are doubled (C<\\ instead of \>)

=item numeric values

are adjusted right (both integer and floating point values)

=back

The differences are illustrated by the following table:

Input to msql (a real carriage return here replaced with ^M):

    CREATE TABLE demo (
      first_field CHAR(10),
      second_field INT
    ) \g

    INSERT INTO demo VALUES ('new
    line',2)\g
    INSERT INTO demo VALUES ('back\\slash',1)\g
    INSERT INTO demo VALUES ('cr^Mcrnl
    nl',3)\g

Output of msql:

     +-------------+--------------+
     | first_field | second_field |
     +-------------+--------------+
     | new
    line    | 2            |
     | back\slash  | 1            |
    crnlr
    nl  | 3            |
     +-------------+--------------+

Output of pmsql:

    +----------------+------------+
    |first_field     |second_field|
    +----------------+------------+
    |new\012line     |           2|
    |back\\slash     |           1|
    |cr\015crnl\012nl|           3|
    +----------------+------------+


=head2 Version information

The version of Msql and Mysql is always stored in $Msql::VERSION or
$Mysql::VERSION as it is perl standard.

The mSQL API implements methods to access some internal configuration
parameters: gethostinfo, getserverinfo, and getprotoinfo.  All three
are available both as class methods or via a database handle. But
under no circumstances they are associated with a database handle. All
three return global variables that reflect the B<last> connect()
command within the current program. This means, that all three return
empty strings or zero I<before> the first call to connect().

This situation is better with MySQL: The methods are valid only
in connection with a database handle.

=head2 Administration

shutdown, createdb, dropdb, reloadacls are all accessible via a
database handle and implement the corresponding methods to what
msqladmin does.

The mSQL and MySQL engines do not permit that these commands are invoked by
users without sufficient privileges. So please make sure
to check the return and error code when you issue one of them.

    $rc = $dbh->shutdown();
    $rc = $dbh->createdb($database);
    $rc = $dbh->dropdb($database);

It should be noted that database deletion is I<not prompted for> in
any way. Nor is it undo-able from within Perl.

    B<Once you issue the dropdb() method, the database will be gone!>

These methods should be used at your own risk.


=head2 StudlyCaps

Real Perl Programmers (C) usually don't like to type I<ListTables> but
prefer I<list_tables> or I<listtables>. The mSQL API uses StudlyCaps
everywhere and so did early versions of MsqlPerl. Beginning with
$VERSION 1.06 all methods are internally in lowercase, but may be
written however you please. Case is ignored and you may use the
underline to improve readability.

The price for using different method names is neglectible. Any method
name you use that can be transformed into a known one, will only be
defined once within a program and will remain an alias until the
program terminates. So feel free to run fetch_row or connecT or
ListDBs as in your old programs. These, of course, will continue to
work.

=head1 PREREQUISITES

mSQL is a database server and an API library written by David
Hughes. To use the adaptor you definitely have to install these first.

MySQL is a libmysqlclient.a library written by Michael Widenius
This was originally inspired by MySQL.


=head1 COMPATIBILITY NOTES

M(y)sql used to be a separate module written in C. This is no longer
the case, instead the old modules are emulated by their corresponding
DBI drivers. I did my best to remove any incompatibilities, but the
following problems are known to remain:

=over 4

=item Static methods

For whatever reason, mSQL implements some functions independent from
the respective database connection that really depend on it. This
made it possible to implement

    Msql->errmsg

or

    Msql->getserverinfo

as static methods. This is no longer the case, it never was for
MysqlPerl. Instead you have to use

    $dbh->errmsg

or

    $dbh->getserverinfo

=item $M(Y)SQL::QUIET

This variable used to turn off the printing of error messages. Unfortunately
DBI uses a completely different mechanism for that: The C<PrintError>
attribute of the database and/or statement handles. We try to emulate
the old behaviour by setting the C<PrintError> attribute to the current
value of $M(Y)SQL::QUIET when a handle is created, that is when
M(y)sql->connect or $dbh->query() are called.

You can overwrite this by using something like

    $dbh->{'dbh'}->{'PrintError'} = 1;

or

    $sth->{'PrintError'} = 0;

=back


=head1 AUTHORS

Andreas Koenig C<koenig@franz.ww.TU-Berlin.DE> wrote the original
MsqlPerl. Jochen Wiedmann wrote the M(y)sqlPerl emulation using DBI.


=head1 SEE ALSO

Alligator Descartes wrote a database driver for Tim Bunce's DBI. I
recommend anybody to carefully watch the development of this module
(C<DBD::mSQL>). Msql is a simple, stable, and fast module, and it will
be supported for a long time. But it's a dead end. I expect in the
medium term, that the DBI efforts result in a richer module family
with better support and more functionality. Alligator maintains an
interesting page on the DBI development:

    http://www.symbolstone.org/technology/perl/DBI

=cut
