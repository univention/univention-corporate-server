# Copyright (c) 2000-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Control::VLVResponse;

use vars qw(@ISA $VERSION);
use Net::LDAP::Control;

@ISA = qw(Net::LDAP::Control);
$VERSION = "0.03";

use Net::LDAP::ASN qw(VirtualListViewResponse);
use strict;

sub init {
  my($self) = @_;

  if (exists $self->{value}) {
    $self->value($self->{value});
  }
  else {
    my $asn = $self->{asn} = {};

    $asn->{targetPosition}        = $self->{target}    || 0;
    $asn->{contentCount}          = $self->{content}   || 0;
    $asn->{virtualListViewResult} = $self->{result}    || 0;
    $asn->{contextID}             = $self->{contextID} || undef;
  }

  $self;
}


sub target {
  my $self = shift;
  if (@_) {
    delete $self->{value};
    return $self->{asn}{targetPosition} = shift;
  }
  $self->{asn}{targetPosition};
}

sub content {
  my $self = shift;
  if (@_) {
    delete $self->{value};
    return $self->{asn}{contentCount} = shift;
  }
  $self->{asn}{contentCount};
}

sub result {
  my $self = shift;
  if (@_) {
    delete $self->{value};
    return $self->{asn}{virtualListViewResult} = shift;
  }
  $self->{asn}{virtualListViewResult};
}

sub context {
  my $self = shift;
  if (@_) {
    delete $self->{value};
    return $self->{asn}{contextID} = shift;
  }
  $self->{asn}{contextID};
}

sub value {
  my $self = shift;

  if (@_) {
    unless ($self->{asn} = $VirtualListViewResponse->decode($_[0])) {
      delete $self->{value};
      return undef;
    }
    $self->{value} = shift;
  }

  exists $self->{value}
    ? $self->{value}
    : $self->{value} = $VirtualListViewResponse->encode($self->{asn});
}

1;

__END__

=head1 NAME

Net::LDAP::Control::VLVResponse -- LDAPv3 Virtual List View server response

=head1 SYNOPSIS

See L<Net::LDAP::Control::VLV>

=head1 DESCRIPTION

C<Net::LDAP::Control::VLVResponse> is a sub-class of L<Net::LDAP::Control>.
It provides a class for manipulating the LDAP Virtual List View Response control
C<>

If the server supports Virtual List Views, then the response from a search operation will
include a VLVResponse control.

=head1 CONSTRUCTOR ARGUMENTS

In addition to the constructor arguments described in
L<Net::LDAP::Control> the following are provided.

=over 4

=item content

An estimate of the number of entries in the complete list. This value should
be used in any subsequent Virtual List View control using the same list.

=item context

An arbitary value which is used to associate subsequent requests with the
request which this control is a response for. This value should be copied
by the client into the Virtual List View control for any subsequent
search that uses the same list.

=item result

A result code indicating the result of the Virtual List View request. This
may be any of the codes listed below.

=item target

The list offset of the target entry.

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

=item LDAP_ADMIN_LIMIT_EXCEEDED

=item LDAP_INSUFFICIENT_ACCESS

=item LDAP_BUSY

=item LDAP_UNWILLING_TO_PERFORM

=item LDAP_OTHER

=item LDAP_SORT_CONTROL_MISSING

=item LDAP_INDEX_RANGE_ERROR

=back

=head1 SEE ALSO

L<Net::LDAP>,
L<Net::LDAP::Control>

=head1 AUTHOR

Graham Barr E<lt>gbarr@pobox.comE<gt>

Please report any bugs, or post any suggestions, to the perl-ldap mailing list
E<lt>perl-ldap@perl.orgE<gt>

=head1 COPYRIGHT

Copyright (c) 2000-2004 Graham Barr. All rights reserved. This program is
free software; you can redistribute it and/or modify it under the same
terms as Perl itself.

=cut

