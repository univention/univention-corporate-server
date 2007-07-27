# Copyright (c) 2000-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Extra;

use strict;
use vars qw($VERSION);

require Net::LDAP;
require Carp;

$VERSION = "0.01";

sub import {
  shift;
  local $SIG{__DIE__} = \&Carp::croak;
  foreach (@_) {
    my $file = "Net/LDAP/Extra/$_.pm";
    next if exists $INC{$file};
    require $file;
    "Net::LDAP::Extra::$_"->import;
  }
}

1;

__END__


=head1 NAME

Net::LDAP::Extra -- Load extra Net::LDAP methods

=head1 SYNOPSIS

  use Net::LDAP::Extra qw(my_extn);

  $ldap = Net::LDAP->new( ... );

  $ldap->my_extn( ... );

=head1 DESCRIPTION

C<Net::LDAP::Extra> allows extra methods to be added to Net::LDAP.
Normally such methods would be added by sub-classing Net::LDAP, but this
proves to get messy as different people write different additions and
others want to use multiple of these sub-classes. Users end up having
to create sub-classes of their own which inherit from all the extension
sub-classes just so they can get all the features.

C<Net::LDAP::Extra> allows methods to be added directly to
all Net::LDAP objects. This can be done by creating a class
C<Net::LDAP::Extra::name> which exports functions. A
C<use Net::LDAP::Extra qw(name)> will then make these functions avaliable
as a methods on all C<Net::LDAP> objects.

Care should be taken when choosing names for the functions to export
to ensure that they do not clash with others.

=cut

