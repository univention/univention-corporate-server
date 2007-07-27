# Copyright (c) 1997-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Filter;

use strict;
use vars qw($VERSION);

$VERSION = "0.14";

# filter       = "(" filtercomp ")"
# filtercomp   = and / or / not / item
# and          = "&" filterlist
# or           = "|" filterlist
# not          = "!" filter
# filterlist   = 1*filter
# item         = simple / present / substring / extensible
# simple       = attr filtertype value
# filtertype   = equal / approx / greater / less
# equal        = "="
# approx       = "~="
# greater      = ">="
# less         = "<="
# extensible   = attr [":dn"] [":" matchingrule] ":=" value
#                / [":dn"] ":" matchingrule ":=" value
# present      = attr "=*"
# substring    = attr "=" [initial] any [final]
# initial      = value
# any          = "*" *(value "*")
# final        = value
# attr         = AttributeDescription from Section 4.1.5 of [1]
# matchingrule = MatchingRuleId from Section 4.1.9 of [1]
# value        = AttributeValue from Section 4.1.6 of [1]
# 
# Special Character encodings
# ---------------------------
#    *               \2a, \*
#    (               \28, \(
#    )               \29, \)
#    \               \5c, \\
#    NUL             \00

my $ErrStr;

sub new {
  my $self = shift;
  my $class = ref($self) || $self;
  
  my $me = bless {}, $class;

  if (@_) {
    $me->parse(shift) or
      return undef;
  }
  $me;
}

my $Attr  = '[-;.:\d\w]*[-;\d\w]';

my %Op = qw(
  &   and
  |   or
  !   not
  =   equalityMatch
  ~=  approxMatch
  >=  greaterOrEqual
  <=  lessOrEqual
  :=  extensibleMatch
);

my %Rop = reverse %Op;

# Unescape
#   \xx where xx is a 2-digit hex number
#   \y  where y is one of ( ) \ *

sub errstr { $ErrStr }

sub _unescape {
  $_[0] =~ s/
	     \\([\da-fA-F]{2}|.)
	    /
	     length($1) == 1
	       ? $1
	       : chr(hex($1))
	    /soxeg;
  $_[0];
}

sub _escape { (my $t = $_[0]) =~ s/([\\\(\)\*\0-\37])/sprintf("\\%02x",ord($1))/sge; $t }

sub _encode {
  my($attr,$op,$val) = @_;

  # An extensible match

  if ($op eq ':=') {

    # attr must be in the form type:dn:1.2.3.4
    unless ($attr =~ /^([-;\d\w]*)(:dn)?(:(\w+|[.\d]+))?$/) {
      $ErrStr = "Bad attribute $attr";
      return undef;
    }
    my($type,$dn,$rule) = ($1,$2,$4);

    return ( {
      extensibleMatch => {
	matchingRule => $rule,
	type         => length($type) ? $type : undef,
	matchValue   => _unescape($val), 
	dnAttributes => $dn ? 1 : undef
      }
    });
  }

  # If the op is = and contains one or more * not
  # preceeded by \ then do partial matches

  if ($op eq '=' && $val =~ /^(\\.|[^\\*]+)*\*/o ) {

    my $n = [];
    my $type = 'initial';

    while ($val =~ s/^((\\.|[^\\*]+)*)\*//) {
      push(@$n, { $type, _unescape("$1") })         # $1 is readonly, copy it
	if length($1) or $type eq 'any';

      $type = 'any';
    }

    push(@$n, { 'final', _unescape($val) })
      if length $val;

    return ({
      substrings => {
	type       => $attr,
	substrings => $n
      }
    });
  }

  # Well we must have an operator and no un-escaped *'s on the RHS

  return {
    $Op{$op} => {
      attributeDesc => $attr, assertionValue =>  _unescape($val)
    }
  };
}

sub parse {
  my $self   = shift;
  my $filter = shift;

  my @stack = ();   # stack
  my $cur   = [];
  my $op;

  undef $ErrStr;

  # a filter is required
  if (!defined $filter) {
    $ErrStr = "Undefined filter";
    return undef;
  }

  # Algorithm depends on /^\(/;
  $filter =~ s/^\s*//;

  $filter = "(" . $filter . ")"
    unless $filter =~ /^\(/;

  while (length($filter)) {

    # Process the start of  (& (...)(...))

    if ($filter =~ s/^\(\s*([&!|])\s*//) {
      push @stack, [$op,$cur];
      $op = $1;
      $cur = [];
      next;
    }

    # Process the end of  (& (...)(...))

    elsif ($filter =~ s/^\)\s*//o) {
      unless (@stack) {
	$ErrStr = "Bad filter, unmatched )";
	return undef;
      }
      my($myop,$mydata) = ($op,$cur);
      ($op,$cur) = @{ pop @stack };
	# Need to do more checking here
      push @$cur, { $Op{$myop} => $myop eq '!' ? $mydata->[0] : $mydata };
      next if @stack;
    }
    
    # present is a special case (attr=*)

    elsif ($filter =~ s/^\(\s*($Attr)=\*\)\s*//o) {
      push(@$cur, { present => $1 } );
      next if @stack;
    }

    # process (attr op string)

    elsif ($filter =~ s/^\(\s*
                        ($Attr)\s*
                        ([:~<>]?=)
                        ((?:\\.|[^\\()]+)*)
                        \)\s*
                       //xo) {
      push(@$cur, _encode($1,$2,$3));
      next if @stack;
    }

    # If we get here then there is an error in the filter string
    # so exit loop with data in $filter
    last;
  }

  if (length $filter) {
    # If we have anything left in the filter, then there is a problem
    $ErrStr = "Bad filter, error before " . substr($filter,0,20);
    return undef;
  }
  if (@stack) {
    $ErrStr = "Bad filter, unmatched (";
    return undef;
  }

  %$self = %{$cur->[0]};

  $self;
}

sub print {
  my $self = shift;
  no strict 'refs'; # select may return a GLOB name
  my $fh = @_ ? shift : select;

  print $fh $self->as_string,"\n";
}

sub as_string { _string(%{$_[0]}) }

sub _string {    # prints things of the form (<op> (<list>) ... )
  my $i;
  my $str = "";

  for ($_[0]) {
    /^and/ and return "(&" . join("", map { _string(%$_) } @{$_[1]}) . ")";
    /^or/  and return "(|" . join("", map { _string(%$_) } @{$_[1]}) . ")";
    /^not/ and return "(!" . _string(%{$_[1]}) . ")";
    /^present/ and return "($_[1]=*)";
    /^(equalityMatch|greaterOrEqual|lessOrEqual|approxMatch)/
      and return "(" . $_[1]->{attributeDesc} . $Rop{$1} . _escape($_[1]->{assertionValue})  .")";
    /^substrings/ and do {
      my $str = join("*", "",map { _escape($_) } map { values %$_ } @{$_[1]->{substrings}});
      $str =~ s/^.// if exists $_[1]->{substrings}[0]{initial};
      $str .= '*' unless exists $_[1]->{substrings}[-1]{final};
      return "($_[1]->{type}=$str)";
    };
    /^extensibleMatch/ and do {
      my $str = "(";
      $str .= $_[1]->{type} if defined $_[1]->{type};
      $str .= ":dn" if $_[1]->{dnAttributes};
      $str .= ":$_[1]->{matchingRule}" if defined $_[1]->{matchingRule};
      $str .= ":=" . _escape($_[1]->{matchValue}) . ")";
      return $str;
    };
  }

  die "Internal error $_[0]";
}

1;
