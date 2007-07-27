# Copyright (c) 1999-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Control::Sort;

use vars qw(@ISA $VERSION);
use Net::LDAP::Control;

@ISA = qw(Net::LDAP::Control);
$VERSION = "0.02";

use Net::LDAP::ASN qw(SortRequest);
use strict;

sub init {
  my($self) = @_;

  if (exists $self->{value}) {
    $self->value($self->{value});
  }
  elsif (exists $self->{order}) {
    $self->order(ref($self->{order}) ? @{$self->{order}} : $self->{order});
  }

  $self;
}

sub value {
  my $self = shift;

  if (@_) {
    my $value = shift;

    delete $self->{value};
    delete $self->{order};
    delete $self->{error};

    my $asn = $SortRequest->decode($value);

    unless ($asn) {
      $self->{error} = $@;
      return undef;
    }

    $self->{order} = [ map {
      ($_->{reverseOrder} ? "-" : "")
      . $_->{type}
      . (defined($_->{orderingRule}) ? ":$_->{orderingRule}" : "")
    } @{$asn->{order}}];

    return $self->{value} = $value;
  }

  unless (defined $self->{value}) {
    $self->{value} = $SortRequest->encode(
      order => [
	map {
	  /^(-)?([^:]+)(?::(.+))?/;
	  {
	    type => $2,
	    (defined $1 ? (reverseOrder => 1)  : ()), 
	    (defined $3 ? (orderingRule => $3) : ())
	  }
	} @{$self->{order} || []}
      ]
    ) or $self->{error} = $@;
  }

  $self->{value};
}

sub valid { exists shift->{order} }

sub order {
  my $self = shift;

  if (@_) {
    # @_ can either be a list, or a single item.
    # if a single item it can be a string, which needs
    # to be split on spaces, or a reference to a list
    #
    # Each element has three parts
    #  leading - (optional)
    #  an attribute name
    #  :match-rule (optional)

    my @order = (@_ == 1) ? split(/\s+/, $_[0]) : @_;

    delete $self->{'value'};
    delete $self->{order};
    delete $self->{error};

    foreach (@order) {
      next if /^-?[^:]+(?::.+)?$/;

      $self->{error} = "Bad order argument '$_'";
      return;
    }

    $self->{order} = \@order;
  }

  return @{$self->{order}};
}

1;

__END__


=head1 NAME

Net::LDAP::Control::Sort - Server Side Sort (SSS) control object

=head1 SYNOPSIS

 use Net::LDAP::Control::Sort;
 use Net::LDAP::Constant qw(LDAP_CONTROL_SORTRESULT);

 $sort = Net::LDAP::Control::Sort->new(
   order => "cn -phone"
 );

 $mesg = $ldap->search( @args, control => [ $sort ]);

 ($resp) = $mesg->control( LDAP_CONTROL_SORTRESULT );

 print "Results are sorted\n" if $resp and !$resp->result;

=head1 DESCRIPTION

C<Net::LDAP::Control::Sort> is a sub-class of
L<Net::LDAP::Control>.  It provides a class
for manipulating the LDAP Server Side Sort (SSS) request control
C<1.2.840.113556.1.4.473> as defined in RFC-2891

If the server supports sorting, then the response from a search
operation will include a sort result control. This control is handled
by L<Net::LDAP::Control::SortResult>.

=head1 CONSTRUCTOR ARGUMENTS

=over 4

=item order

A string which defines how entries may be sorted. It consists of
multiple directives, spearated by whitespace. Each directive describes how
to sort entries using a single attribute. If two entries have identical
attributes, then the next directive in the list is used.

Each directive specifies a sorting order as follows

  -attributeType:orderingRule

The leading C<-> is optional, and if present indicates that the sorting order should
be reversed. C<attributeType> is the attribute name to sort by. C<orderingRule> is optional and
indicates the rule to use for the sort and should be valid for the given C<attributeType>.

Any one attributeType should only appear once in the sorting list.

B<Examples>

  "cn"         sort by cn using the default ordering rule for the cn attribute
  "-cn"        sort by cn using the reverse of the default ordering rule
  "age cn"     sort by age first, then by cn using the default ordering rules
  "cn:1.2.3.4" sort by cn using the ordering rule defined as 1.2.3.4

=back


=head1 METHODS

As with L<Net::LDAP::Control> each constructor argument
described above is also available as a method on the object which will
return the current value for the attribute if called without an argument,
and set a new value for the attribute if called with an argument.

=head1 SEE ALSO

L<Net::LDAP>,
L<Net::LDAP::Control::SortResult>,
L<Net::LDAP::Control>,
http://www.ietf.org/rfc/rfc2891.txt

=head1 AUTHOR

Graham Barr E<lt>gbarr@pobox.comE<gt>

Please report any bugs, or post any suggestions, to the perl-ldap mailing list
E<lt>perl-ldap@perl.orgE<gt>

=head1 COPYRIGHT

Copyright (c) 1999-2004 Graham Barr. All rights reserved. This program is
free software; you can redistribute it and/or modify it under the same
terms as Perl itself.

=cut
