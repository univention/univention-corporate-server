# Copyright (c) 2000-2002 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Convert::ASN1;

# $Id: _encode.pm,v 1.1.2.1 2007/03/08 09:08:01 jmm Exp $

BEGIN {
  unless (CHECK_UTF8) {
    local $SIG{__DIE__};
    eval { require bytes } and 'bytes'->import
  }
}

# These are the subs which do the encoding, they are called with
# 0      1    2       3     4     5
# $opt, $op, $stash, $var, $buf, $loop
# The order in the array must match the op definitions above

my @encode = (
  sub { die "internal error\n" },
  \&_enc_boolean,
  \&_enc_integer,
  \&_enc_bitstring,
  \&_enc_string,
  \&_enc_null,
  \&_enc_object_id,
  \&_enc_real,
  \&_enc_sequence,
  \&_enc_sequence, # SET is the same encoding as sequence
  \&_enc_time,
  \&_enc_time,
  \&_enc_utf8,
  \&_enc_any,
  \&_enc_choice,
  \&_enc_object_id,
);


sub _encode {
  my ($optn, $ops, $stash, $path) = @_;
  my $var;

  foreach my $op (@{$ops}) {
    if (defined(my $opt = $op->[cOPT])) {
      next unless defined $stash->{$opt};
    }
    if (defined($var = $op->[cVAR])) {
      push @$path, $var;
      require Carp, Carp::croak(join(".", @$path)," is undefined")  unless defined $stash->{$var};
    }
    $_[4] .= $op->[cTAG];

    &{$encode[$op->[cTYPE]]}(
      $optn,
      $op,
      (UNIVERSAL::isa($stash, 'HASH')
	? ($stash, defined($var) ? $stash->{$var} : undef)
	: ({}, $stash)),
      $_[4],
      $op->[cLOOP],
      $path,
    );

    pop @$path if defined $var;
  }

  $_[4];
}


sub _enc_boolean {
# 0      1    2       3     4     5      6
# $optn, $op, $stash, $var, $buf, $loop, $path

  $_[4] .= pack("CC",1, $_[3] ? 0xff : 0);
}


sub _enc_integer {
# 0      1    2       3     4     5      6
# $optn, $op, $stash, $var, $buf, $loop, $path
  if (abs($_[3]) >= 2**31) {
    my $os = i2osp($_[3], ref($_[3]) || $_[0]->{encode_bigint} || 'Math::BigInt');
    my $len = length $os;
    my $msb = (vec($os, 0, 8) & 0x80) ? 0 : 255;
    $len++, $os = chr($msb) . $os if $msb xor $_[3] > 0;
    $_[4] .= asn_encode_length($len);
    $_[4] .= $os;
  }
  else {
    my $val = int($_[3]);
    my $neg = ($val < 0);
    my $len = num_length($neg ? ~$val : $val);
    my $msb = $val & (0x80 << (($len - 1) * 8));

    $len++ if $neg ? !$msb : $msb;

    $_[4] .= asn_encode_length($len);
    $_[4] .= substr(pack("N",$val), -$len);
  }
}


sub _enc_bitstring {
# 0      1    2       3     4     5      6
# $optn, $op, $stash, $var, $buf, $loop, $path
  my $vref = ref($_[3]) ? \($_[3]->[0]) : \$_[3];

  if (CHECK_UTF8 and Encode::is_utf8($$vref)) {
    utf8::encode(my $tmp = $$vref);
    $vref = \$tmp;
  }

  if (ref($_[3])) {
    my $less = (8 - ($_[3]->[1] & 7)) & 7;
    my $len = ($_[3]->[1] + 7)/8;
    $_[4] .= asn_encode_length(1+$len);
    $_[4] .= chr($less);
    $_[4] .= substr($$vref, 0, $len);
    if ($less && $len) {
      substr($_[4],-1) &= chr((0xff << $less) & 0xff);
    }
  }
  else {
    $_[4] .= asn_encode_length(1+length $$vref);
    $_[4] .= chr(0);
    $_[4] .= $$vref;
  }
}


