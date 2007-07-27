# Copyright (c) 1999-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Control::SortResult;

use Net::LDAP::ASN qw(SortResult);
use Net::LDAP::Control;

$VERSION = "0.01";
@ISA = qw(Net::LDAP::Control);

sub init {
  my($self) = @_;

  if (exists $self->{value}) {
    $self->{asn} = $SortResult->decode(delete $self->{value});
  }
  else {
    $self->{asn} = { sortResult => delete $self->{result} };
    $self->{asn}{attributeType} = delete $self->{attr} if exists $self->{attr};
  }

  $self;
}

sub value {
  my $self = shift;

  $self->{value} = $SortResult->encode($self->{asn});
}

sub result {
  my $self = shift;

  @_ ? ($self->{asn}{sortResult}=shift)
     : $self->{asn}{sortResult};
}

sub attr {
  my $self = shift;

  @_ ? ($self->{asn}{attributeType}=shift)
     : $self->{asn}{attributeType};
}

1;


__END__


=head1 NAME

Net::LDAP::Control::SortResult - Server Side Sort (SSS) result control object

=head1 SYNOPSIS

 use Net::LDAP::Control::Sort;
 use Net::LDAP::Constant qw(LDAP_CONTROL_SORTRESULT);
 use Net::LDAP::Util qw(ldap_error_name);

 $sort = Net::LDAP::Control::Sort->new(
   order => "cn -age"
 );

 $mesg = $ldap->search( @args, control => [ $sort ]);

 ($resp) = $mesg->control( LDAP_CONTROL_SORTRESULT );

 if ($resp) {
   if ($resp->result) {
     my $attr = $resp->attr;
     print "Problem sorting, ",ldap_error_name($resp->result);
     print " ($attr)" if $attr;
     print "\n";
   }
   else {
     print "Results are sorted\n";
   }
 }
 else {
   print "Server does not support sorting\n";
 }

=head1 DESCRIPTION

C<Net::LDAP::Control::SortResult> is a sub-class of
L<Net::LDAP::Control>.  It provides a class for
manipulating the LDAP sort request control C<1.2.840.113556.1.4.474>
as defined in RFC-2891

A sort result control will be returned by the server in response to
a search with a Server Side Sort control. If a sort result control is
not returned then the user may assume that the server does not support
sorting and the results are not sorted.

=head1 CONSTRUCTOR ARGUMENTS

=over 4

=item attr

If C<result> indicates that there was a problem with sorting and that problem was
due to one of the attributes specified in the sort control. C<attr> is set to
the name of the attribute causing the problem.

=item result

This is the result code that describes if the sort operation was sucessful. If will
be one of the result codes describes below.

=back


=head1 METHODS

As with L<Net::LDAP::Control> each constructor argument
described above is also avaliable as a method on the object which will
return the current value for the attribute if called without an argument,
and set a new value for the attribute if called with an argument.

=head1 RESULT CODES

Possible results from a sort request are listed below. See L<Net::LDAP::Constant> for
a definition of each.

=over 4

=item LDAP_SUCCESS

=item LDAP_OPERATIONS_ERROR

=item LDAP_TIMELIMIT_EXCEEDED

=item LDAP_STRONG_AUTH_REQUIRED

=item LDAP_ADMIN_LIMIT_EXCEEDED

=item LDAP_NO_SUCH_ATTRIBUTE

=item LDAP_INAPPROPRIATE_MATCHING

=item LDAP_INSUFFICIENT_ACCESS

=item LDAP_BUSY

=item LDAP_UNWILLING_TO_PERFORM

=item LDAP_OTHER

=back

=head1 SEE ALSO

L<Net::LDAP>,
L<Net::LDAP::Control::Sort>,
L<Net::LDAP::Control>,
http://ww.ietf.org/rfc/rfc2891.txt

=head1 AUTHOR

Graham Barr E<lt>gbarr@pobox.comE<gt>

Please report any bugs, or post any suggestions, to the perl-ldap mailing list
E<lt>perl-ldap@perl.orgE<gt>

=head1 COPYRIGHT

Copyright (c) 1999-2004 Graham Barr. All rights reserved. This program is
free software; you can redistribute it and/or modify it under the same
terms as Perl itself.

=cut
