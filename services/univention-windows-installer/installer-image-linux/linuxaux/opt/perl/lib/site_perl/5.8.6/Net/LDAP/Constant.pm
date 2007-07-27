# Copyright (c) 1998-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Constant;

$VERSION = "0.03";

use Carp;

my %const;

sub import {
  shift;
  my $callpkg = caller(0);
  _find(@_);
  my $oops;
  my $all = grep /:all/, @_;
  foreach my $sym ($all ? keys %const : @_) {
    if (my $sub = $const{$sym}) {
      *{$callpkg . "::$sym"} = $sub;
    }
    else {
      ++$oops;
      carp(qq["$sym" is not exported by the Net::LDAP::Constant module]);
    }
  }
  croak("Can't continue after import errors") if $oops;
}

sub _find {
  if (my @need = grep { ! $const{$_} } @_) {
    my %need; @need{@need} = ();
    my $all = exists $need{':all'};
    seek(DATA,0,0);
    local $/=''; # paragraph mode
    local $_;
    while(<DATA>) {
      next unless /^=item\s+(LDAP_\S+)\s+\((.*)\)/ and ($all or exists $need{$1});
      my ($name, $value) = ($1,$2);
      delete $need{$name};
      $const{$name} = sub () { $value };
      last unless keys %need;
    }
  }
  @const{@_};
}

sub AUTOLOAD {
  (my $name = $AUTOLOAD) =~ s/^.*:://;
  my $sub = _find($name) or croak("Undefined subroutine &$AUTOLOAD");
  my $val = &$sub; # Avoid prototype error caused by *$AUTOLOAD = $sub
  *$AUTOLOAD = sub { $val };
  goto &$AUTOLOAD;
}

# These subs are really in Net::LDAP::Util, but need to access <DATA>
# so its easier for them to be here.

my @err2name;

sub Net::LDAP::Util::ldap_error_name {
  my $code = 0 + (ref($_[0]) ? $_[0]->code : $_[0]);

  unless (@err2name) {
    seek(DATA,0,0);
    local $/=''; # paragraph mode
    local $_;
    my $n = -1;
    while(<DATA>) {
      last if /^=head2/ and ++$n;
      next if $n;
      $err2name[$2] = $1 if /^=item\s+(LDAP_\S+)\s+\((\d+)\)/;
    }
  }
  $err2name[$code] || sprintf("LDAP error code %d(0x%02X)",$code,$code);
}


sub Net::LDAP::Util::ldap_error_text {
  my $code = 0 + (ref($_[0]) ? $_[0]->code : $_[0]);
  my $text;

  seek(DATA,0,0);
  local $/=''; # paragraph mode
  local $_;
  my $n = -1;
  while(<DATA>) {
    last if /^=head2/ and ++$n;
    next if $n;
    if (/^=item\s+(LDAP_\S+)\s+\((\d+)\)/) {
      last if defined $text;
      $text = '' if $2 == $code;
    }
    elsif (defined $text) {
      $text .= $_;
    }
  }

  if (defined $text) {
    # Do some cleanup. Really should use a proper pod parser here.

    $text =~ s/^=item\s+\*\s+/ * /msg;
    $text =~ s/^=(over\s*\d*|back)//msg;
    $text =~ s/ +\n//g;
    $text =~ s/\n\n+/\n\n/g;
    $text =~ s/\n+\Z/\n/ if defined $text;
  }

  return $text;
}

1;

__DATA__

=head1 NAME

Net::LDAP::Constant - Constants for use with Net::LDAP

=head1 SYNOPSIS

 use Net::LDAP qw(LDAP_SUCCESS LDAP_PROTOCOL_ERROR);

=head1 DESCRIPTION

B<Net::LDAP::Constant> exports constant subroutines for the following LDAP
error codes.

=head2 Protocol Constants

=over 4

=item LDAP_SUCCESS (0)

Operation completed without error

=item LDAP_OPERATIONS_ERROR (1)

Server encountered an internal error

=item LDAP_PROTOCOL_ERROR (2)

Unrecognized version number or incorrect PDU structure

=item LDAP_TIMELIMIT_EXCEEDED (3)

The time limit on a search operation has been exceeded

=item LDAP_SIZELIMIT_EXCEEDED (4)

The maximum number of search results to return has been exceeded.

=item LDAP_COMPARE_FALSE (5)

This code is returned when a compare request completes and the attribute value
given is not in the entry specified

=item LDAP_COMPARE_TRUE (6)

This code is returned when a compare request completes and the attribute value
given is in the entry specified

=item LDAP_AUTH_METHOD_NOT_SUPPORTED (7)