sub _enc_string {
# 0      1    2       3     4     5      6
# $optn, $op, $stash, $var, $buf, $loop, $path

  if (CHECK_UTF8 and Encode::is_utf8($_[3])) {
    utf8::encode(my $tmp = $_[3]);
    $_[4] .= asn_encode_length(length $tmp);
    $_[4] .= $tmp;
  }
  else {
    $_[4] .= asn_encode_length(length $_[3]);
    $_[4] .= $_[3];
  }
}


sub _enc_null {
# 0      1    2       3     4     5      6
# $optn, $op, $stash, $var, $buf, $loop, $path

  $_[4] .= chr(0);
}


sub _enc_object_id {
# 0      1    2       3     4     5      6
# $optn, $op, $stash, $var, $buf, $loop, $path

  my @data = ($_[3] =~ /(\d+)/g);

  if ($_[1]->[cTYPE] == opOBJID) {
    if(@data < 2) {
      @data = (0);
    }
    else {
      my $first = $data[1] + ($data[0] * 40);
      splice(@data,0,2,$first);
    }
  }

  my $l = length $_[4];
  $_[4] .= pack("cw*", 0, @data);
  substr($_[4],$l,1) = asn_encode_length(length($_[4]) - $l - 1);
}


sub _enc_real {
# 0      1    2       3     4     5      6
# $optn, $op, $stash, $var, $buf, $loop, $path

  # Zero
  unless ($_[3]) {
    $_[4] .= chr(0);
    return;
  }

  require POSIX;

  # +oo (well we use HUGE_VAL as Infinity is not avaliable to perl)
  if ($_[3] >= POSIX::HUGE_VAL()) {
    $_[4] .= pack("C*",0x01,0x40);
    return;
  }

  # -oo (well we use HUGE_VAL as Infinity is not avaliable to perl)
  if ($_[3] <= - POSIX::HUGE_VAL()) {
    $_[4] .= pack("C*",0x01,0x41);
    return;
  }

  if (exists $_[0]->{'encode_real'} && $_[0]->{'encode_real'} ne 'binary') {
    my $tmp = sprintf("%g",$_[3]);
    $_[4] .= asn_encode_length(1+length $tmp);
    $_[4] .= chr(1); # NR1?
    $_[4] .= $tmp;
    return;
  }

  # We have a real number.
  my $first = 0x80;
  my($mantissa, $exponent) = POSIX::frexp($_[3]);

  if ($mantissa < 0.0) {
    $mantissa = -$mantissa;
    $first |= 0x40;
  }
  my($eMant,$eExp);

  while($mantissa > 0.0) {
    ($mantissa, my $int) = POSIX::modf($mantissa * (1<<8));
    $eMant .= chr($int);
  }
  $exponent -= 8 * length $eMant;

  _enc_integer(undef, undef, undef, $exponent, $eExp);

  # $eExp will br prefixed by a length byte
  
  if (5 > length $eExp) {
    $eExp =~ s/\A.//s;
    $first |= length($eExp)-1;
  }
  else {
    $first |= 0x3;
  }

  $_[4] .= asn_encode_length(1 + length($eMant) + length($eExp));
  $_[4] .= chr($first);
  $_[4] .= $eExp;
  $_[4] .= $eMant;
}


sub _enc_sequence {
# 0      1    2       3     4     5      6
# $optn, $op, $stash, $var, $buf, $loop, $path

  if (my $ops = $_[1]->[cCHILD]) {
    my $l = length $_[4];
    $_[4] .= "\0\0"; # guess
    if (defined $_[5]) {
      my $op   = $ops->[0]; # there should only be one
      my $enc  = $encode[$op->[cTYPE]];
      my $tag  = $op->[cTAG];
      my $loop = $op->[cLOOP];

      push @{$_[6]}, -1;

      foreach my $var (@{$_[3]}) {
	$_[6]->[-1]++;
	$_[4] .= $tag;

	&{$enc}(
	  $_[0], # $optn
	  $op,   # $op
	  $_[2], # $stash
	  $var,  # $var
	  $_[4], # $buf
	  $loop, # $loop
	  $_[6], # $path
	);
      }
      pop @{$_[6]};
    }
    else {
      _encode($_[0],$_[1]->[cCHILD], defined($_[3]) ? $_[3] : $_[2], $_[6], $_[4]);
    }
    substr($_[4],$l,2) = asn_encode_length(length($_[4]) - $l - 2);
  }
  else {
    $_[4] .= asn_encode_length(length $_[3]);
    $_[4] .= $_[3];
  }
}


