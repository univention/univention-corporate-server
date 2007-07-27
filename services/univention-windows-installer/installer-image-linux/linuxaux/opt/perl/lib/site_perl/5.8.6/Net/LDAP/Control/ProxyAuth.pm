# Copyright (c) 2001-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Control::ProxyAuth;

use vars qw(@ISA $VERSION);
use Net::LDAP::Control;

@ISA = qw(Net::LDAP::Control);
$VERSION = "1.04";

use Net::LDAP::ASN qw(proxyAuthValue);
use strict;

sub init {
  my($self) = @_;

  delete $self->{asn};

  unless (exists $self->{value}) {
    $self->{asn} = {
      proxyDN   => $self->{proxyDN} || '',
    };
  }

  $self->{critical}=1;

  $self;
}

sub proxyDN {
  my $self = shift;
  $self->{asn} ||= $proxyAuthValue->decode($self->{value});
  if (@_) {
    delete $self->{value};
    return $self->{asn}{proxyDN} = shift || 0;
  }
  $self->{asn}{proxyDN};
}

sub value {
  my $self = shift;

  exists $self->{value}
    ? $self->{value}
    : $self->{value} = $proxyAuthValue->encode($self->{asn});
}

1;

__END__

=head1 NAME

Net::LDAP::Control::ProxyAuth - LDAPv3 Proxy Authentication control object

=head1 SYNOPSIS

 use Net::LDAP;
 use Net::LDAP::Control::ProxyAuth;

 $ldap = Net::LDAP->new( "ldap.mydomain.eg" );

 $auth = Net::LDAP::Control::ProxyAuth->new( proxyDN => 'cn=me,ou=people,o=myorg.com' );

 @args = ( base     => "cn=subnets,cn=sites,cn=configuration,$BASE_DN",
	   scope    => "subtree",
	   filter   => "(objectClass=subnet)",
	   callback => \&process_entry, # Call this sub for each entry
	   control  => [ $auth ],
 );

 while(1) {
   # Perform search
   my $mesg = $ldap->search( @args );

   # Only continue on LDAP_SUCCESS
   $mesg->code and last;

 }


=head1 DESCRIPTION

C<Net::LDAP::Control::ProxyAuth> provides an interface for the creation and manipulation
of objects that represent the C<proxyauthorisationControl> as described by draft-weltman-ldapv3-proxy-05.txt.

=head1 CONSTRUCTOR ARGUMENTS

In addition to the constructor arguments described in
L<Net::LDAP::Control> the following are provided.

=over 4

=item proxyDN

The proxyDN that is required. This is the identity we are requesting operations to use

=back

=head1 METHODS

As with L<Net::LDAP::Control> each constructor argument
described above is also available as a method on the object which will
return the current value for the attribute if called without an argument,
and set a new value for the attribute if called with an argument.

=head1 SEE ALSO

L<Net::LDAP>,
L<Net::LDAP::Control>,

=head1 AUTHOR

Olivier Dubois, Swift sa/nv based on Net::LDAP::Control::Page from
Graham Barr E<lt>gbarr@pobox.comE<gt>

Please report any bugs, or post any suggestions, to the perl-ldap
mailing list E<lt>perl-ldap@perl.orgE<gt>

=head1 COPYRIGHT

Copyright (c) 2001-2004 Graham Barr. All rights reserved. This program is
free software; you can redistribute it and/or modify it under the same
terms as Perl itself.

=cut

