# Copyright (c) 2000-2002 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Convert::ASN1;

# $Id: IO.pm,v 1.1.2.1 2007/03/08 09:08:01 jmm Exp $

use strict;
use Socket;

BEGIN {
  local $SIG{__DIE__};
  eval { require bytes } and 'bytes'->import
}

sub asn_recv { # $socket, $buffer, $flags

  my $peer;
  my $buf;
  my $n = 128;
  my $pos = 0;
  my $depth = 0;
  my $len = 0;
  my($tmp,$tb,$lb);

  MORE:
  for(
    $peer = recv($_[0],$buf,$n,MSG_PEEK);
    defined $peer;
    $peer = recv($_[0],$buf,$n<<=1,MSG_PEEK)
  ) {

    if ($depth) { # Are we searching of "\0\0"

      unless (2+$pos <= length $buf) {
	next MORE if $n == length $buf;
	last MORE;
      }

      if(substr($buf,$pos,2) eq "\0\0") {
	unless (--$depth) {
	  $len = $pos + 2;
	  last MORE;
	}
      }
    }

    # If we can decode a tag and length we can detemine the length
    ($tb,$tmp) = asn_decode_tag(substr($buf,$pos));
    unless ($tb || $pos+$tb < length $buf) {
      next MORE if $n == length $buf;
      last MORE;
    }

    if (ord(substr($buf,$pos+$tb,1)) == 0x80) {
      # indefinite length, grrr!
      $depth++;
      $pos += $tb + 1;
      redo MORE;
    }

    ($lb,$len) = asn_decode_length(substr($buf,$pos+$tb));

    if ($lb) {
      if ($depth) {
	$pos += $tb + $lb + $len;
	redo MORE;
      }
      else {
	$len += $tb + $lb + $pos;
	last MORE;
      }
    }
  }

  if (defined $peer) {
    if ($len > length $buf) {
      # Check we can read the whole element
      goto error
	unless defined($peer = recv($_[0],$buf,$len,MSG_PEEK));

      if ($len > length $buf) {
	# Cannot get whole element
	$_[1]='';
	return $peer;
      }
    }
    elsif ($len == 0) {
      $_[1] = '';
      return $peer;
    }

    if ($_[2] & MSG_PEEK) {
      $_[1] =  substr($buf,0,$len);
    }
    elsif (!defined($peer = recv($_[0],$_[1],$len,0))) {
      goto error;
    }

    return $peer;
  }

error:
    $_[1] = undef;
}

sub asn_read { # $fh, $buffer, $offset

  # We need to read one packet, and exactly only one packet.
  # So we have to read the first few bytes one at a time, until
  # we have enough to decode a tag and a length. We then know
  # how many more bytes to read

  my $pos = 0;
  my $need = 0;
  if ($_[2]) {
    if ($_[2] > length $_[1]) {
      require Carp;
      Carp::carp("Offset beyond end of buffer");
      return;
    }
    substr($_[1],$_[2]) = '';
  }
  else {
    $_[1] = '';
  }
  my $depth = 0;
  my $ch;
  my $n;

  while(($n = $need - length $_[1]) > 0) {
    sysread($_[0],$_[1],$n,length $_[1]) or
	goto READ_ERR;
  }

  while(1) {
    $need = $pos + 2;
    my $tch = ord(substr($_[1],$pos++,1));

    # Tag may be multi-byte
    if(($tch & 0x1f) == 0x1f) {
      my $ch;
      do {
        $need++;
	while(($n = $need - length $_[1]) > 0) {
	  sysread($_[0],$_[1],$n,length $_[1]) or
	      goto READ_ERR;
	}
	$ch = ord(substr($_[1],$pos++,1));
      } while($ch & 0x80);
    }

    $need = $pos + 1;

    while(($n = $need - length $_[1]) > 0) {
      sysread($_[0],$_[1],$n,length $_[1]) or
	  goto READ_ERR;
    }

    my $len = ord(substr($_[1],$pos++,1));

    if($len & 0x80) {
      unless ($len &= 0x7f) {
	$depth++;
	next;
      }
      $need = $pos + $len;

      while(($n = $need - length $_[1]) > 0) {
	sysread($_[0],$_[1],$n,length $_[1]) or
	    goto READ_ERR;
      }

      $pos += $len + unpack("N", "\0" x (4 - $len) . substr($_[1],$pos,$len));
    }
    elsif (!$len && !$tch) {
      die "Bad ASN PDU" unless $depth;
      unless (--$depth) {
	last;
      }
    }
    else {
      $pos += $len;
    }

    $need = $pos + 2*$depth;

    while(($n = $need - length $_[1]) > 0) {
      sysread($_[0],$_[1],$n,length $_[1]) or
	  goto READ_ERR;
    }
    last unless $depth;
  }

  return length $_[1];

READ_ERR:
    $@ = "I/O Error $! " . CORE::unpack("H*",$_[1]);
    return undef;
}

sub asn_send { # $sock, $buffer, $flags, $to

  @_ == 4
    ? send($_[0],$_[1],$_[2],$_[3])
    : send($_[0],$_[1],$_[2]);
}

sub asn_write { # $sock, $buffer

  syswrite($_[0],$_[1], length $_[1]);
}

sub asn_get { # $fh

  my $fh = ref($_[0]) ? $_[0] : \($_[0]);
  my $href = \%{*$fh};

  $href->{'asn_buffer'} = '' unless exists $href->{'asn_buffer'};

  my $need = delete $href->{'asn_need'} || 0;
  while(1) {
    next if $need;
    my($tb,$tag) = asn_decode_tag($href->{'asn_buffer'}) or next;
    my($lb,$len) = asn_decode_length(substr($href->{'asn_buffer'},$tb,8)) or next;
    $need = $tb + $lb + $len;
  }
  continue {
    if ($need && $need <= length $href->{'asn_buffer'}) {
      my $ret = substr($href->{'asn_buffer'},0,$need);
      substr($href->{'asn_buffer'},0,$need) = '';
      return $ret;
    }

    my $get = $need > 1024 ? $need : 1024;

    sysread($_[0], $href->{'asn_buffer'}, $get, length $href->{'asn_buffer'})
      or return undef;
  }
}

sub asn_ready { # $fh

  my $fh = ref($_[0]) ? $_[0] : \($_[0]);
  my $href = \%{*$fh};

  return 0 unless exists $href->{'asn_buffer'};
  
  return $href->{'asn_need'} <= length $href->{'asn_buffer'}
    if exists $href->{'asn_need'};

  my($tb,$tag) = asn_decode_tag($href->{'asn_buffer'}) or return 0;
  my($lb,$len) = asn_decode_length(substr($href->{'asn_buffer'},$tb,8)) or return 0;

  $href->{'asn_need'} = $tb + $lb + $len;

  $href->{'asn_need'} <= length $href->{'asn_buffer'};
}

1;
