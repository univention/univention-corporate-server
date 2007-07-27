# Copyright (c) 1997-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Search;

use strict;
use vars qw(@ISA $VERSION);
use Net::LDAP::Message;
use Net::LDAP::Entry;
use Net::LDAP::Filter;
use Net::LDAP::Constant qw(LDAP_SUCCESS LDAP_DECODING_ERROR);

@ISA = qw(Net::LDAP::Message);
$VERSION = "0.10";


sub first_entry { # compat
  my $self = shift;
  $self->entry(0);
}


sub next_entry { # compat
  my $self = shift;
  $self->entry( defined $self->{'CurrentEntry'}
		? $self->{'CurrentEntry'} + 1
		: 0);
}


sub decode {
  my $self = shift;
  my $result = shift;

  return $self->SUPER::decode($result)
    if exists $result->{protocolOp}{searchResDone};

  my $data;
  @{$self}{qw(controls ctrl_hash)} = ($result->{controls}, undef);

  if ($data = delete $result->{protocolOp}{searchResEntry}) {

    my $entry = Net::LDAP::Entry->new;

    $entry->decode($data)
      or $self->set_error(LDAP_DECODING_ERROR,"LDAP decode error")
     and return;

    push(@{$self->{entries} ||= []}, $entry);

    $self->{callback}->($self,$entry)
      if (defined $self->{callback});

    return $self;
  }
  elsif ($data = delete $result->{protocolOp}{searchResRef}) {

    push(@{$self->{'reference'} ||= []}, @$data);

    $self->{callback}->($self, bless $data, 'Net::LDAP::Reference')
      if (defined $self->{callback});

    return $self;
  }

  $self->set_error(LDAP_DECODING_ERROR, "LDAP decode error");
  return;
}

sub entry {
  my $self = shift;
  my $index = shift || 0; # avoid undef warning and default to first entry

  my $entries = $self->{entries} ||= [];
  my $ldap = $self->parent;

  # There could be multiple response to a search request
  # but only the last will set {resultCode}
  until (exists $self->{resultCode} || (@{$entries} > $index)) {
    return
      unless $ldap->_recvresp($self->mesg_id) == LDAP_SUCCESS;
  }

  return
    unless (@{$entries} > $index);

  $self->{current_entry} = $index; # compat

  return $entries->[$index];
}

sub all_entries { goto &entries } # compat

sub count {
  my $self = shift;
  scalar entries($self);
}

sub shift_entry {
  my $self = shift;

  entry($self, 0) ? shift @{$self->{entries}} : undef;
}

sub pop_entry {
  my $self = shift;

  entry($self, 0) ? pop @{$self->{entries}} : undef;
}

sub sorted {
  my $self = shift;

  $self->sync unless exists $self->{resultCode};

  return unless exists $self->{entries} && ref($self->{entries});

  return @{$self->{entries}} unless @{$self->{entries}} > 1;

  require Net::LDAP::Util;

  map { $_->[0] }
    sort {
      my $v;
      my $i = 2;
      foreach my $attr (@_) {
	$v = ($a->[$i] ||= join("\000", @{$a->[0]->get_value($attr, asref => 1) || []}))
	      cmp
	     ($b->[$i] ||= join("\000", @{$b->[0]->get_value($attr, asref => 1) || []}))
	  and last;
	$i++;
      }

      $v ||= ($a->[1] ||= Net::LDAP::Util::canonical_dn( $a->[0]->dn, "reverse" => 1, separator => "\0"))
		cmp
	     ($b->[1] ||= Net::LDAP::Util::canonical_dn( $b->[0]->dn, "reverse" => 1, separator => "\0"));
    }
    map { [ $_ ] } @{$self->{entries}};
}

sub references {
  my $self = shift;

  $self->sync unless exists $self->{resultCode};

  return unless exists $self->{'reference'} && ref($self->{'reference'});

  @{$self->{'reference'} || []}
}

sub as_struct {
  my $self = shift;
  my %result = map { ( $_->dn, ($_->{'attrs'} || $_->_build_attrs) ) } entries($self);
  return \%result;
}

sub entries {
  my $self = shift;

  $self->sync unless exists $self->{resultCode};

  @{$self->{entries} || []}
}

package Net::LDAP::Reference;

sub references {
  my $self = shift;

  @{$self}
}


1;
