# Copyright (c) 1997-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Entry;

use strict;
use Net::LDAP::ASN qw(LDAPEntry);
use Net::LDAP::Constant qw(LDAP_LOCAL_ERROR);
use vars qw($VERSION);

$VERSION = "0.22";

sub new {
  my $self = shift;
  my $type = ref($self) || $self;

  my $entry = bless { 'changetype' => 'add', changes => [] }, $type;

  $entry;
}

sub clone {
  my $self  = shift;
  my $clone = $self->new();

  $clone->dn($self->dn());
  foreach ($self->attributes()) {
    $clone->add($_ => [$self->get_value($_)]);
  }

  $clone->{changetype} = $self->{changetype};
  my @changes = @{$self->{changes}};
  while (my($action, $cmd) = splice(@changes,0,2)) {
    my @new_cmd;
    my @cmd = @$cmd;
    while (my($type, $val) = splice(@cmd,0,2)) {
      push @new_cmd, $type, [ @$val ];
    }
    push @{$clone->{changes}}, $action, \@new_cmd;
  }

  $clone;
}

# Build attrs cache, created when needed

sub _build_attrs {
  +{ map { (lc($_->{type}),$_->{vals}) }  @{$_[0]->{asn}{attributes}} };
}

# If we are passed an ASN structure we really do nothing

sub decode {
  my $self = shift;
  my $result = ref($_[0]) ? shift : $LDAPEntry->decode(shift)
    or return;

  %{$self} = ( asn => $result, changetype => 'modify', changes => []);

  $self;
}



sub encode {
  $LDAPEntry->encode( shift->{asn} );
}


sub dn {
  my $self = shift;
  @_ ? ($self->{asn}{objectName} = shift) : $self->{asn}{objectName};
}

sub get_attribute {
  require Carp;
  Carp::carp("->get_attribute deprecated, use ->get_value") if $^W;
  shift->get_value(@_, asref => !wantarray);
}

sub get {
  require Carp;
  Carp::carp("->get deprecated, use ->get_value") if $^W;
  shift->get_value(@_, asref => !wantarray);
}


sub exists {
  my $self = shift;
  my $type = lc(shift);
  my $attrs = $self->{attrs} ||= _build_attrs($self);

  exists $attrs->{$type};
}

sub get_value {
  my $self = shift;
  my $type = lc(shift);
  my %opt  = @_;

  if ($opt{alloptions}) {
    my %ret = map {
                $_->{type} =~ /^\Q$type\E((?:;.*)?)$/i ? (lc($1), $_->{vals}) : ()
              } @{$self->{asn}{attributes}};
    return %ret ? \%ret : undef;
  }

  my $attrs = $self->{attrs} ||= _build_attrs($self);
  my $attr  = $attrs->{$type} or return;

  return $opt{asref}
	  ? $attr
	  : wantarray
	    ? @{$attr}
	    : $attr->[0];
}


sub changetype {
  my $self = shift;
  return $self->{'changetype'} unless @_;
  $self->{'changes'} = [];
  $self->{'changetype'} = shift;
}



sub add {
  my $self  = shift;
  my $cmd   = $self->{'changetype'} eq 'modify' ? [] : undef;
  my $attrs = $self->{attrs} ||= _build_attrs($self);

  while (my($type,$val) = splice(@_,0,2)) {
    $type = lc $type;

    push @{$self->{asn}{attributes}}, { type => $type, vals => ($attrs->{$type}=[])}
      unless exists $attrs->{$type};

    push @{$attrs->{$type}}, ref($val) ? @$val : $val;

    push @$cmd, $type, [ ref($val) ? @$val : $val ]
      if $cmd;

  }

  push(@{$self->{'changes'}}, 'add', $cmd) if $cmd;
}


sub replace {
  my $self  = shift;
  my $cmd   = $self->{'changetype'} eq 'modify' ? [] : undef;
  my $attrs = $self->{attrs} ||= _build_attrs($self);

  while(my($type, $val) = splice(@_,0,2)) {
    $type = lc $type;

    if (defined($val) and (!ref($val) or @$val)) {

      push @{$self->{asn}{attributes}}, { type => $type, vals => ($attrs->{$type}=[])}
	unless exists $attrs->{$type};

      @{$attrs->{$type}} = ref($val) ? @$val : ($val);

      push @$cmd, $type, [ ref($val) ? @$val : $val ]
	if $cmd;

    }
    else {
      delete $attrs->{$type};

      @{$self->{asn}{attributes}}
	= grep { $type ne lc($_->{type}) } @{$self->{asn}{attributes}};

      push @$cmd, $type, []
	if $cmd;

    }
  }

  push(@{$self->{'changes'}}, 'replace', $cmd) if $cmd;
}


