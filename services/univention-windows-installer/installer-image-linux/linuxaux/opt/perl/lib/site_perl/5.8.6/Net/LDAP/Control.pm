# Copyright (c) 1999-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Control;

use vars qw($VERSION);
use strict;

use Net::LDAP::Constant qw(
  LDAP_CONTROL_SORTREQUEST
  LDAP_CONTROL_SORTRESULT
  LDAP_CONTROL_VLVREQUEST
  LDAP_CONTROL_VLVRESPONSE
  LDAP_CONTROL_PAGED
  LDAP_CONTROL_PROXYAUTHENTICATION
  LDAP_CONTROL_MANAGEDSAIT
  LDAP_CONTROL_PERSISTENTSEARCH
  LDAP_CONTROL_ENTRYCHANGE
);

$VERSION = "0.05";

my %Pkg2Type = (

  'Net::LDAP::Control::Sort'		=> LDAP_CONTROL_SORTREQUEST,
  'Net::LDAP::Control::SortResult' 	=> LDAP_CONTROL_SORTRESULT,

  'Net::LDAP::Control::VLV'		=> LDAP_CONTROL_VLVREQUEST,
  'Net::LDAP::Control::VLVResponse'	=> LDAP_CONTROL_VLVRESPONSE,

  'Net::LDAP::Control::Paged'		=> LDAP_CONTROL_PAGED,

  'Net::LDAP::Control::ProxyAuth'	=> LDAP_CONTROL_PROXYAUTHENTICATION,


  'Net::LDAP::Control::ManageDsaIT'	=> LDAP_CONTROL_MANAGEDSAIT,
  'Net::LDAP::Control::PersistentSearch'	=> LDAP_CONTROL_PERSISTENTSEARCH,
  'Net::LDAP::Control::EntryChange'	=> LDAP_CONTROL_ENTRYCHANGE,
  #
  #LDAP_CONTROL_PWEXPIRED
  #LDAP_CONTROL_PWEXPIRING
  #
  #LDAP_CONTROL_REFERRALS
);

my %Type2Pkg = reverse %Pkg2Type;

sub register {
  my($class,$oid) = @_;

  require Carp and Carp::croak("$oid is already registered to $Type2Pkg{$oid}")
    if exists $Type2Pkg{$oid} and $Type2Pkg{$oid} ne $class;

  require Carp and Carp::croak("$class is already registered to $Pkg2Type{$class}")
    if exists $Pkg2Type{$class} and $Pkg2Type{$class} ne $oid;

  $Type2Pkg{$oid} = $class;
  $Pkg2Type{$class} = $oid;
}

sub new {
  my $self = shift;
  my $pkg  = ref($self) || $self;
  my $oid  = (@_ & 1) ? shift : undef;
  my %args = @_;

  $args{'type'} ||= $oid || $Pkg2Type{$pkg} || '';

  unless ($args{type} =~ /^\d+(?:\.\d+)+$/) {
    $args{error} = 'Invalid OID';
    return bless \%args;
  }

  if ($pkg eq __PACKAGE__ and exists $Type2Pkg{$args{type}}) {
    $pkg = $Type2Pkg{$args{type}};
    eval "require $pkg" or die $@;
  }

  delete $args{error};

  bless(\%args, $pkg)->init;
}


sub from_asn {
  my $self = shift;
  my $asn = shift;
  my $class = ref($self) || $self;

  if ($class eq __PACKAGE__ and exists $Type2Pkg{$asn->{type}}) {
    $class = $Type2Pkg{$asn->{type}};
    eval "require $class" or die $@;
  }

  delete $asn->{error};

  bless($asn, $class)->init;
}

sub to_asn {
  my $self = shift;
  $self->value; # Ensure value is there
  delete $self->{critical} unless $self->{critical};
  $self;
}

sub critical {
  my $self = shift;
  $self->{critical} = shift if @_;
  $self->{critical} || 0;
}

sub value    {
  my $self = shift;
  $self->{value} = shift if @_;
  $self->{value} || undef
}

sub type  { shift->{type} }
sub valid { ! exists shift->{error} }
sub error { shift->{error} }
sub init  { shift }

1;

__END__


=head1 NAME

