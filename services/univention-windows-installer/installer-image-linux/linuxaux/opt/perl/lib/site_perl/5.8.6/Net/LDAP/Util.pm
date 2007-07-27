# Copyright (c) 1999-2004 Graham Barr <gbarr@pobox.com> and
# Norbert Klasen <norbert.klasen@daasi.de> All Rights Reserved.
# This program is free software; you can redistribute it and/or modify
# it under the same terms as Perl itself.

package Net::LDAP::Util;

=head1 NAME

Net::LDAP::Util - Utility functions

=head1 SYNOPSIS

  use Net::LDAP::Util qw(ldap_error_text
                         ldap_error_name
                         ldap_error_desc
                        );

  $mesg = $ldap->search( .... );

  die "Error ",ldap_error_name($mesg) if $mesg->code;

=head1 DESCRIPTION

B<Net::LDAP::Util> is a collection of utility functions for use with
the L<Net::LDAP> modules.

=head1 FUNCTIONS

=over 4

=cut

use vars qw($VERSION);
require Exporter;
require Net::LDAP::Constant;
@ISA = qw(Exporter);
@EXPORT_OK = qw(
  ldap_error_name
  ldap_error_text
  ldap_error_desc
  canonical_dn
  ldap_explode_dn
  escape_filter_value
  unescape_filter_value
  escape_dn_value
  unescape_dn_value
);
%EXPORT_TAGS = (
	error	=> [ qw(ldap_error_name ldap_error_text ldap_error_desc) ],
	filter	=> [ qw(escape_filter_value unescape_filter_value) ],
	dn    	=> [ qw(canonical_dn ldap_explode_dn
	                escape_dn_value unescape_dn_value) ],
	escape 	=> [ qw(escape_filter_value unescape_filter_value
	                escape_dn_value unescape_dn_value) ],
);

$VERSION = "0.10";

=item ldap_error_name ( ERR )

Returns the name corresponding with ERR. ERR can either be an LDAP
error number, or a C<Net::LDAP::Message> object containing an error
code. If the error is not known the a string in the form C<"LDAP error
code %d(0x%02X)"> is returned.

=cut

# Defined in Constant.pm

=item ldap_error_text ( ERR )

Returns the text from the POD description for the given error. ERR can
either be an LDAP error code, or a C<Net::LDAP::Message> object
containing an LDAP error code. If the error code given is unknown then
C<undef> is returned.

=cut

# Defined in Constant.pm

=item ldap_error_desc ( ERR )

Returns a short text description of the error. ERR can either be an
LDAP error code or a C<Net::LDAP::Message> object containing an LDAP
error code.

=cut

