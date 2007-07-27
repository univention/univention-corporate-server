
package Net::LDAP::Extension::SetPassword;

require Net::LDAP::Extension;

$VERSION = "0.02";
@ISA = qw(Net::LDAP::Extension);

use Convert::ASN1;
my $passwdModReq = Convert::ASN1->new;
$passwdModReq->prepare(q<SEQUENCE {
                       user         [0] STRING OPTIONAL,
                       oldpasswd    [1] STRING OPTIONAL,
                       newpasswd    [2] STRING OPTIONAL
                       }>);

my $passwdModRes = Convert::ASN1->new;
$passwdModRes->prepare(q<SEQUENCE {
                       genPasswd    [0] STRING OPTIONAL
                       }>);

sub Net::LDAP::set_password {
  my $ldap = shift;
  my %opt = @_;

  my $res = $ldap->extension(
	name => '1.3.6.1.4.1.4203.1.11.1',
	value => $passwdModReq->encode(\%opt)
  );

  bless $res; # Naughty :-)
}

sub gen_password {
  my $self = shift;

  my $out = $passwdModRes->decode($self->response);

  $out->{genPasswd};
}

1;

__END__

=head1 NAME

Net::LDAP::Extension::SetPassword - LDAPv3 Modify Password extension object

=head1 SYNOPSIS

 use Net::LDAP;
 use Net::LDAP::Extension::SetPassword;

 $ldap = Net::LDAP->new( "ldap.mydomain.eg" );

 $ldap->bind('cn=Joe User,cn=People,dc=mydomain,dc=eg",
             password => 'oldPassword');

 $mesg = $ldap->set_password( oldpasswd => 'oldPassword' );

 die "error: ", $mesg->code(), ": ", $mesg->error()  if ($mesg->code());
 
 print "changed your password to", $mesg->gen_passwd() , "\n";


=head1 DESCRIPTION

C<Net::LDAP::Extension::SetPassword> implements the C<Modify Password>
extended LDAPv3 operation as described in RFC 3062.

It implements no object by itself but extends the L<Net::LDAP> object 
by another method:

=head1 METHODS

=over 4

=item set_password ( OPTIONS )

Set the password for a user.

OPTIONS is a list of key/value pairs. The following keys are recognized:

=over 4

=item user

If present, this option contains the octet string representation of the
user associated with the request.  Depending on how users are identified
in the directory this string may or may not be a DN according to RFC 2253.

If this option is not present present, the request acts up upon the
password of the user currently associated with the LDAP session.

=item oldpasswd

This option, if present, must contain the current password of the user
for whom this operation is performed.

It depends on the server's implementation in which cirumstances this 
option is allowed to be missing.

=item newpasswd

If present, this option contains the desired password for the user for
whom the operation is performed.

Depending on the server's implementation this option may be required by
the LDAP server.

=back


=item gen_password ( )

Return the password generated in the previous C<set_password()> call.

This method is a method of the L<Net::LDAP::Message> response object
returned in reply to C<set_password()> in case the C<set_password()>
call succeeded.

By this method the caller can query for the value of the password in
case he did not call C<set_password()> with the C<newpasswd> option.

=back

=head1 SEE ALSO

L<Net::LDAP>,
L<Net::LDAP::Extension>

=head1 AUTHOR

Graham Barr E<lt>gbarr@pobox.comE<gt>,
documentation by Peter Marschall E<lt>peter@adpm.deE<gt>.

Please report any bugs, or post any suggestions, to the perl-ldap
mailing list E<lt>perl-ldap@perl.orgE<gt>

=head1 COPYRIGHT

Copyright (c) 2002-2004 Graham Barr. All rights reserved. This program is
free software; you can redistribute it and/or modify it under the same
terms as Perl itself.

=cut

