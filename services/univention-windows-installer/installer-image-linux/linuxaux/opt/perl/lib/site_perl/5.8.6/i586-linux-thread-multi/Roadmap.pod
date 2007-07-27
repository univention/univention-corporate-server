=head1 NAME

DBI::Roadmap - Planned Enhancements for the DBI

Tim Bunce - 12th November 2004

=head1 SYNOPSIS

This document gives a high level overview of the future of the Perl
DBI module.

The DBI module is the standard database interface for Perl applications.
It is used worldwide in countless applications, in every kind of
business, and on platforms from clustered super-computers to PDAs.
Database interface drivers are available for all common databases
and many not-so-common ones.

The planned enhancements cover testing, performance, high availability
and load balancing, batch statements, Unicode, database portability,
and more.

Addressing these issues together, in coordinated way, will help
ensure maximum future functionality with minimal disruptive
(incompatible) upgrades.

=head1 SCOPE

Broad categories of changes are outlined here along with some
rationale, but implementation details and minor planned enhancements
are omitted.  More details can be found in:
L<http://svn.perl.org/modules/dbi/trunk/ToDo>


=head1 CHANGES AND ENHANCEMENTS

These are grouped into categories and are not listed in any particular order.

=head2 Performance

The DBI has always treated performance as a priority. Some parts
of the implementation, however, remain unoptimized, especially in
relation to threads.

* When the DBI is used with a Perl built with thread support enabled
(such as for Apache mod_perl 2, and some common Linux distributions)
it runs significantly slower. There are two reasons for this and
both can be fixed but require non-trivial changes to both the DBI
and drivers.

* Connection pooling in a threaded application, such as mod_perl,
is difficult because DBI handles cannot be passed between threads.
An alternative mechanism for passing connections between threads
has been defined, and an experimental connection pool module
implemented using it, but development has stalled.

* The majority of DBI handle creation code is implemented in Perl.
Moving most of this to C will speed up handle creation significantly.

* The popular fetchrow_hashref() method is many times slower than
fetchrow_arrayref(). It has to get the names of the columns, then
create and load a new hash each time. A $h->{FetchHashReuse} attribute
would allow the same hash to be reused each time making fetchrow_hashref()
about the same speed as fetchrow_arrayref().

* Support for asynchronous (non-blocking) DBI method calls would
enable applications to continue processing in parallel with database
activity.  This is also relevant for GUI and other event-driven
applications.  The DBI needs to define a standard interface for
this so drivers can implement it in a portable way, where possible.

These changes would significantly enhance the performance of the
DBI and many applications which use the DBI.


=head2 Testing

The DBI has a test suite. Every driver has a test suite.  Each is
limited in its scope.  The driver test suite is testing for behavior
that the driver author I<thinks> the DBI specifies, but may be
subtly incorrect.  These test suites are poorly maintained because
the return on investment for a single driver is too low to provide
sufficient incentive.

A common test suite that can be reused by all the drivers is needed.
It would:

* Improve the quality of the DBI and drivers.

* Ensure all drivers conform to the DBI specification.  Easing the
porting of applications between databases, and the implementation
of database independent modules layered over the DBI.

* Improve the DBI specification by clarifying unclear issues in
order to implement test cases.

* Encourage expansion of the test suite as driver authors and others
will be motivated by the greater benefits of their contributions.

* Detect and record optional functionality that a driver has not
yet implemented.

* Improve the testing of DBI subclassing, DBI::PurePerl and the
various "transparent" drivers, such as DBD::Proxy and DBD::Multiplex,
by automatically running the test suite through them.

These changes would improve the quality of all applications using
the DBI.


=head2 High Availability and Load Balancing

* The DBD::Multiplex driver provides a framework to enable a wide
range of dynamic functionality, including support for high-availability,
failover, load-balancing, caching, and access to distributed data.
It is currently being enhanced but development has stalled.

* The DBD::Proxy module is complex and relatively inefficient because
it's trying to be a complete proxy for most DBI method calls.  For
many applications a simpler proxy architecture that operates with
a single round-trip to the server would be simpler, faster, and more
flexible.

New proxy client and server classes are needed, which could be
subclassed to support specific client to server transport mechanisms
(such as HTTP and Spread::Queue).  Apart from the efficiency gains,
this would also enable the use of a load-balanced pool of stateless
servers for greater scalability and reliability.