Net::LDAP::Control - LDAPv3 control object base class

=head1 SYNOPSIS

 use Net::LDAP::Control;
 use Net::LDAP::Constant qw( LDAP_CONTROL_MATCHEDVALS );

 $ctrl = Net::LDAP::Control->new(
   type     => "1.2.3.4",
   value    => "help",
   critical => 0
 );

 $mesg = $ldap->search( @args, control => [ $ctrl ]);

 $ctrl = Net::LDAP::Control->new( type => LDAP_CONTROL_MATCHEDVALS );

=head1 DESCRIPTION

C<Net::LDAP::Control> is a base-class for LDAPv3 control objects.

=cut

##
## Need more blurb in here about controls
##

=head1 CONSTRUCTORS

=over 4

=item new ( ARGS )

ARGS is a list of name/value pairs, valid arguments are.

=over 4

=item critical

A booloean value, if TRUE and the control is unrecognized by the server or
is inappropriate for the requested operation then the server will return
an error and the operation will not be performed.

If FALSE and the control is unrecognized by the server or
is inappropriate for the requested operation then the server will ignore
the control and perform the requested operation as if the control was
not given.

If absent, FALSE is assumed.

=item type

A dotted-decimal representation of an OBJECT IDENTIFIER which
uniquely identifies the control. This prevents conflicts between
control names.

This may be ommitted if the contructor is being called on a sub-class of
Net::LDAP::Control which has registered to be associated with an OID.
If the contructor is being called on the Net::LDAP::Control
package, then this argument must be given.  If the given OID has been
registered by a package, then the returned object will be of the type
registered to handle that OID.

=item value

Optional information associated with the control. It's format is specific
to the particular control.

=back

=item from_asn ( ASN )

ASN is a HASH reference, normally extracted from a PDU. It will contain
a C<type> element and optionally C<critical> and C<value> elements. On
return ASN will be blessed into a package. If C<type> is a registered
OID, then ASN will be blessed into the registered package, if not then ASN
will be blessed into Net::LDAP::Control.

This constructor is used internally by Net::LDAP and assumes that HASH
passed contains a valid control. It should be used with B<caution>.

=back

=head1 METHODS

In addition to the methods listed below, each of the named parameters
to C<new> is also avaliable as a method. C<type> will return the OID of
the control object. C<value> and C<critical> are set/get methods and will
return the current value for each attribute if called without arguments,
but may also be called with arguments to set new values.

=over 4

=item error ()

If there has been an error returns a description of the error, otherwise it will
return C<undef>

=item init ()

C<init> will be called as the last step in both contructors. What it does will depend
on the sub-class. It must always return the object.

=item register ( OID )

C<register> is provided for sub-class implementors. It should be called as a class method
on a sub-class of Net::LDAP::Control with the OID that the class will handle. Net::LDAP::Control
will remember this class and OID pair and use it in the following
situations.

=over 4

=item *

C<new> is called as a class method on the Net::LDAP::Control package and OID is passed
as the type. The returned object will be blessed into the package that registered
the OID.

=item *

C<new> is called as a class method on a registered package and the C<type> is not
specified. The C<type> will be set to the OID registered by that package.

=item *

C<from_asn> is called to construct an object from ASN. The returned object will be
blessed into the package which was registered to handle the OID in the ASN.

=back

=item ( to_asn )

Returns a structure suitable for passing to Convert::ASN1 for
encoding. This method will be called by L<Net::LDAP> when the
control is used.

The base class implementation of this method will call the C<value> method
without arguments to allow a sub-class to encode it's value. Sub-classes
should not need to override this method.

=item valid ()

Returns true if the object is valid and can be encoded. The default implementation
for this method is to return TRUE if there is no error, but sub-classes may override that.

=back

=head1 SEE ALSO

L<Net::LDAP>

=head1 AUTHOR

Graham Barr E<lt>gbarr@pobox.comE<gt>

Please report any bugs, or post any suggestions, to the perl-ldap mailing list
E<lt>perl-ldap@perl.orgE<gt>

=head1 COPYRIGHT

Copyright (c) 1999-2004 Graham Barr. All rights reserved. This program is
free software; you can redistribute it and/or modify it under the same
terms as Perl itself.

=cut