my @err2desc = (
  "Success",                                             # 0x00 LDAP_SUCCESS
  "Operations error",                                    # 0x01 LDAP_OPERATIONS_ERROR
  "Protocol error",                                      # 0x02 LDAP_PROTOCOL_ERROR
  "Timelimit exceeded",                                  # 0x03 LDAP_TIMELIMIT_EXCEEDED
  "Sizelimit exceeded",                                  # 0x04 LDAP_SIZELIMIT_EXCEEDED
  "Compare false",                                       # 0x05 LDAP_COMPARE_FALSE
  "Compare true",                                        # 0x06 LDAP_COMPARE_TRUE
  "Strong authentication not supported",                 # 0x07 LDAP_STRONG_AUTH_NOT_SUPPORTED
  "Strong authentication required",                      # 0x08 LDAP_STRONG_AUTH_REQUIRED
  "Partial results and referral received",               # 0x09 LDAP_PARTIAL_RESULTS
  "Referral received",                                   # 0x0a LDAP_REFERRAL
  "Admin limit exceeded",                                # 0x0b LDAP_ADMIN_LIMIT_EXCEEDED
  "Critical extension not available",                    # 0x0c LDAP_UNAVAILABLE_CRITICAL_EXT
  "Confidentiality required",                            # 0x0d LDAP_CONFIDENTIALITY_REQUIRED
  "SASL bind in progress",                               # 0x0e LDAP_SASL_BIND_IN_PROGRESS
  undef,
  "No such attribute",                                   # 0x10 LDAP_NO_SUCH_ATTRIBUTE
  "Undefined attribute type",                            # 0x11 LDAP_UNDEFINED_TYPE
  "Inappropriate matching",                              # 0x12 LDAP_INAPPROPRIATE_MATCHING
  "Constraint violation",                                # 0x13 LDAP_CONSTRAINT_VIOLATION
  "Type or value exists",                                # 0x14 LDAP_TYPE_OR_VALUE_EXISTS
  "Invalid syntax",                                      # 0x15 LDAP_INVALID_SYNTAX
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  "No such object",                                      # 0x20 LDAP_NO_SUCH_OBJECT
  "Alias problem",                                       # 0x21 LDAP_ALIAS_PROBLEM
  "Invalid DN syntax",                                   # 0x22 LDAP_INVALID_DN_SYNTAX
  "Object is a leaf",                                    # 0x23 LDAP_IS_LEAF
  "Alias dereferencing problem",                         # 0x24 LDAP_ALIAS_DEREF_PROBLEM
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  "Inappropriate authentication",                        # 0x30 LDAP_INAPPROPRIATE_AUTH
  "Invalid credentials",                                 # 0x31 LDAP_INVALID_CREDENTIALS
  "Insufficient access",                                 # 0x32 LDAP_INSUFFICIENT_ACCESS
  "DSA is busy",                                         # 0x33 LDAP_BUSY
  "DSA is unavailable",                                  # 0x34 LDAP_UNAVAILABLE
  "DSA is unwilling to perform",                         # 0x35 LDAP_UNWILLING_TO_PERFORM
  "Loop detected",                                       # 0x36 LDAP_LOOP_DETECT
  undef,
  undef,
  undef,
  undef,
  undef,
  "Sort control missing",                                # 0x3C LDAP_SORT_CONTROL_MISSING
  "Index range error",                                   # 0x3D LDAP_INDEX_RANGE_ERROR
  undef,
  undef,
  "Naming violation",                                    # 0x40 LDAP_NAMING_VIOLATION
  "Object class violation",                              # 0x41 LDAP_OBJECT_CLASS_VIOLATION
  "Operation not allowed on nonleaf",                    # 0x42 LDAP_NOT_ALLOWED_ON_NONLEAF
  "Operation not allowed on RDN",                        # 0x43 LDAP_NOT_ALLOWED_ON_RDN
  "Already exists",                                      # 0x44 LDAP_ALREADY_EXISTS
  "Cannot modify object class",                          # 0x45 LDAP_NO_OBJECT_CLASS_MODS
  "Results too large",                                   # 0x46 LDAP_RESULTS_TOO_LARGE
  "Affects multiple servers",                            # 0x47 LDAP_AFFECTS_MULTIPLE_DSAS
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  undef,
  "Unknown error",                                       # 0x50 LDAP_OTHER
  "Can't contact LDAP server",                           # 0x51 LDAP_SERVER_DOWN
  "Local error",                                         # 0x52 LDAP_LOCAL_ERROR
  "Encoding error",                                      # 0x53 LDAP_ENCODING_ERROR
  "Decoding error",                                      # 0x54 LDAP_DECODING_ERROR
  "Timed out",                                           # 0x55 LDAP_TIMEOUT
  "Unknown authentication method",                       # 0x56 LDAP_AUTH_UNKNOWN
  "Bad search filter",                                   # 0x57 LDAP_FILTER_ERROR
  "Canceled",                                            # 0x58 LDAP_USER_CANCELED
  "Bad parameter to an ldap routine",                    # 0x59 LDAP_PARAM_ERROR
  "Out of memory",                                       # 0x5a LDAP_NO_MEMORY
  "Can't connect to the LDAP server",                    # 0x5b LDAP_CONNECT_ERROR
  "Not supported by this version of the LDAP protocol",  # 0x5c LDAP_NOT_SUPPORTED
  "Requested LDAP control not found",                    # 0x5d LDAP_CONTROL_NOT_FOUND
  "No results returned",                                 # 0x5e LDAP_NO_RESULTS_RETURNED
  "More results to return",                              # 0x5f LDAP_MORE_RESULTS_TO_RETURN
  "Client detected loop",                                # 0x60 LDAP_CLIENT_LOOP
  "Referral hop limit exceeded",                         # 0x61 LDAP_REFERRAL_LIMIT_EXCEEDED
);