* The DBI currently offers no support for distributed transactions.
The most useful elements of the standard XA distributed transaction
interface standard could be included in the DBI specification.
Drivers for databases which support distributed transactions could
then be extended to support it.

These changes would enable new kinds of DBI applications for critical
environments.


=head2 Unicode

Use of Unicode with the DBI is growing rapidly. The DBI should do
more to help drivers support Unicode and help applications work
with drivers that don't yet support Unicode directly.

* Define expected behavior for fetching data and binding parameters.

* Provide interfaces to support Unicode issues for XS and pure Perl
drivers and applications.

* Provide functions for applications to help diagnose inconsistencies
between byte string contents and setting of the SvUTF8 flag.

These changes would smooth the transition to Unicode for many
applications and drivers.


=head2 Batch Statements

Batch statements are a sequence of SQL statements, or a stored
procedure containing a sequence of SQL statements, which can be
executed as a whole.

Currently the DBI has no standard interface for dealing with multiple
results from batch statements.  After considerable discussion, an
interface design has been agreed upon with driver authors, but has
not yet been implemented.

These changes would enable greater application portability between
databases, and greater performance for databases that directly
support batch statements.


=head2 Introspection

* The methods of the DBI API are installed dynamically when the DBI
is loaded.  The data structure used to define the methods and their
dispatch behavior should be made part of the DBI API. This would
enable more flexible and correct behavior by modules subclassing
the DBI and by dynamic drivers such as DBD::Proxy and DBD::Multiplex.

* Handle attribute information should also be made available, for
the same reasons.

* Currently is it not possible to discover all the child statement
handles that belong to a database handle (or all database handles
that belong to a driver handle).  This makes certain tasks more
difficult, especially some debugging scenarios.  A cache of weak
references to child handles would solve the problem without creating
reference loops.

* It is often useful to know which handle attributes have been
changed since the handle was created (e.g., in mod_perl where a
handle needs to be reset or cloned). This will become more important
as developers start exploring use of the newly added
$h1->swap_inner_handle($h2) method.

These changes would simplify and improve the stability of many
advanced uses of the DBI.


=head2 Extensibility

The DBI can be extended in three main dimensions: subclassing the
DBI, subclassing a driver, and callback hooks. Each has different
pros and cons, each is applicable in different situations, and
all need enhancing.

* Subclassing the DBI is functional but not well defined and some
key elements are incomplete, particularly the DbTypeSubclass mechanism
(that automatically subclasses to a class tree according to the
type of database being used).  It also needs more thorough testing.

* Subclassing a driver is undocumented, poorly tested and very
probably incomplete. However it's a powerful way to embed certain
kinds of functionality 'below' applications while avoiding some of
the side-effects of subclassing the DBI (especially in relation to
error handling).

* Callbacks are currently limited to error handling (the HandleError
and HandleSetError attributes).  Providing callback hooks for more
events, such as a row being fetched, would enable utility modules,
for example, to modify the behavior of a handle independent of any
subclassing in use.

These changes would enable cleaner and more powerful integration
between applications, layered modules, and the DBI.


=head2 Debugability

* Enabling DBI trace output at a high level of detail causes a large
volume of output, much of it probably unrelated to the problem being
investigated. Trace output should be controlled by the new named-topic
mechanism instead of just the trace level.

* Calls to XS functions (such as many DBI and driver methods) don't
normally appear in the call stack.  Optionally enabling that would
enable more useful diagnostics to be produced.

* Integration with the Perl debugger would make it simpler to perform
actions on a per-handle basis (such as breakpoint on execute,
breakpoint on error).

These changes would enable more rapid application development and
fault finding.


=head2 Database Portability

* The DBI has not yet addressed the issue of portability among SQL
dialects.  This is the main hurdle limiting database portability
for DBI applications.

The goal is I<not> to fully parse the SQL and rewrite it in a
different dialect.  That's well beyond the scope of the DBI and
should be left to layered modules.  A simple token rewriting mechanism
for five comment styles, two quoting styles, four placeholder styles,
plus the ODBC "{foo ...}" escape syntax, is sufficient to significantly
raise the level of SQL portability.

