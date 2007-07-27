# Copyright (c) 2000-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Control::VLV;

use vars qw(@ISA $VERSION);
use Net::LDAP::Control;

@ISA = qw(Net::LDAP::Control);
$VERSION = "0.03";

use Net::LDAP::ASN qw(VirtualListViewRequest);
use strict;

sub init {
  my($self) = @_;

  # VLVREQUEST should always have a critical of true
  $self->{'critical'} = 1 unless exists $self->{'critical'};

  if (exists $self->{value}) {
    $self->value($self->{value});
  }
  else {
    my $asn = $self->{asn} = {};

    $asn->{beforeCount} = $self->{before} || 0;
    $asn->{afterCount}  = $self->{after} || 0;
    if (exists $self->{assert}) {
      $asn->{byValue} = $self->{assert};
    }
    else {
      $asn->{byoffset} = {
 	offset => $self->{offset} || 0,
	contentCount => $self->{content} || 0
      };
    }
  }

  $self;
}

sub before {
  my $self = shift;
  if (@_) {
    delete $self->{value};
    return $self->{asn}{beforeCount} = shift;
  }
  $self->{asn}{beforeCount};
}

sub after  {
  my $self = shift;
  if (@_) {
    delete $self->{value};
    return $self->{asn}{afterCount} = shift;
  }
  $self->{asn}{afterCount};
}

sub content {
  my $self = shift;
  if (@_) {
    delete $self->{value};
    if (exists $self->{asn}{byValue}) {
      delete $self->{asn}{byValue};
      $self->{asn}{byoffset} = { offset => 0 };
    }
    return $self->{asn}{byoffset}{contentCount} = shift;
  }
  exists $self->{asn}{byoffset}
    ? $self->{asn}{byoffset}{contentCount}
    : undef;
}

sub assert {
  my $self = shift;
  if (@_) {
    delete $self->{value};
    delete $self->{asn}{byoffset};
    return $self->{asn}{byValue} = shift;
  }
  exists $self->{asn}{byValue}
    ? $self->{asn}{byValue}
    : undef;
}

sub context {
  my $self = shift;
  if (@_) {
    delete $self->{value};
    return $self->{asn}{contextID} = shift;
  }
  $self->{asn}{contextID};
}

# Update self with values from a response

sub response {
  my $self = shift;
  my $resp = shift;
  
  my $asn = $self->{asn};

  $asn->{contextID} = $resp->context;
  $asn->{byoffset} = {
    offset => $resp->target,
    contentCount => $resp->content
  };
  delete $asn->{byValue};

  1;  
}

sub offset {
  my $self = shift;
  if (@_) {
    delete $self->{value};
    if (exists $self->{asn}{byValue}) {
      delete $self->{asn}{byValue};
      $self->{asn}{byoffset} = { contentCount => 0 };
    }
    return $self->{asn}{byoffset}{offset} = shift;
  }
  exists $self->{asn}{byoffset}
    ? $self->{asn}{byoffset}{offset}
    : undef;
}

sub value {
  my $self = shift;

  if (@_) {
    unless ($self->{asn} = $VirtualListViewRequest->decode($_[0])) {
      delete $self->{value};
      return undef;
    }
    $self->{value} = shift;
  }

  exists $self->{value}
    ? $self->{value}
    : $self->{value} = $VirtualListViewRequest->encode($self->{asn});
}

sub scroll {
  my $self = shift;
  my $n = shift;
  my $asn = $self->{asn};
  my $byoffset = $asn->{byoffset}
    or return undef;
  my $offset = $byoffset->{offset} + $n;
  my $content;

  if ($offset < 1) {
    $asn->{afterCount} += $asn->{beforeCount};
    $asn->{beforeCount} = 0;
    $offset = $byoffset->{offset} = 1;
  }
  elsif ($byoffset->{contentCount} and $asn->{afterCount}+$offset >$byoffset->{contentCount}) {
    if ($offset > $byoffset->{contentCount}) {
      $offset = $byoffset->{offset} = $byoffset->{contentCount};
      $asn->{beforeCount} += $asn->{afterCount};
      $asn->{afterCount} = 0;
    }
    else {
      my $tmp = $byoffset->{contentCount} - $offset;
      $asn->{beforeCount} += $tmp;
      $asn->{afterCount}  -= $tmp;
      $byoffset->{offset} = $offset;
    }
  }
  else {
    $byoffset->{offset} = $offset;
  }

  $offset;
}

sub scroll_page {
  my $self = shift;
  my $n = shift;
  my $asn = $self->{asn};
  my $page_size = $asn->{beforeCount} + $asn->{afterCount} + 1;

  $self->scroll( $page_size * $n);
}

sub start {
  my $self = shift;
  my $asn = $self->{asn};
  $asn->{afterCount} += $asn->{beforeCount};
  $asn->{beforeCount} = 0;
  $self->offset(1);
}

sub end {
  my $self = shift;
  my $asn = $self->{asn};
  my $content = $self->content || 0;
  
  $asn->{beforeCount} += $asn->{afterCount};
  $asn->{afterCount} = 0;
  $self->offset($content);
}

1;

__END__

=head1 NAME

Net::LDAP::Control::VLV - LDAPv3 Virtual List View control object