Unrecognized SASL mechanism name

=item LDAP_STRONG_AUTH_NOT_SUPPORTED (7)

Unrecognized SASL mechanism name

=item LDAP_STRONG_AUTH_REQUIRED (8)

The server requires authentication be performed with a SASL mechanism

=item LDAP_PARTIAL_RESULTS (9)

Returned to version 2 clients when a referral is returned. The response
will contain a list of URL's for other servers.

=item LDAP_REFERRAL (10)

The server is referring the client to another server. The response will
contain a list of URL's

=item LDAP_ADMIN_LIMIT_EXCEEDED (11)

The server has exceed the maximum number of entries to search while gathering
a list of search result candidates

=item LDAP_UNAVAILABLE_CRITICAL_EXT (12)

A control or matching rule specified in the request is not supported by
the server

=item LDAP_CONFIDENTIALITY_REQUIRED (13)

This result code is returned when confidentiality is required to perform
a given operation

=item LDAP_SASL_BIND_IN_PROGRESS (14)

The server requires the client to send a new bind request, with the same SASL
mechanism, to continue the authentication process

=item LDAP_NO_SUCH_ATTRIBUTE (16)

The request referenced an attribute that does not exist

=item LDAP_UNDEFINED_TYPE (17)

The request contains an undefined attribute type

=item LDAP_INAPPROPRIATE_MATCHING (18)

An extensible matching rule in the given filter does not apply to the specified
attribute

=item LDAP_CONSTRAINT_VIOLATION (19)

The request contains a value which does not meet with certain constraints.
This result can be returned as a consequence of

=over 4

=item *

The request was to add or modify a user password, and the password fails to
meet the criteria the server is configured to check. This could be that the
password is too short, or a recognizable word (e.g. it matches one of the
attributes in the users entry) or it matches a previous password used by
the same user.

=item *

The request is a bind request to a user account that has been locked

=back

=item LDAP_TYPE_OR_VALUE_EXISTS (20)

The request attempted to add an attribute type or value that already exists

=item LDAP_INVALID_SYNTAX (21)

Some part of the request contained an invalid syntax. It could be a search
with an invalid filter or a request to modify the schema and the given
schema has a bad syntax.

=item LDAP_NO_SUCH_OBJECT (32)

The server cannot find an object specified in the request

=item LDAP_ALIAS_PROBLEM (33)

Server encountered a problem while attempting to dereference an alias

=item LDAP_INVALID_DN_SYNTAX (34)

The request contained an invalid DN

=item LDAP_IS_LEAF (35)

The specified entry is a leaf entry

=item LDAP_ALIAS_DEREF_PROBLEM (36)

Server encountered a problem while attempting to dereference an alias

=item LDAP_INAPPROPRIATE_AUTH (48)

The server requires the client which had attempted to bind anonymously or
without supplying credentials to provide some form of credentials

=item LDAP_INVALID_CREDENTIALS (49)

The wrong password was supplied or the SASL credentials could not be processed

=item LDAP_INSUFFICIENT_ACCESS (50)

The client does not have sufficient access to perform the requested
operation

=item LDAP_BUSY (51)

The server is too busy to perform requested operation

=item LDAP_UNAVAILABLE (52)

The server in unavailable to perform the request, or the server is
shutting down

=item LDAP_UNWILLING_TO_PERFORM (53)

The server is unwilling to perform the requested operation

=item LDAP_LOOP_DETECT (54)

The server was unable to perform the request due to an internal loop detected

=item LDAP_SORT_CONTROL_MISSING (60)

The search contained a "virtual list view" control, but not a server-side
sorting control, which is required when a "virtual list view" is given.

=item LDAP_INDEX_RANGE_ERROR (61)

The search contained a control for a "virtual list view" and the results
exceeded the range specified by the requested offsets.

=item LDAP_NAMING_VIOLATION (64)

The request violates the structure of the DIT

=item LDAP_OBJECT_CLASS_VIOLATION (65)

The request specifies a change to an existing entry or the addition of a new
entry that does not comply with the servers schema

=item LDAP_NOT_ALLOWED_ON_NONLEAF (66)

The requested operation is not allowed on an entry that has child entries

=item LDAP_NOT_ALLOWED_ON_RDN (67)

The requested operation ill affect the RDN of the entry

=item LDAP_ALREADY_EXISTS (68)

The client attempted to add an entry that already exists. This can occur as
a result of

=over 4

=item *

An add request was submitted with a DN that already exists

=item *

A modify DN requested was submitted, where the requested new DN already exists

=item *

The request is adding an attribute to the schema and an attribute with the
given OID or name already exists