* Another problem area is date/time formatting.  Since version 1.41
the DBI has defined a way to express that dates should be fetched
in SQL standard date format (YYYY-MM-DD).  This is one example of
the more general case where bind_col() needs to be called with
particular attributes on all columns of a particular type.

A mechanism is needed whereby an application can specify default
bind_col() attributes to be applied automatically for each column
type. With a single step, all DATE type columns, for example, can
be set to be returned in the standard format.

These changes would enable greater database portability for
applications and greater functionality for layered modules.


=head2 Intellectual Property

* Clarify current intellectual property status, including a review
  of past contributions to ensure the DBI is unemcumbered.

* Establish a procedure for vetting future contributions for any
  intellectual property issues.

These changes are important for companies taking a formal approach
to assessing their risks in using Open Source software.


=head2 Other Enhancements

* Reduce the work needed to create new database interface drivers.

* Definition of an interface to support scrollable cursors.


=head2 Parrot and Perl 6

The current DBI implementation in C code is unlikely to run on Perl 6.
Perl 6 will target the Parrot virtual machine and so the internal
architecture will be radically different from Perl 5.

One of the goals of the Parrot project is to be a platform for many
dynamic languages (including Python, PHP, Ruby, etc) and to enable
those languages to reuse each others modules. A database interface
for Parrot is also a database interface for any and all languages
that run on Parrot.

The Perl DBI would make an excellent base for a Parrot database
interface because it has more functionality, and is more mature and
extensible, than the database interfaces of the other dynamic
languages.

I plan to better define the API between the DBI and the drivers and
use that API as the primary API for the 'raw' Parrot database
interface.  This project is known a Parrot DBDI (for "DataBase
Driver Interface").  The announcement can be read in
<http://groups.google.com/groups?selm=20040127225639.GF38394@dansat.data-plan.com>

The bulk of the work will be translating the DBI C and Perl base
class code into Parrot PIR, or a suitable language that generates
PIR.  The project stalled, due to Parrot not having key functionality
at the time.  That has been resolved but the project has not yet
restarted.

Each language targeting Parrot would implement their own small
'thin' language-specific method dispatcher (a "Perl6 DBI", "Python
DBI", "PHP DBI" etc) layered over the common Parrot DBDI interface
and drivers.

The major benefit of the DBDI project is that a much wider community
of developers share the same database drivers. There would be more
developers maintaining less code so the benefits of the Open Source
model are magnified.


=head1 PRIORITIES

=head2 Transition Drivers

The first priority is to make all the infrastructure changes that
impact drivers and make an alpha release available for driver authors.

As far as possible, the changes will be implemented in a way that
enables driver authors use the same code base for DBI v1 and DBI v2.

The main changes required by driver authors are:

* Code changes for PERL_NO_GET_CONTEXT, plus removing PERL_POLLUTE
and DBIS

* Code changes in DBI/DBD interface (new way to create handles, new
callbacks etc)

* Common test suite infrastructure (driver-specific test base class)

=head2 Transition Applications

A small set of incompatible changes that may impact some applications
will also be made in v2.0. See http://svn.perl.org/modules/dbi/trunk/ToDo

=head2 Incremental Developments

Once DBI v2.0 is available, the other enhancements can be implemented
incrementally on the updated foundations. Priorities for those
changes have not been set.

=head2 DBI v1 

DBI v1 will continue to be maintained on a separate branch for
bug fixes and any enhancements that ease the transition to DBI v2.

=head1 RESOURCES AND CONTRIBUTIONS

See L<http://dbi.perl.org/contributing> for I<how you can help>.

If your company has benefited from the DBI, please consider if
it could make a donation to The Perl Foundation "DBI Development"
fund at L<http://dbi.perl.org/donate> to secure future development.

Alternatively, if your company would benefit from a specific new
DBI feature, please consider sponsoring its development through my
consulting company, Data Plan Services. Work is performed rapidly
on a fixed-price payment-on-delivery basis. Contact me for details.

Using such targeted financing allows you to contribute to DBI
development and rapidly get something specific and directly valuable
to you in return.

My company also offers annual support contracts for the DBI, which
provide another way to support the DBI and get something specific
in return. Contact me for details.

Thank you.

=cut
