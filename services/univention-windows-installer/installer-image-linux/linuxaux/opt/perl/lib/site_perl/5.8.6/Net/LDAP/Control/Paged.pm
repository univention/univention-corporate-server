# Copyright (c) 2000-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Control::Paged;

use vars qw(@ISA $VERSION);
use Net::LDAP::Control;

@ISA = qw(Net::LDAP::Control);
$VERSION = "0.02";

use Net::LDAP::ASN qw(realSearchControlValue);
use strict;

sub init {
  my($self) = @_;

  delete $self->{asn};

  unless (exists $self->{value}) {
    $self->{asn} = {
      size   => $self->{size} || 0,
      cookie => defined($self->{cookie}) ? $self->{cookie} : ''
    };
  }

  $self;
}

sub cookie {
  my $self = shift;
  $self->{asn} ||= $realSearchControlValue->decode($self->{value});
  if (@_) {
    delete $self->{value};
    return $self->{asn}{cookie} = defined($_[0]) ? $_[0] : '';
  }
  $self->{asn}{cookie};
}

sub size {
  my $self = shift;
  $self->{asn} ||= $realSearchControlValue->decode($self->{value});
  if (@_) {
    delete $self->{value};
    return $self->{asn}{size} = shift || 0;
  }
  $self->{asn}{size};
}

sub value {
  my $self = shift;

  exists $self->{value}
    ? $self->{value}
    : $self->{value} = $realSearchControlValue->encode($self->{asn});
}

1;

__END__

=head1 NAME

Net::LDAP::Control::Paged - LDAPv3 Paged results control object

=head1 SYNOPSIS

 use Net::LDAP;
 use Net::LDAP::Control::Paged;
 use Net::LDAP::Constant qw( LDAP_CONTROL_PAGED );

 $ldap = Net::LDAP->new( "ldap.mydomain.eg" );

 $page = Net::LDAP::Control::Paged->new( size => 100 );

 @args = ( base     => "cn=subnets,cn=sites,cn=configuration,$BASE_DN",
	   scope    => "subtree",
	   filter   => "(objectClass=subnet)",
	   callback => \&process_entry, # Call this sub for each entry
	   control  => [ $page ],
 );

 my $cookie;
 while(1) {
   # Perform search
   my $mesg = $ldap->search( @args );

   # Only continue on LDAP_SUCCESS
   $mesg->code and last;

   # Get cookie from paged control
   my($resp)  = $mesg->control( LDAP_CONTROL_PAGED ) or last;
   $cookie    = $resp->cookie or last;

   # Set cookie in paged control
   $page->cookie($cookie);
 }

 if ($cookie) {
   # We had an abnormal exit, so let the server know we do not want any more
   $page->cookie($cookie);
   $page->size(0);
   $ldap->search( @args );
 }

=head1 DESCRIPTION

C<Net::LDAP::Control::Paged> provides an interface for the creation and manipulation
of objects that represent the C<pagedResultsControl> as described by RFC-2696.

=head1 CONSTRUCTOR ARGUMENTS

In addition to the constructor arguments described in
L<Net::LDAP::Control> the following are provided.

=over 4

=item cookie

The value to use as the cookie. This is not normally set when an object is
created, but is set from the cookie value returned by the server. This associates
a search with a previous search, so the server knows to return the page
of entries following the entries it returned the previous time.

=item size

The page size that is required. This is the maximum number of entries that the
server will return to the search request.

=back

=head1 METHODS

As with L<Net::LDAP::Control> each constructor argument
described above is also avaliable as a method on the object which will
return the current value for the attribute if called without an argument,
and set a new value for the attribute if called with an argument.

=head1 SEE ALSO

L<Net::LDAP>,
L<Net::LDAP::Control>,
http://www.ietf.org/rfc/rfc2696.txt

=head1 AUTHOR

Graham Barr E<lt>gbarr@pobox.comE<gt>

Please report any bugs, or post any suggestions, to the perl-ldap mailing list
E<lt>perl-ldap@perl.orgE<gt>

=head1 COPYRIGHT

Copyright (c) 2000-2004 Graham Barr. All rights reserved. This program is
free software; you can redistribute it and/or modify it under the same
terms as Perl itself.

=cut