=head1 SYNOPSIS

 use Net::LDAP;
 use Net::LDAP::Control::VLV;
 use Net::LDAP::Constant qw( LDAP_CONTROL_VLVRESPONSE );

 $ldap = Net::LDAP->new( "ldap.mydomain.eg" );

 # Get the first 20 entries
 $vlv  = Net::LDAP::Control::VLV->new(
	   before  => 0,	# No entries from before target entry
	   after   => 19,	# 19 entries after target entry
	   content => 0,	# List size unknown
	   offset  => 1,	# Target entry is the first
	 );
 $sort = Net::LDAP::Control::Sort->new( sort => 'cn' );

 @args = ( base     => "o=Ace Industry, c=us",
	   scope    => "subtree",
	   filter   => "(objectClass=inetOrgPerson)",
	   callback => \&process_entry, # Call this sub for each entry
	   control  => [ $vlv, $sort ],
 );

 $mesg = $ldap->search( @args );

 # Get VLV response control
 ($resp)  = $mesg->control( LDAP_CONTROL_VLVRESPONSE ) or die;
 $vlv->response( $resp );

 # Set the control to get the last 20 entries
 $vlv->end;

 $mesg = $ldap->search( @args );

 # Get VLV response control
 ($resp)  = $mesg->control( LDAP_CONTROL_VLVRESPONSE ) or die;
 $vlv->response( $resp );

 # Now get the previous page
 $vlv->scroll_page( -1 );

 $mesg = $ldap->search( @args );

 # Get VLV response control
 ($resp)  = $mesg->control( LDAP_CONTROL_VLVRESPONSE ) or die;
 $vlv->response( $resp );

 # Now page with first entry starting with "B" in the middle
 $vlv->before(9);	# Change page to show 9 before
 $vlv->after(10);	# Change page to show 10 after
 $vlv->assert("B");	# assert "B"
 
 $mesg = $ldap->search( @args );

=head1 DESCRIPTION

C<Net::LDAP::Control::VLV> provides an interface for the creation and
manipulation of objects that represent the Virtual List View as described
by draft-ietf-ldapext-ldapv3-vlv-03.txt.

When using a Virtual List View control in a search, it must be accompanied by a sort
control. See L<Net::LDAP::Control::Sort>

=cut

##
## Need some blurb here to describe the VLV control. Maybe extract some simple
## describtion from the draft RFC
##

=head1 CONSTRUCTOR ARGUMENTS

In addition to the constructor arguments described in
L<Net::LDAP::Control> the following are provided.

=over 4

=item after

Set the number of entries the server should return from the list after
the target entry.

=item assert

Set the assertion value user to locate the target entry. This value should
be a legal value to compare with the first attribute in the sort control
that is passed with the VLV control. The target entry is the first entry
in the list which is greater than or equal the assert value.

=item before

Set the number of entries the server should return from the list before
the target entry.

=item content

Set the number of entries in the list. On the first search this value
should be set to zero. On subsequent searches it should be set to the
length of the list, as returned by the server in the VLVResponse control.

=item context

Set the context identifier.  On the first search this value should be
set to zero. On subsequent searches it should be set to the context
value returned by the server in the VLVResponse control.

=item offset

Set the offset of the target entry.

=back

=head2 METHODS

As with L<Net::LDAP::Control> each constructor argument
described above is also avaliable as a method on the object which will
return the current value for the attribute if called without an argument,
and set a new value for the attribute if called with an argument.

The C<offset> and C<assert> attributes are mutually exclusive. Setting
one or the other will cause previous values set by the other to
be forgotten. The C<content> attribute is also associated with the
C<offset> attribute, so setting C<assert> will cause any C<content>
value to be forgotten.

=over 4

=item end

Set the target entry to the end of the list. This method will change the C<before>
and C<after> attributes so that the target entry is the last in the page.

=item response VLV_RESPONSE

Set the attributes in the control as per VLV_RESPONSE. VLV_RESPONSE should be a control
of type L<Net::LDAP::Control::VLVResponse> returned
from the server. C<response> will populate the C<context>, C<offset> and C<content>
attibutes of the control with the values from VLV_RESPONSE. Because this sets the
C<offset> attribute, any previous setting of the C<assert> attribute will be forgotten.

=item scroll NUM

Move the target entry by NUM entries. A positive NUM will move the target entry towards
the end of the list and a negative NUM will move the target entry towards the
start of the list. Returns the index of the new target entry, or C<undef> if the current target
is identified by an assertion.

C<scroll> may change the C<before> and C<after> attributes if the scroll value would
cause the page to go off either end of the list. But the page size will be maintained.

=item scroll_page NUM

Scroll by NUM pages. This method simple calculates the current page size and calls
C<scroll> with C<NUM * $page_size>

=item start

Set the target entry to the start of the list. This method will change the C<before> and C<after>
attributes to the the target entry is the first entry in the page.

=back

=head1 SEE ALSO

L<Net::LDAP>,
L<Net::LDAP::Control>,
L<Net::LDAP::Control::Sort>,
L<Net::LDAP::Control::VLVResponse>

=head1 AUTHOR

Graham Barr E<lt>gbarr@pobox.comE<gt>

Please report any bugs, or post any suggestions, to the perl-ldap mailing list
E<lt>perl-ldap@perl.orgE<gt>

=head1 COPYRIGHT

Copyright (c) 2000-2004 Graham Barr. All rights reserved. This program is
free software; you can redistribute it and/or modify it under the same
terms as Perl itself.

=cut