sub delete {
  my $self = shift;

  unless (@_) {
    $self->changetype('delete');
    return;
  }

  my $cmd = $self->{'changetype'} eq 'modify' ? [] : undef;
  my $attrs = $self->{attrs} ||= _build_attrs($self);

  while(my($type,$val) = splice(@_,0,2)) {
    $type = lc $type;

    if (defined($val) and (!ref($val) or @$val)) {
      my %values;
      @values{@$val} = ();

      unless( @{$attrs->{$type}}
        = grep { !exists $values{$_} } @{$attrs->{$type}})
      {
	delete $attrs->{$type};
	@{$self->{asn}{attributes}}
	  = grep { $type ne lc($_->{type}) } @{$self->{asn}{attributes}};
      }

      push @$cmd, $type, [ ref($val) ? @$val : $val ]
	if $cmd;
    }
    else {
      delete $attrs->{$type};

      @{$self->{asn}{attributes}}
	= grep { $type ne lc($_->{type}) } @{$self->{asn}{attributes}};

      push @$cmd, $type, [] if $cmd;
    }
  }

  push(@{$self->{'changes'}}, 'delete', $cmd) if $cmd;
}


sub update {
  my $self = shift;
  my $ldap = shift;
  my %opt = @_;
  my $mesg;
  my $user_cb = delete $opt{callback};
  my $cb = sub { $self->changetype('modify') unless $_[0]->code;
                 $user_cb->(@_) if $user_cb };

  if ($self->{'changetype'} eq 'add') {
    $mesg = $ldap->add($self, 'callback' => $cb, %opt);
  }
  elsif ($self->{'changetype'} eq 'delete') {
    $mesg = $ldap->delete($self, 'callback' => $cb, %opt);
  }
  elsif ($self->{'changetype'} =~ /modr?dn/) {
    my @args = (newrdn => $self->get_value('newrdn'),
                deleteoldrdn => $self->get_value('deleteoldrdn'));
    my $newsuperior = $self->get_value('newsuperior');
    push(@args, newsuperior => $newsuperior) if $newsuperior;
    $mesg = $ldap->moddn($self, @args, 'callback' => $cb, %opt);
  }
  elsif (@{$self->{'changes'}}) {
    $mesg = $ldap->modify($self, 'changes' => $self->{'changes'}, 'callback' => $cb, %opt);
  }
  else {
    require Net::LDAP::Message;
    $mesg = Net::LDAP::Message->new( $ldap );
    $mesg->set_error(LDAP_LOCAL_ERROR,"No attributes to update");
  }

  return $mesg;
}


# Just for debugging

sub dump {
  my $self = shift;
  no strict 'refs'; # select may return a GLOB name
  my $fh = @_ ? shift : select;

  my $asn = $self->{asn};
  print $fh "-" x 72,"\n";
  print $fh "dn:",$asn->{objectName},"\n\n" if $asn->{objectName};

  my($attr,$val);
  my $l = 0;

  for (keys %{ $self->{attrs} ||= _build_attrs($self) }) {
    $l = length if length > $l;
  }

  my $spc = "\n  " . " " x $l;

  foreach $attr (@{$asn->{attributes}}) {
    $val = $attr->{vals};
    printf $fh "%${l}s: ", $attr->{type};
    my($i,$v);
    $i = 0;
    foreach $v (@$val) {
      print $fh $spc if $i++;
      print $fh $v;
    }
    print $fh "\n";
  }
}

sub attributes {
  my $self = shift;
  my %opt  = @_;

  if ($opt{nooptions}) {
    my %done;
    return map {
      $_->{type} =~ /^([^;]+)/;
      $done{lc $1}++ ? () : ($1);
    } @{$self->{asn}{attributes}};
  }
  else {
    return map { $_->{type} } @{$self->{asn}{attributes}};
  }
}

sub asn {
  shift->{asn}
}

sub changes {
  my $ref = shift->{'changes'};
  $ref ? @$ref : ();
}

1;