=back

=item LDAP_NO_OBJECT_CLASS_MODS (69)

Request attempt to modify the object class of an entry that should not be
modified

=item LDAP_RESULTS_TOO_LARGE (70)

The results of the request are to large

=item LDAP_AFFECTS_MULTIPLE_DSAS (71)

The requested operation needs to be performed on multiple servers where
the requested operation is not permitted

=item LDAP_OTHER (80)

An unknown error has occurred

=item LDAP_SERVER_DOWN (81)

C<Net::LDAP> cannot establish a connection or the connection has been lost

=item LDAP_LOCAL_ERROR (82)

An error occurred in C<Net::LDAP>

=item LDAP_ENCODING_ERROR (83)

C<Net::LDAP> encountered an error while encoding the request packet that would
have been sent to the server

=item LDAP_DECODING_ERROR (84)

C<Net::LDAP> encountered an error while decoding a response packet from
the server.

=item LDAP_TIMEOUT (85)

C<Net::LDAP> timeout while waiting for a response from the server

=item LDAP_AUTH_UNKNOWN (86)

The method of authentication requested in a bind request is unknown to
the server

=item LDAP_FILTER_ERROR (87)

An error occurred while encoding the given search filter.

=item LDAP_USER_CANCELED (88)

The user canceled the operation

=item LDAP_PARAM_ERROR (89)

An invalid parameter was specified

=item LDAP_NO_MEMORY (90)

Out of memory error

=item LDAP_CONNECT_ERROR (91)

A connection to the server could not be established

=item LDAP_NOT_SUPPORTED (92)

An attempt has been made to use a feature not supported by Net::LDAP

=item LDAP_CONTROL_NOT_FOUND (93)

The controls required to perform the requested operation were not
found.

=item LDAP_NO_RESULTS_RETURNED (94)

No results were returned from the server.

=item LDAP_MORE_RESULTS_TO_RETURN (95)

There are more results in the chain of results.

=item LDAP_CLIENT_LOOP (96)

A loop has been detected. For example when following referals.

=item LDAP_REFERRAL_LIMIT_EXCEEDED (97)

The referral hop limit has been exceeded.

=back

=head2 Control OIDs

=item LDAP_CONTROL_SORTREQUEST (1.2.840.113556.1.4.473)

=item LDAP_CONTROL_SORTRESULT (1.2.840.113556.1.4.474)

=item LDAP_CONTROL_VLVREQUEST (2.16.840.1.113730.3.4.9)

=item LDAP_CONTROL_VLVRESPONSE (2.16.840.1.113730.3.4.10)

=item LDAP_CONTROL_PROXYAUTHENTICATION (2.16.840.1.113730.3.4.12)

=item LDAP_CONTROL_PAGED (1.2.840.113556.1.4.319)

=item LDAP_CONTROL_TREE_DELETE (1.2.840.113556.1.4.805)

=item LDAP_CONTROL_MATCHEDVALS (1.2.826.0.1.3344810.2.2)

=item LDAP_CONTROL_MANAGEDSAIT (2.16.840.1.113730.3.4.2)

=item LDAP_CONTROL_PERSISTENTSEARCH (2.16.840.1.113730.3.4.3)

=item LDAP_CONTROL_ENTRYCHANGE (2.16.840.1.113730.3.4.7)

=item LDAP_CONTROL_PWEXPIRED (2.16.840.1.113730.3.4.4)

=item LDAP_CONTROL_PWEXPIRING (2.16.840.1.113730.3.4.5)

=item LDAP_CONTROL_REFERRALS (1.2.840.113556.1.4.616)

=head2 Extension OIDs

B<Net::LDAP::Constant> exports constant subroutines for the following LDAP
extension OIDs.

=over 4

=item LDAP_EXTENSION_START_TLS (1.3.6.1.4.1.1466.20037)

Indicates if the server supports the Start TLS extension (RFC 2830)

=item LDAP_EXTENSION_PASSWORD_MODIFY (1.3.6.1.4.1.4203.1.11.1)

Indicates that the server supports the Password Modify extension (RFC 3062)

=back

=head1 SEE ALSO

L<Net::LDAP>,
L<Net::LDAP::Message>

=head1 AUTHOR

Graham Barr E<lt>gbarr@pobox.comE<gt>

Please report any bugs, or post any suggestions, to the perl-ldap mailing list
E<lt>perl-ldap@perl.orgE<gt>

=head1 COPYRIGHT

Copyright (c) 1998-2004 Graham Barr. All rights reserved. This program is
free software; you can redistribute it and/or modify it under the same
terms as Perl itself.

=cut