my %_enc_time_opt = ( utctime => 1, withzone => 0, raw => 2);

sub _enc_time {
# 0      1    2       3     4     5      6
# $optn, $op, $stash, $var, $buf, $loop, $path

  my $mode = $_enc_time_opt{$_[0]->{'encode_time'} || ''} || 0;

  if ($mode == 2) {
    $_[4] .= asn_encode_length(length $_[3]);
    $_[4] .= $_[3];
    return;
  }

  my @time;
  my $offset;
  my $isgen = $_[1]->[cTYPE] == opGTIME;

  if (ref($_[3])) {
    $offset = int($_[3]->[1] / 60);
    $time = $_[3]->[0] + $_[3]->[1];
  }
  elsif ($mode == 0) {
    if (exists $_[0]->{'encode_timezone'}) {
      $offset = int($_[0]->{'encode_timezone'} / 60);
      $time = $_[3] + $_[0]->{'encode_timezone'};
    }
    else {
      @time = localtime($_[3]);
      my @g = gmtime($_[3]);
      
      $offset = ($time[1] - $g[1]) + ($time[2] - $g[2]) * 60;
      $time = $_[3] + $offset*60;
    }
  }
  else {
    $time = $_[3];
  }
  @time = gmtime($time);
  $time[4] += 1;
  $time[5] = $isgen ? ($time[5] + 1900) : ($time[5] % 100);

  my $tmp = sprintf("%02d"x6, @time[5,4,3,2,1,0]);
  if ($isgen) {
    my $sp = sprintf("%.03f",$time);
    $tmp .= substr($sp,-4) unless $sp =~ /\.000$/;
  }
  $tmp .= $offset ? sprintf("%+03d%02d",$offset / 60, abs($offset % 60)) : 'Z';
  $_[4] .= asn_encode_length(length $tmp);
  $_[4] .= $tmp;
}


sub _enc_utf8 {
# 0      1    2       3     4     5      6
# $optn, $op, $stash, $var, $buf, $loop, $path

  if (CHECK_UTF8) {
    my $tmp = $_[3];
    utf8::upgrade($tmp) unless Encode::is_utf8($tmp);
    utf8::encode($tmp);
    $_[4] .= asn_encode_length(length $tmp);
    $_[4] .= $tmp;
  }
  else {
    $_[4] .= asn_encode_length(length $_[3]);
    $_[4] .= $_[3];
  }
}


sub _enc_any {
# 0      1    2       3     4     5      6
# $optn, $op, $stash, $var, $buf, $loop, $path

  my $handler;
  if ($_[1]->[cDEFINE] && $_[2]->{$_[1]->[cDEFINE]}) {
    $handler=$_[0]->{oidtable}{$_[2]->{$_[1]->[cDEFINE]}};
  }
  if ($handler) {
    $_[4] .= $handler->encode($_[3]);
  } else {
    $_[4] .= $_[3];
  }
}


sub _enc_choice {
# 0      1    2       3     4     5      6
# $optn, $op, $stash, $var, $buf, $loop, $path

  my $stash = defined($_[3]) ? $_[3] : $_[2];
  for my $op (@{$_[1]->[cCHILD]}) {
    my $var = defined $op->[cVAR] ? $op->[cVAR] : $op->[cCHILD]->[0]->[cVAR];

    if (exists $stash->{$var}) {
      push @{$_[6]}, $var;
      _encode($_[0],[$op], $stash, $_[6], $_[4]);
      pop @{$_[6]};
      return;
    }
  }
  require Carp;
  Carp::croak("No value found for CHOICE " . join(".", @{$_[6]}));
}


1;

