# Copyright (c) 1997-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::LDIF;

use strict;
use SelectSaver;
require Net::LDAP::Entry;
use vars qw($VERSION);

$VERSION = "0.15";

my %mode = qw(w > r < a >>);

sub new {
  my $pkg = shift;
  my $file = shift || "-";
  my $mode = shift || "r";
  my %opt = @_;
  my $fh;
  my $opened_fh = 0;
  
  if (ref($file)) {
    $fh = $file;
  }
  else {
    if ($file eq "-") {
      if ($mode eq "w") {
        ($file,$fh) = ("STDOUT",\*STDOUT);
      }
      else {
        ($file,$fh) = ("STDIN",\*STDIN);
      }
    }
    else {
      require Symbol;
      $fh = Symbol::gensym();
      my $open = $file =~ /^\| | \|$/x
	? $file
	: (($mode{$mode} || "<") . $file);
      open($fh,$open) or return;
      $opened_fh = 1;
    }
  }

  # Default the encoding of DNs to 'none' unless the user specifies
  $opt{'encode'} = 'none' unless exists $opt{'encode'};

  # Default the error handling to die 
  $opt{'onerror'} = 'die' unless exists $opt{'onerror'};

  $opt{'lowercase'} ||= 0;
  $opt{'change'} ||= 0;
  $opt{'sort'} ||= 0;

  my $self = {
    changetype => "modify",
    modify => 'add',
    wrap => 78,
    %opt,
    fh   => $fh,
    file => "$file",
    opened_fh => $opened_fh,
    eof => 0,
    write_count => ($mode eq 'a' and tell($fh) > 0) ? 1 : 0,
  };

  # fetch glob for URL type attributes (one per LDIF object)
  if ($mode eq "r") {
    require Symbol;
    $self->{_attr_fh} = Symbol::gensym();
  }

  bless $self, $pkg;
}
  
sub _read_lines {
  my $self = shift;
  my @ldif;

  {
    local $/ = "";
    my $fh = $self->{'fh'};
    my $ln;
    do {	# allow comments separated by blank lines
      $ln = $self->{_next_lines} || scalar <$fh>;
      unless ($ln) {
         $self->{_next_lines} = '';
         $self->{_current_lines} = '';
         $self->eof(1);
         return;
      }
      $ln =~ s/\n //sg;
      $ln =~ s/^#.*\n//mg;
      chomp($ln);
      $self->{_current_lines} = $ln;
    } until ($self->{_current_lines} || $self->eof());
    chomp(@ldif = split(/^/, $ln));
    do {
      $ln = scalar <$fh> || '';
      $self->eof(1) unless $ln;
      $ln =~ s/\n //sg;
      $ln =~ s/^#.*\n//mg;
      chomp($ln);
      $self->{_next_lines} = $ln;
    } until ($self->{_next_lines} || $self->eof());
  }

  @ldif;
}


# read attribute value from URL (currently only file: URLs)
sub _read_url_attribute {
  my $self = shift;
  my $url = shift;
  my @ldif = @_;
  my $line;

  if ($url =~ s/^file:(?:\/\/)?//) {
    my $fh = $self->{_attr_fh};
    unless (open($fh, '<', $url)) {
      $self->_error("can't open $line: $!", @ldif);
      return;
    }
    binmode($fh);
    { # slurp in whole file at once
      local $/;
      $line = <$fh>;
    }
    close($fh);
  } else {
    $self->_error("unsupported URL type", @ldif);
    return;
  }

  $line;
}


# _read_one() is deprecated and will be removed
# in a future version
*_read_one = \&_read_entry; 

