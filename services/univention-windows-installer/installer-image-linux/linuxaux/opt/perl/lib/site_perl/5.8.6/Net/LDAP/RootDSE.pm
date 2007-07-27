# Copyright (c) 2003-2004 Chris Ridd <chris.ridd@isode.com> and
# Graham Barr <gbarr@pobox.com>. All rights reserved.  This program is
# free software; you can redistribute it and/or modify it under the
# same terms as Perl itself.

package Net::LDAP::RootDSE;

use Net::LDAP::Entry;

@ISA = qw(Net::LDAP::Entry);
$VERSION = "0.01";

use strict;

sub supported_feature        { _supported_feature( @_, 'supportedFeatures'       ) }
sub supported_extension      { _supported_feature( @_, 'supportedExtension'      ) }
sub supported_version        { _supported_feature( @_, 'supportedLDAPVersion'    ) }
sub supported_control        { _supported_feature( @_, 'supportedControl'        ) }
sub supported_sasl_mechanism { _supported_feature( @_, 'supportedSASLMechanisms' ) }

sub _supported_feature {
  my $root = shift;
  my $attr = pop;

  my %ext; @ext{ $root->get_value( $attr ) } = ();

  @_ == grep exists $ext{$_}, @_;
}

1;

__END__

=head1 NAME

Net::LDAP::RootDSE - An LDAP RootDSE object

=head1 SYNOPSIS

 my $dse = $ldap->root_dse();

 # get naming Contexts
 my @contexts = $dse->get_value('namingContext');

 # get supported LDAP versions as an array reference
 my $versions = $dse->get_value('supportedLDAPVersion', asref => 1);

=head1 DESCRIPTION

=head2 Methods

=over 4

=item get_value

C<get_value> is identical to L<Net::LDAP::Entry/get_value>

=item supported_extension ( OID_LIST )

Returns true if the server supports all of the specified
extension OIDs

=item supported_feature ( OID_LIST )

Returns true if the server supports all of the specified
feature OIDs

=item supported_version ( VERSION_LIST )

Returns true if the server supports all of the specified
versions

=item supported_control ( OID_LIST )

Returns true if the server supports all of the specified
control OIDs

=item supported_sasl_mechanism ( SASL_MECH_LIST )

Returns true if the server supports all of the specified
SASL mechanism names

=back

=head1 SEE ALSO

L<Net::LDAP>, L<Net::LDAP::Entry>

=head1 AUTHOR

Chris Ridd E<lt>chris.ridd@isode.comE<gt>, 
Graham Barr E<lt>gbarr@pobox.comE<gt>.

=head1 COPYRIGHT

Copyright (c) 2003-2004, Chris Ridd and Graham Barr. All rights reserved. This
library is free software; you can redistribute it and/or modify
it under the same terms as Perl itself.

=cut
