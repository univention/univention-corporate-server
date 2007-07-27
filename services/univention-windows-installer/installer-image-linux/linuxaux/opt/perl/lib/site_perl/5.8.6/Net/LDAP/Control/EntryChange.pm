# Copyright (c) 2004 Peter Marschall <peter@adpm.de>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Control::EntryChange;

use vars qw(@ISA $VERSION);
use Net::LDAP::Control;

@ISA = qw(Net::LDAP::Control);
$VERSION = "0.01";

use Net::LDAP::ASN qw(EntryChangeNotification);
use strict;

sub init {
  my($self) = @_;

  delete $self->{asn};

  unless (exists $self->{value}) {
    $self->{asn} = {
      changeTypes  => $self->{changeType} || '0',
      previousDN   => $self->{previousDN} || '',
      changeNumber => $self->{changeNumber} || '0',
    };
  }

  $self;
}

sub changeType {
  my $self = shift;
  $self->{asn} ||= $EntryChangeNotification->decode($self->{value});
  if (@_) {
    delete $self->{value};
    return $self->{asn}{changeType} = shift || 0;
  }
  $self->{asn}{changeType};
}

sub previousDN {
  my $self = shift;
  $self->{asn} ||= $EntryChangeNotification->decode($self->{value});
  if (@_) {
    delete $self->{value};
    return $self->{asn}{previousDN} = shift || '';
  }
  $self->{asn}{previousDN};
}

sub changeNumber {
  my $self = shift;
  $self->{asn} ||= $EntryChangeNotification->decode($self->{value});
  if (@_) {
    delete $self->{value};
    return $self->{asn}{changeNumber} = shift || 0;
  }
  $self->{asn}{changeNumber};
}

sub value {
  my $self = shift;

  exists $self->{value}
    ? $self->{value}
    : $self->{value} = $EntryChangeNotification->encode($self->{asn});
}

1;

__END__

=head1 NAME

Net::LDAP::Control::EntryChange - LDAPv3 Entry Change Notification control object

=head1 SYNOPSIS

 use Net::LDAP;
 use Net::LDAP::Control::PersistentSearch;
 use Net::LDAP::Constant qw(LDAP_CONTROL_ENTRYCHANGE);

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
   my ($control) = $message->control(LDAP_CONTROL_ENTRYCHANGE);

   print $control->changeType()."\t".$entry->dn()."\n";
 }


=head1 DESCRIPTION

C<Net::LDAP::Control::EntryChange> provides an interface for the creation
and manipulation of objects that represent the C<EntryChangeNotification>
control as described by draft-smith-psearch-ldap-01.txt.

=head1 CONSTRUCTOR ARGUMENTS

In addition to the constructor arguments described in
L<Net::LDAP::Control> the following are provided.

=over 4

=item changeType

An integer value telling the type of LDAP operation that the entry
has undergone.
It is one of the following values (which represent the LDAP
operations indicated next to them):

=over 4

=item 1 = add

=item 2 = delete

=item 4 = modify

=item 8 = modDN

=back

=item previousDN

When changeType is 8 (for modDN) this parameter tells the entry's DN
before the modDN operation.
In all other cases this value is not defined.

=item changeNumber

This is the change number according to <draft-good-ldap-changelog-03.txt>
assigned by a server for the change.  If a server supports an LDAP
Change Log it should include this field.

=back

Usually you do not need to create a C<Net::LDAP::Control::EntryChange>
control yourself because it is provided by the server in response to
an option with the C<Net::LDAP::Control::PersistentSearch> control.

=head1 METHODS

As with L<Net::LDAP::Control> each constructor argument
described above is also available as a method on the object which will
return the current value for the attribute if called without an argument,
and set a new value for the attribute if called with an argument.

=head1 SEE ALSO

L<Net::LDAP>,
L<Net::LDAP::Control>,
L<Net::LDAP::Control::PersistentSearch>

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

