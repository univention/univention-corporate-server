# Copyright (c) 2000-2002 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Convert::ASN1;

# $Id: Debug.pm,v 1.1.2.1 2007/03/08 09:08:01 jmm Exp $

##
## just for debug :-)
##

sub _hexdump {
  my($fmt,$pos) = @_[1,2]; # Don't copy buffer

  $pos ||= 0;

  my $offset  = 0;
  my $cnt     = 1 << 4;
  my $len     = length($_[0]);
  my $linefmt = ("%02X " x $cnt) . "%s\n";

  print "\n";

  while ($offset < $len) {
    my $data = substr($_[0],$offset,$cnt);
    my @y = unpack("C*",$data);

    printf $fmt,$pos if $fmt;

    # On the last time through replace '%02X ' with '__ ' for the
    # missing values
    substr($linefmt, 5*@y,5*($cnt-@y)) = "__ " x ($cnt - @y)
	if @y != $cnt;

    # Change non-printable chars to '.'
    $data =~ s/[\x00-\x1f\x7f-\xff]/./sg;
    printf $linefmt, @y,$data;

    $offset += $cnt;
    $pos += $cnt;
  }
}

my %type = (
  split(/[\t\n]\s*/,
    q(10	SEQUENCE
      01	BOOLEAN
      0A	ENUM
      0D	RELATIVE-OID
      11	SET
      02	INTEGER
      03	BIT STRING
      C0	[PRIVATE %d]
      04	STRING
      40	[APPLICATION %d]
      05	NULL
      06	OBJECT ID
      80	[CONTEXT %d]
    )
  )
);

BEGIN { undef &asn_dump }
sub asn_dump {
  my $fh = @_>1 ? shift : \*STDERR;

  my $ofh = select($fh);

  my $pos = 0;
  my $indent = "";
  my @seqend = ();
  my $length = length($_[0]);
  my $fmt = $length > 0xffff ? "%08X" : "%04X";

  while(1) {
    while (@seqend && $pos >= $seqend[0]) {
      $indent = substr($indent,2);
      warn "Bad sequence length " unless $pos == shift @seqend;
      printf "$fmt     : %s}\n",$pos,$indent;
    }
    last unless $pos < $length;
    
    my $start = $pos;
    my($tb,$tag,$tnum) = asn_decode_tag2(substr($_[0],$pos,10));
    $pos += $tb;
    my($lb,$len) = asn_decode_length(substr($_[0],$pos,10));
    $pos += $lb;

    if($tag == 0 && $len == 0) {
      $seqend[0] = $pos;
      redo;
    }
    printf $fmt. " %4d: %s",$start,$len,$indent;

    my $label = $type{sprintf("%02X",$tag & ~0x20)}
		|| $type{sprintf("%02X",$tag & 0xC0)}
		|| "[UNIVERSAL %d]";
    printf $label, $tnum;

    if ($tag & ASN_CONSTRUCTOR) {
      print " {\n";
      if($len < 0) {
          unshift(@seqend, length $_[0]);
      }
      else {
          unshift(@seqend, $pos + $len);
      }
      $indent .= "  ";
      next;
    }

    my $tmp;

    for ($label) { # switch
      /^(INTEGER|ENUM)/ && do {
	Convert::ASN1::_dec_integer({},[],{},$tmp,$_[0],$pos,$len);
	printf " = %d\n",$tmp;
        last;
      };

      /^BOOLEAN/ && do {
	Convert::ASN1::_dec_boolean({},[],{},$tmp,$_[0],$pos,$len);
	printf " = %s\n",$tmp ? 'TRUE' : 'FALSE';
        last;
      };

      /^(?:(OBJECT ID)|(RELATIVE-OID))/ && do {
	my @op; $op[cTYPE] = $1 ? opOBJID : opROID;
	Convert::ASN1::_dec_object_id({},\@op,{},$tmp,$_[0],$pos,$len);
	printf " = %s\n",$tmp;
        last;
      };

      /^NULL/ && do {
	print "\n";
        last;
      };

      /^STRING/ && do {
	Convert::ASN1::_dec_string({},[],{},$tmp,$_[0],$pos,$len);
	if ($tmp =~ /[\x00-\x1f\x7f-\xff]/s) {
  	  _hexdump($tmp,$fmt . "     :   ".$indent, $pos);
	}
	else {
	  printf " = '%s'\n",$tmp;
	}
        last;
      };

#      /^BIT STRING/ && do {
#	Convert::BER::BIT_STRING->unpack($ber,\$tmp);
#	print " = ",$tmp,"\n";
#        last;
#      };

      # default -- dump hex data
      _hexdump(substr($_[0],$pos,$len),$fmt . "     :   ".$indent, $pos);
    }
    $pos += $len;
  }

  select($ofh);
}

BEGIN { undef &asn_hexdump }
sub asn_hexdump {
    my $fh = @_>1 ? shift : \*STDERR;
    my $ofh = select($fh);

    _hexdump($_[0]);
    print "\n";
    select($ofh);
}

BEGIN { undef &dump }
sub dump {
  my $self = shift;
  
  for (@{$self->{script}}) {
    dump_op($_,"",{},1);
  }
}

BEGIN { undef &dump_all }
sub dump_all {
  my $self = shift;
  
  while(my($k,$v) = each %{$self->{tree}}) {
    print STDERR "$k:\n";
    for (@$v) {
      dump_op($_,"",{},1);
    }
  }
}


BEGIN { undef &dump_op }
sub dump_op {
  my($op,$indent,$done,$line) = @_;
  $indent ||= "";
  printf STDERR "%3d: ",$line;
  if ($done->{$op}) {
    print STDERR "    $indent=",$done->{$op},"\n";
    return ++$line;
  }
  $done->{$op} = $line++;
  print STDERR $indent,"[ '",unpack("H*",$op->[cTAG]),"', ";
  print STDERR $op->[cTYPE] =~ /\D/ ? $op->[cTYPE] : $opName[$op->[cTYPE]];
  print STDERR ", ",defined($op->[cVAR]) ? $op->[cVAR] : "_";
  print STDERR ", ",defined($op->[cLOOP]) ? $op->[cLOOP] : "_";
  print STDERR ", ",defined($op->[cOPT]) ? $op->[cOPT] : "_";
  print STDERR "]";
  if ($op->[cCHILD]) {
    print STDERR " ",scalar @{$op->[cCHILD]},"\n";
    for (@{$op->[cCHILD]}) {
      $line = dump_op($_,$indent . " ",$done,$line);
    }
  }
  else {
    print STDERR "\n";
  }
  print STDERR "\n" unless length $indent;
  $line;
}

1;

