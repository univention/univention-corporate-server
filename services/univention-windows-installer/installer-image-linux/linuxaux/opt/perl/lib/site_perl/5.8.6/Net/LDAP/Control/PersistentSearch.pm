# Copyright (c) 2004 Peter Marschall <peter@adpm.de>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Control::PersistentSearch;

use vars qw(@ISA $VERSION);
use Net::LDAP::Control;

@ISA = qw(Net::LDAP::Control);
$VERSION = "0.01";

use Net::LDAP::ASN qw(PersistentSearch);
use strict;

sub init {
  my($self) = @_;

  delete $self->{asn};

  unless (exists $self->{value}) {
    $self->{asn} = {
      changeTypes => $self->{changeTypes} || '15',
      changesOnly => $self->{changesOnly} || '0',
      returnECs   => $self->{returnECs} || '0',
    };
  }

  $self;
}

sub changeTypes {
  my $self = shift;
  $self->{asn} ||= $PersistentSearch->decode($self->{value});
  if (@_) {
    delete $self->{value};
    return $self->{asn}{changeTypes} = shift || 0;
  }
  $self->{asn}{changeTypes};
}

sub changesOnly {
  my $self = shift;
  $self->{asn} ||= $PersistentSearch->decode($self->{value});
  if (@_) {
    delete $self->{value};
    return $self->{asn}{changesOnly} = shift || 0;
  }
  $self->{asn}{changesOnly};
}

sub returnECs {
  my $self = shift;
  $self->{asn} ||= $PersistentSearch->decode($self->{value});
  if (@_) {
    delete $self->{value};
    return $self->{asn}{returnECs} = shift || 0;
  }
  $self->{asn}{returnECs};
}

sub value {
  my $self = shift;

  exists $self->{value}
    ? $self->{value}
    : $self->{value} = $PersistentSearch->encode($self->{asn});
}

1;

__END__

=head1 NAME

Net::LDAP::Control::PersistentSearch - LDAPv3 Persistent Search control object

=head1 SYNOPSIS

 use Net::LDAP;
 use Net::LDAP::Control::PersistentSearch;

 $ldap = Net::LDAP->new( "ldap.mydomain.eg" );

 $persist = Net::LDAP::Control::PersistentSearch->new( changeTypes => 15,
                                                       changesOnly => 1,
                                                       returnECs => 1 );

 $srch = $ldap->search( base     => "cn=People,dc=mydomain,dc=eg",
                        filter   => "(objectClass=person)",
                        callback => \&process_entry, # call for each entry
                        control  => [ $persist ] );

 die "error: ",$srch->code(),": ",$srch->error()  if ($srch->code());

 sub process_entry {
   my $message = shift;
   my $entry = shift;

   print $entry->dn()."\n";
 }


=head1 DESCRIPTION

C<Net::LDAP::Control::PersistentSearch> provides an interface for the creation
and manipulation of objects that represent the C<PersistentSearch> control as
described by draft-smith-psearch-ldap-01.txt.

=head1 CONSTRUCTOR ARGUMENTS

In addition to the constructor arguments described in
L<Net::LDAP::Control> the following are provided.

=over 4

=item changeTypes

An integer value determining the types of changes to look out for.
It is the bitwise OR of the following values (which represent the LDAP
operations indicated next to them):

=over 4

=item 1 = add

=item 2 = delete

=item 4 = modify

=item 8 = modDN

=back

If it is not given it defaults to 15 meaning all changes.

=item changesOnly

A boolean value telling whether the server may return
entries that match the search criteria.

If C<TRUE> the server must not return return any existing
entries that match the search criteria.  Entries are only
returned when they are changed (added, modified, deleted, or
subject to a modifyDN operation)

=item returnECs

If C<TRUE>, the server must return an Entry Change Notification
control with each entry returned as the result of changes.

See L<Net::LDAP::Control::EntryChange> for details.

=back

=head1 METHODS

As with L<Net::LDAP::Control> each constructor argument
described above is also available as a method on the object which will
return the current value for the attribute if called without an argument,
and set a new value for the attribute if called with an argument.

=head1 SEE ALSO

L<Net::LDAP>,
L<Net::LDAP::Control>,
L<Net::LDAP::Control::EntryChange>

=head1 AUTHOR

Peter Marschall E<lt>peter@adpm.deE<gt>, based on Net::LDAP::Control::Page
from Graham Barr E<lt>gbarr@pobox.comE<gt> and the preparatory work
of Don Miller E<lt>donm@uidaho.eduE<gt>.

Please report any bugs, or post any suggestions, to the perl-ldap
mailing list E<lt>perl-ldap@perl.orgE<gt>

=head1 COPYRIGHT

Copyright (c) 2004 Peter Marschall. All rights reserved. This program is
free software; you can redistribute it and/or modify it under the same
terms as Perl itself.

=cut