sub _read_entry {
  my $self = shift;
  my @ldif;
  $self->_clear_error();
  
  @ldif = $self->_read_lines;

  unless (@ldif) {	# empty records are errors if not at eof
    $self->_error("illegal empty LDIF entry")  if (!$self->eof());
    return;
  }
  # What does that mean ???
  #shift @ldif if @ldif && $ldif[0] !~ /\D/;

  if (@ldif and $ldif[0] =~ /^version:\s+(\d+)/) {
    $self->{version} = $1;
    shift @ldif;
    return $self->_read_entry
      unless @ldif;
  }

  if (@ldif <= 1) {
     $self->_error("LDIF entry is not valid", @ldif);
     return;
  }
  elsif (not ( $ldif[0] =~ s/^dn:(:?) *//) ) {
     $self->_error("First line of LDIF entry does not begin with 'dn:'", @ldif);
     return;
  }

  my $dn = shift @ldif;

  if (length($1)) {
    eval { require MIME::Base64 };
    if ($@) {
      $self->_error($@, @ldif);
      return;
    }
    $dn = MIME::Base64::decode($dn);
  }

  my $entry = Net::LDAP::Entry->new;
  $entry->dn($dn);

  if ($ldif[0] =~ /^changetype:\s*/) {
    my $changetype = $ldif[0] =~ s/^changetype:\s*//
        ? shift(@ldif) : $self->{'changetype'};
    $entry->changetype($changetype);

    return $entry if ($changetype eq "delete");

    unless (@ldif) {
      $self->_error("LDAP entry is not valid",@ldif);
      return;
    }

    while(@ldif) {
      my $modify = $self->{'modify'};
      my $modattr;
      my $lastattr;
      if($changetype eq "modify") {
        unless ( (my $tmp = shift @ldif) =~ s/^(add|delete|replace):\s*([-;\w]+)// ) {
          $self->_error("LDAP entry is not valid",@ldif); 
          return;
        }
        $lastattr = $modattr = $2;
        $modify  = $1;
      }
      my @values;
      while(@ldif) {
        my $line = shift @ldif;
        my $attr;
  
        if ($line eq "-") {
          $entry->$modify($lastattr, \@values)
            if defined $lastattr;
          undef $lastattr;
          @values = ();
          last;
        }
 
        $line =~ s/^([-;\w]+):\s*// and $attr = $1;

        # base64 encoded attribute: decode it
        if ($line =~ s/^:\s*//) {
          eval { require MIME::Base64 };
          if ($@) {
            $self->_error($@, @ldif);
            return;
          }
          $line = MIME::Base64::decode($line);
        }
        # url attribute: read in file:// url, fail on others
        elsif ($line =~ s/^\<\s*(.*?)\s*$/$1/) {
          $line = $self->_read_url_attribute($line, @ldif);
          return  if !defined($line);
        }
 
        if( defined($modattr) && $attr ne $modattr ) {
          $self->_error("LDAP entry is not valid", @ldif);
          return;
        }

        if(!defined($lastattr) || $lastattr ne $attr) {
          $entry->$modify($lastattr, \@values)
            if defined $lastattr;
          $lastattr = $attr;
          @values = ($line);
          next;
        }
        push @values, $line;
      }
      $entry->$modify($lastattr, \@values)
       if defined $lastattr;
    }
  }

  else {
    my @attr;
    my $last = "";
    my $vals = [];
    my $line;
    my $attr;
    foreach $line (@ldif) {
      $line =~ s/^([-;\w]+):\s*// && ($attr = $1) or next;
  
      # base64 encoded attribute: decode it
      if ($line =~ s/^:\s*//) {
        eval { require MIME::Base64 };
        if ($@) {
          $self->_error($@, @ldif);
          return;
        }
        $line = MIME::Base64::decode($line);
      }
      # url attribute: read in file:// url, fail on others
      elsif ($line =~ s/^\<\s*(.*?)\s*$/$1/) {
        $line = $self->_read_url_attribute($line, @ldif);
        return  if !defined($line);
      }
  
      if ($attr eq $last) {
        push @$vals, $line;
        next;
      }
      else {
        $vals = [$line];
        push(@attr,$last=$attr,$vals);
      }
    }
    $entry->add(@attr);
  }
  $self->{_current_entry} = $entry;

  $entry;
}

sub read_entry {
  my $self = shift;

  unless ($self->{'fh'}) {
     $self->_error("LDIF file handle not valid");
     return;
  }
  $self->_read_entry();
}

# read() is deprecated and will be removed
# in a future version
sub read {
  my $self = shift;

  return $self->read_entry() unless wantarray;

  my($entry, @entries);
  push(@entries,$entry) while $entry = $self->read_entry;

  @entries;
}

sub eof {
  my $self = shift;
  my $eof = shift;

  if ($eof) {
    $self->{_eof} = $eof; 
  }

  $self->{_eof};
}

sub _wrap {
  if($_[1] > 40) {
    my $pos = $_[1];
    while($pos < length($_[0])) {
      substr($_[0],$pos,0) = "\n ";
      $pos += $_[1]+1;
    }
  }
  $_[0];
}

sub _write_attr {
  my($attr,$val,$wrap,$lower) = @_;
  my $v;
  my $res = 1;	# result value
  foreach $v (@$val) {
    my $ln = $lower ? lc $attr : $attr;
    if ($v =~ /(^[ :]|[\x00-\x1f\x7f-\xff])/) {
      require MIME::Base64;
      $ln .= ":: " . MIME::Base64::encode($v,"");
    }
    else {
      $ln .= ": " . $v;
    }
    $res &&= print _wrap($ln,$wrap),"\n";
  }
  $res;
}

# helper function to compare attribute names (sort objectClass first)
sub _cmpAttrs {
  ($a =~ /^objectclass$/io)
  ? -1 : (($b =~ /^objectclass$/io) ? 1 : ($a cmp $b));
}

sub _write_attrs {
  my($entry,$wrap,$lower,$sort) = @_;
  my @attributes = $entry->attributes();
  my $attr;
  my $res = 1;	# result value
  @attributes = sort _cmpAttrs @attributes  if ($sort);
  foreach $attr (@attributes) {
    my $val = $entry->get_value($attr, asref => 1);
    $res &&= _write_attr($attr,$val,$wrap,$lower);
  }
  $res;
}

sub _write_dn {
  my($dn,$encode,$wrap) = @_;
  if ($dn =~ /^[ :<]|[\x00-\x1f\x7f-\xff]/) {
    if ($encode =~ /canonical/i) {
      require Net::LDAP::Util;
      $dn = Net::LDAP::Util::canonical_dn($dn);
      # Canonicalizer won't fix leading spaces, colons or less-thans, which
      # are special in LDIF, so we fix those up here.
      $dn =~ s/^([ :<])/\\$1/;
    } elsif ($encode =~ /base64/i) {
      require MIME::Base64;
      $dn = "dn:: " . MIME::Base64::encode($dn,"");
    } else {
      $dn = "dn: $dn";
    }
  } else {
    $dn = "dn: $dn";
  }
  print _wrap($dn,$wrap), "\n";
}

# write() is deprecated and will be removed
# in a future version
sub write {
  my $self = shift;

  $self->_write_entry(0, @_);
}

sub write_entry {
  my $self = shift;

  $self->_write_entry($self->{change}, @_);
}

# internal helper: write entry in different format depending on 1st arg
sub _write_entry {
  my $self = shift;
  my $change = shift;
  my $entry;
  my $wrap = int($self->{'wrap'});
  my $lower = $self->{'lowercase'};
  my $sort = $self->{'sort'};
  my $res = 1;	# result value
  local($\,$,); # output field and record separators

  unless ($self->{'fh'}) {
     $self->_error("LDIF file handle not valid");
     return;
  }
  my $saver = SelectSaver->new($self->{'fh'});
  
  my $fh = $self->{'fh'};
  foreach $entry (@_) {
    unless (ref $entry) {
       $self->_error("Entry '$entry' is not a valid Net::LDAP::Entry object.");
       $res = 0;
       next;
    }

    if ($change) {
      my @changes = $entry->changes;
      my $type = $entry->changetype;

      # Skip entry if there is nothing to write
      next if $type eq 'modify' and !@changes;

      if ($self->{write_count}++) {
	$res &&= print "\n";
      }
      else {
        $res &&= print "version: $self->{version}\n\n"
          if defined $self->{version};
      }
      $res &&= _write_dn($entry->dn,$self->{'encode'},$wrap);

      $res &&= print "changetype: $type\n";

      if ($type eq 'delete') {
        next;
      }
      elsif ($type eq 'add') {
        $res &&= _write_attrs($entry,$wrap,$lower,$sort);
        next;
      }
      elsif ($type =~ /modr?dn/o) {
        my $deleteoldrdn = $entry->get_value('deleteoldrdn') || 0;
        $res &&= print _write_attr('newrdn',$entry->get_value('newrdn', asref => 1),$wrap,$lower);
        $res &&= print 'deleteoldrdn: ', $deleteoldrdn,"\n";
        my $ns = $entry->get_value('newsuperior', asref => 1);
        $res &&= print _write_attr('newsuperior',$ns,$wrap,$lower) if defined $ns;
        next;
      }

      my $dash=0;
      foreach my $chg (@changes) {
        unless (ref($chg)) {
          $type = $chg;
          next;
        }
        my $i = 0;
        while ($i < @$chg) {
	  $res &&= print "-\n" if $dash++;
          my $attr = $chg->[$i++];
          my $val = $chg->[$i++];
          $res &&= print $type,": ",$attr,"\n";
          $res &&= _write_attr($attr,$val,$wrap,$lower);
        }
      }
    }

    else {
      if ($self->{write_count}++) {
	$res &&= print "\n";
      }
      else {
        $res &&= print "version: $self->{version}\n\n"
          if defined $self->{version};
      }
      $res &&= _write_dn($entry->dn,$self->{'encode'},$wrap);
      $res &&= _write_attrs($entry,$wrap,$lower,$sort);
    }
  }

  $res;
}

# read_cmd() is deprecated in favor of read_entry() 
# and will be removed in a future version
sub read_cmd {
  my $self = shift;

  return $self->read_entry() unless wantarray;

  my($entry, @entries);
  push(@entries,$entry) while $entry = $self->read_entry;

  @entries;
}

# _read_one_cmd() is deprecated in favor of _read_one() 
# and will be removed in a future version
*_read_one_cmd = \&_read_entry;

# write_cmd() is deprecated in favor of write_entry() 
# and will be removed in a future version
sub write_cmd {
  my $self = shift;

  $self->_write_entry(1, @_);
}

sub done {
  my $self = shift;
  my $res = 1;	# result value
  if ($self->{fh}) {
     if ($self->{opened_fh}) {
       $res = close $self->{fh};
       undef $self->{opened_fh};
     }
     delete $self->{fh};
  }
  $res;
}

my %onerror = (
  'die'   => sub {
                my $self = shift;
                require Carp;
                $self->done;
                Carp::croak($self->error(@_));
             },
  'warn'  => sub { 
                my $self = shift;
                require Carp; 
                Carp::carp($self->error(@_)); 
             },
  'undef' => sub { 
                my $self = shift;
                require Carp; 
                Carp::carp($self->error(@_)) if $^W; 
             },
);

sub _error {
   my ($self,$errmsg,@errlines) = @_;
   $self->{_err_msg} = $errmsg;
   $self->{_err_lines} = join "\n",@errlines;

   scalar &{ $onerror{ $self->{onerror} } }($self,$self->{_err_msg}) if $self->{onerror};
}

sub _clear_error {
  my $self = shift;

  undef $self->{_err_msg};
  undef $self->{_err_lines};
}

sub error {
  my $self = shift;
  $self->{_err_msg};
}

sub error_lines {
  my $self = shift;
  $self->{_err_lines};
}

sub current_entry {
  my $self = shift;
  $self->{_current_entry};
}

sub current_lines {
  my $self = shift;
  $self->{_current_lines};
}

sub version {
  my $self = shift;
  return $self->{version} unless @_;
  $self->{version} = shift;
}

sub next_lines {
  my $self = shift;
  $self->{_next_lines};
}

sub DESTROY {
  my $self = shift;
  $self->done();
}

1;