sub ldap_error_desc {
  my $code = (ref($_[0]) ? $_[0]->code : $_[0]);
  $err2desc[$code] || sprintf("LDAP error code %d(0x%02X)",$code,$code);
}





=item canonical_dn ( DN [ , OPTIONS ] )

Returns the given B<DN> in a canonical form. Returns undef if B<DN> is
not a valid Distinguished Name. (Note: The empty string "" is a valid DN.)
B<DN> can either be a string or reference to an array of hashes as returned by 
ldap_explode_dn, which is useful when constructing a DN.

It performs the following operations on the given B<DN>:

=over 4

=item *

Removes the leading 'OID.' characters if the type is an OID instead
of a name.

=item *

Escapes all RFC 2253 special characters (",", "+", """, "\", "E<lt>",
"E<gt>", ";", "#", "=", " "), slashes ("/"), and any other character
where the ASCII code is E<lt> 32 as \hexpair.

=item *

Converts all leading and trailing spaces in values to be \20.

=item *

If an RDN contains multiple parts, the parts are re-ordered so that
the attribute type names are in alphabetical order.

=back

B<OPTIONS> is a list of name/value pairs, valid options are:

=over 4

=item casefold

Controls case folding of attribute type names. Attribute values are not
affected by this option. The default is to uppercase. Valid values are:
	
=over 4

=item lower

Lowercase attribute type names.

=item upper

Uppercase attribute type names. This is the default.

=item none

Do not change attribute type names.

=back

=item mbcescape

If TRUE, characters that are encoded as a multi-octet UTF-8 sequence 
will be escaped as \(hexpair){2,*}.

=item reverse

If TRUE, the RDN sequence is reversed.

=item separator

Separator to use between RDNs. Defaults to comma (',').

=back

=cut

sub canonical_dn($%) {
  my ($dn, %opt) = @_;

  return $dn unless defined $dn and $dn ne '';
  
  # create array of hash representation
  my $rdns = ref($dn) eq 'ARRAY'
		? $dn
		: ldap_explode_dn( $dn )
    or return undef; #error condition
  
  # assign specified or default separator value
  my $separator = $opt{separator} || ',';

  # flatten all RDNs into strings
  my @flatrdns =
    map {
      my $rdn = $_;
      my @types = sort keys %$rdn;
      join('+',
        map {
          my $val = $rdn->{$_};
          
          if ( ref($val) ) {
            $val = '#' . unpack("H*", $$val);
          } else {
            #escape insecure characters and optionally MBCs
            if ( $opt{mbcescape} ) {
              $val =~ s/([\x00-\x1f\/\\",=+<>#;\x7f-\xff])/
                sprintf("\\%02x",ord($1))/xeg;
            } else {
              $val =~ s/([\x00-\x1f\/\\",=+<>#;])/
                sprintf("\\%02x",ord($1))/xeg;
            }
            #escape leading and trailing whitespace
            $val =~ s/(^\s+|\s+$)/
              "\\20" x length $1/xeg; 
          }
          
          # case fold attribute type and create return value
          if ( !$opt{casefold} || $opt{casefold} eq 'upper' ) {
            (uc $_)."=$val";
          } elsif ( $opt{casefold} eq 'lower' ) {
            (lc $_)."=$val";
          } else {
            "$_=$val";
          }
        } @types);
    } @$rdns;
  
  # join RDNs into string, optionally reversing order
  $opt{reverse}
    ? join($separator, reverse @flatrdns)
    : join($separator, @flatrdns);
}


=item ldap_explode_dn ( DN [ , OPTIONS ] )

Explodes the given B<DN> into an array of hashes and returns a reference to this 
array. Returns undef if B<DN> is not a valid Distinguished Name.

A Distinguished Name is a sequence of Relative Distingushed Names (RDNs), which 
themselves are sets of Attributes. For each RDN a hash is constructed with the 
attribute type names as keys and the attribute values as corresponding values. 
These hashes are then strored in an array in the order in which they appear 
in the DN.

For example, the DN 'OU=Sales+CN=J. Smith,DC=example,DC=net' is exploded to:
[
  {
    'OU' =E<gt> 'Sales',
    'CN' =E<gt> 'J. Smith'
  },
  {
    'DC' =E<gt> 'example'
  },
  {
    'DC' =E<gt> 'net'
  }
]

(RFC2253 string) DNs might also contain values, which are the bytes of the 
BER encoding of the X.500 AttributeValue rather than some LDAP string syntax. 
These values are hex-encoded and prefixed with a #. To distingush such BER 
values, ldap_explode_dn uses references to the actual values, 
e.g. '1.3.6.1.4.1.1466.0=#04024869,DC=example,DC=com' is exploded to:
[
  {
    '1.3.6.1.4.1.1466.0' =E<gt> \"\004\002Hi"
  },
  {
    'DC' =E<gt> 'example'
  },
  {
    'DC' =E<gt> 'com'
  }
];

It also performs the following operations on the given DN:

=over 4

=item *

Unescape "\" followed by ",", "+", """, "\", "E<lt>", "E<gt>", ";",
"#", "=", " ", or a hexpair and and strings beginning with "#".

=item *

Removes the leading OID. characters if the type is an OID instead
of a name.

=back

B<OPTIONS> is a list of name/value pairs, valid options are:

=over 4

=item casefold

Controls case folding of attribute types names. Attribute values are not
affected by this option. The default is to uppercase. Valid values are:
	
=over 4

=item lower

Lowercase attribute types names.

=item upper

Uppercase attribute type names. This is the default.

=item none

Do not change attribute type names.

=back

=item reverse

If TRUE, the RDN sequence is reversed.

=back

=cut

sub ldap_explode_dn($%) {
  my ($dn, %opt) = @_;
  return undef unless defined $dn;
  return [] if $dn eq '';

  my (@dn, %rdn);
  while (
  $dn =~ /\G(?:
    \s*
    ([a-zA-Z][-a-zA-Z0-9]*|(?:[Oo][Ii][Dd]\.)?\d+(?:\.\d+)*)
    \s*
    =
    \s*
    (
      (?:[^\\",=+<>\#;]*[^\\",=+<>\#;\s]|\s*\\(?:[\\ ",=+<>#;]|[0-9a-fA-F]{2}))* 
      |
      \#(?:[0-9a-fA-F]{2})+
      |
      "(?:[^\\"]+|\\(?:[\\",=+<>#;]|[0-9a-fA-F]{2}))*"
    )
    \s*
    (?:([;,+])\s*(?=\S)|$)
    )\s*/gcx)
  {
    my($type,$val,$sep) = ($1,$2,$3);

    $type =~ s/^oid\.(\d+(\.\d+)*)$/$1/i; #remove leading "oid."

    if ( !$opt{casefold} || $opt{casefold} eq 'upper' ) {
      $type = uc $type;
    } elsif ( $opt{casefold} eq 'lower' ) {
      $type = lc($type);
    }

    if ( $val =~ s/^#// ) {
      # decode hex-encoded BER value
      my $tmp = pack('H*', $val);
      $val = \$tmp;
    } else {
      # remove quotes
      $val =~ s/^"(.*)"$/$1/;
      # unescape characters
      $val =~ s/\\([\\ ",=+<>#;]|[0-9a-fA-F]{2}) 
           /length($1)==1 ? $1 : chr(hex($1))
           /xeg; 
    }

    $rdn{$type} = $val;

    unless (defined $sep and $sep eq '+') {
      if ( $opt{reverse} ) {
        unshift @dn, { %rdn };
      } else {
        push @dn, { %rdn };
      }
      %rdn = ();
    }
  }

  length($dn) == (pos($dn)||0)
    ? \@dn
    : undef;
}


=item escape_filter_value ( VALUES )

Escapes the given B<VALUES> according to RFC 2254 so that they
can be safely used in LDAP filters.

Any control characters with an ACII code E<lt> 32 as well as the
characters with special meaning in LDAP filters "*", "(", ")",
and "\" the backslash are converted into the representation
of a backslash followed by two hex digits representing the
hexadecimal value of the character.

Returns the converted list in list mode and the first element
in scalar mode.

=cut

## convert a list of values into its LDAP filter encoding ##
# Synopsis:  @escaped = escape_filter_value(@values)
sub escape_filter_value(@)
{
my @values = @_;

  map { $_ =~ s/([\x00-\x1F\*\(\)\\])/"\\".unpack("H2",$1)/oge; } @values;

  return(wantarray ? @values : $values[0]);
}


=item unescape_filter_value ( VALUES )

Undoes the conversion done by B<escape_filter_value()>.

Converts any sequences of a backslash followed by two hex digits
into the corresponding character.

Returns the converted list in list mode and the first element
in scalar mode.

=cut

## convert a list of values from its LDAP filter encoding ##
# Synopsis:  @values = unescape_filter_value(@escaped)
sub unescape_filter_value(@)
{
my @values = @_;

  map { $_ =~ s/\\([0-9a-fA-F]{2})/pack("H2",$1)/oge; } @values;

  return(wantarray ? @values : $values[0]);
}


=item escape_dn_value ( VALUES )

Escapes the given B<VALUES> according to RFC 2253 so that they
can be safely used in LDAP DNs.

The characters ",", "+", """, "\", "E<lt>", "E<gt>", ";", "#", "="
with a special meaning in RFC 2252 are preceeded by ba backslash.
Control characters with an ASCII code E<lt> 32 are represented
as \hexpair.
Finally all leading and trailing spaces are converted to
sequences of \20.

Returns the converted list in list mode and the first element
in scalar mode.

=cut

## convert a list of values into its DN encoding ##
# Synopsis:  @escaped = escape_dn_value(@values)
sub escape_dn_value(@)
{
my @values = @_;

  map { $_ =~ s/([\\",=+<>#;])/\\$1/og;
        $_ =~ s/([\x00-\x1F])/"\\".unpack("H2",$1)/oge;
        $_ =~ s/(^\s+|\s+$)/"\\20" x length($1)/oge; } @values;

  return(wantarray ? @values : $values[0]);
}


=item unescape_dn_value ( VALUES )

Undoes the conversion done by B<escape_dn_value()>.

Any escape sequence starting with a baskslash - hexpair or
special character - will be transformed back to the
corresponding character.

Returns the converted list in list mode and the first element
in scalar mode.

=cut

## convert a list of values from its LDAP filter encoding ##
# Synopsis:  @values = unescape_dn_value(@escaped)
sub unescape_dn_value(@)
{
my @values = @_;

  map { $_ =~ s/\\([\\",=+<>#;]|[0-9a-fA-F]{2})
               /(length($1)==1) ? $1 : pack("H2",$1)
               /ogex; } @values;

  return(wantarray ? @values : $values[0]);
}


=back


=head1 AUTHOR

Graham Barr E<lt>gbarr@pobox.comE<gt>

=head1 COPYRIGHT

Copyright (c) 1999-2004 Graham Barr. All rights reserved. This program is
free software; you can redistribute it and/or modify it under the same
terms as Perl itself.

ldap_explode_dn and canonical_dn also

(c) 2002 Norbert Klasen, norbert.klasen@daasi.de, All Rights Reserved.

=cut

1;
