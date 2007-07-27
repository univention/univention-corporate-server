# Copyright (c) 1998-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Schema;

use strict;
use vars qw($VERSION);

$VERSION = "0.9903";

#
# Get schema from the server (or read from LDIF) and parse it into
# data structure
#
sub new {
  my $self = shift;
  my $type = ref($self) || $self;
  my $schema = bless {}, $type;

  @_ ? $schema->parse(@_) : $schema;
}

sub _error {
  my $self = shift;
  $self->{error} = shift;
  return;
}


sub parse {
  my $schema = shift;
  my $arg = shift;

  unless (defined($arg)) {
    $schema->_error('Bad argument');
    return undef;
  }

  %$schema = ();

  my $entry;
  if( ref $arg ) {
    if (UNIVERSAL::isa($arg, 'Net::LDAP::Entry')) {
      $entry = $arg;
    }
    elsif (UNIVERSAL::isa($arg, 'Net::LDAP::Search')) {
      unless ($entry = $arg->entry) {
	$schema->_error('Bad Argument');
	return undef;
      }
    }
    else {
      $schema->_error('Bad Argument');
      return undef;
    }
  }
  elsif( -f $arg ) {
    require Net::LDAP::LDIF;
    my $ldif = Net::LDAP::LDIF->new( $arg, "r" );
    $entry = $ldif->read();
    unless( $entry ) {
      $schema->_error("Cannot parse LDIF from file [$arg]");
      return undef;
    }
  }
  else {
    $schema->_error("Can't load schema from [$arg]: $!");
    return undef;
  }

  eval {
    local $SIG{__DIE__} = sub {};
    _parse_schema( $schema, $entry );
  };

  if ($@) {
    $schema->_error($@);
    return undef;
  }

  return $schema;
}

#
# Dump as LDIF
#
# XXX - We should really dump from the internal structure. That way we can
#       have methods to modify the schema and write a new one -- GMB
sub dump {
  my $self = shift;
  my $fh = @_ ? shift : \*STDOUT;
  my $entry = $self->{'entry'} or return;
  require Net::LDAP::LDIF;
  Net::LDAP::LDIF->new($fh,"w", wrap => 0)->write($entry);
  1;
}

#
# Given another Net::LDAP::Schema, merge the contents together.
# XXX - todo
#
sub merge {
  my $self = shift;
  my $new = shift;

  # Go through structure of 'new', copying code to $self. Take some
  # parameters describing what to do in the event of a clash.
}


sub all_attributes		{ values %{shift->{at}}  }
sub all_objectclasses		{ values %{shift->{oc}}  }
sub all_syntaxes		{ values %{shift->{syn}} }
sub all_matchingrules		{ values %{shift->{mr}}  }
sub all_matchingruleuses	{ values %{shift->{mru}} }
sub all_ditstructurerules	{ values %{shift->{dts}} }
sub all_ditcontentrules		{ values %{shift->{dtc}} }
sub all_nameforms		{ values %{shift->{nfm}} }

sub superclass {
  my $self = shift;
  my $oc = shift;

  my $elem = $self->objectclass( $oc )
    or return scalar _error($self, "Not an objectClass");

  return @{$elem->{sup} || []};
}

sub must { _must_or_may(@_,'must') }
sub may  { _must_or_may(@_,'may')  }

#
# Return must or may attributes for this OC.
#
sub _must_or_may {
  my $self = shift;
  my $must_or_may = pop;
  my @oc = @_ or return;

  #
  # If called with an entry, get the OC names and continue
  #
  if ( ref($oc[0]) && UNIVERSAL::isa( $oc[0], "Net::LDAP::Entry" ) ) {
    my $entry = $oc[0];
    @oc = $entry->get_value( "objectclass" )
      or return;
  }

  my %res;
  my %done;

  while (@oc) {
    my $oc = shift @oc;

    $done{lc $oc}++ and next;

    my $elem = $self->objectclass( $oc ) or next;
    if (my $res  = $elem->{$must_or_may}) {
    @res{ @$res } = (); 	# Add in, getting uniqueness
    }
    my $sup = $elem->{sup} or next;
    push @oc, @$sup;
  }

  my %unique = map { ($_,$_) } $self->attribute(keys %res);
  values %unique;
}

#
# Given name or oid, return element or undef if not of appropriate type
#

sub _get {
  my $self = shift;
  my $type = pop(@_);
  my $hash = $self->{$type};
  my $oid  = $self->{oid};

  my @elem = grep $_, map {
    my $elem = $hash->{lc $_};

    ($elem or ($elem = $oid->{$_} and $elem->{type} eq $type))
      ? $elem
      : undef;
  } @_;

  wantarray ? @elem : $elem[0];
}

sub attribute		{ _get(@_,'at')  }
sub objectclass		{ _get(@_,'oc')  }
sub syntax		{ _get(@_,'syn') }
sub matchingrule	{ _get(@_,'mr')  }
sub matchingruleuse	{ _get(@_,'mru') }
sub ditstructurerule	{ _get(@_,'dts') }
sub ditcontentrule	{ _get(@_,'dtc') }
sub nameform		{ _get(@_,'nfm') }


#
# XXX - TODO - move long comments to POD and write up interface
#
# Data structure is:
#
# $schema (hash ref)
#
# The {oid} piece here is a little redundant since we control the other
# top-level members. We promote the first listed name to be 'canonical' and
# also make up a name for syntaxes (from the description). Thus we always
# have a unique name. This avoids a lot of checking in the access routines.
#
# ->{oid}->{$oid}->{
#			name	=> $canonical_name, (created for syn)
#			aliases	=> list of non. canon names
#			type	=> at/oc/syn
#			desc	=> description
#			must	=> list of can. names of mand. atts [if OC]
#			may	=> list of can. names of opt. atts [if OC]
#			syntax	=> can. name of syntax [if AT]
#			... etc per oid details
#
# These next items are optimisations, to avoid always searching the OID
# lists. Could be removed in theory. Each is a hash ref mapping
# lowercase names to the hash stored in the oid struucture
#
# ->{at}
# ->{oc}
# ->{syn}
# ->{mr}
# ->{mru}
# ->{dts}
# ->{dtc}
# ->{nfm}
#

#
# These items have no following arguments
#
my %flags = map { ($_,1) } qw(
			      single-value
			      obsolete
			      collective
			      no-user-modification
			      abstract
			      structural
			      auxiliary
			     );

#
# These items can have lists arguments
# (name can too, but we treat it special)
#
my %listops = map { ($_,1) } qw(must may sup);

#
# Map schema attribute names to internal names
#
my %type2attr = qw(
	at	attributetypes
	oc	objectclasses
	syn	ldapsyntaxes
	mr	matchingrules
	mru	matchingruleuse
	dts	ditstructurerules
	dtc	ditcontentrules
	nfm	nameforms
);

#
# Return ref to hash containing schema data - undef on failure
#

sub _parse_schema {
  my $schema = shift;
  my $entry = shift;

  return undef unless defined($entry);

  keys %type2attr; # reset iterator
  while(my($type,$attr) = each %type2attr) {
    my $vals = $entry->get_value($attr, asref => 1);

    my %names;
    $schema->{$type} = \%names;		# Save reference to hash of names => element

    next unless $vals;			# Just leave empty ref if nothing

    foreach my $val (@$vals) {
      #
      # The following statement takes care of defined attributes
      # that have no data associated with them.
      #
      next if $val eq '';

      #
      # We assume that each value can be turned into an OID, a canonical
      # name and a 'schema_entry' which is a hash ref containing the items
      # present in the value.
      #
      my %schema_entry = ( type => $type, aliases => [] );

      my @tokens;
      pos($val) = 0;

      push @tokens, $+
        while $val =~ /\G\s*(?:
                       ([()])
                      |
                       ([^"'\s()]+)
                      |
                       "([^"]*)"
                      |
                       '((?:[^']+|'[^\s)])*)'
                      )\s*/xcg;
      die "Cannot parse [$val] [",substr($val,pos($val)),"]" unless @tokens and pos($val) == length($val);

      # remove () from start/end
      shift @tokens if $tokens[0]  eq '(';
      pop   @tokens if $tokens[-1] eq ')';

      # The first token is the OID
      my $oid = $schema_entry{oid} = shift @tokens;

      while(@tokens) {
	my $tag = lc shift @tokens;

	if (exists $flags{$tag}) {
	  $schema_entry{$tag} = 1;
	}
	elsif (@tokens) {
	  if (($schema_entry{$tag} = shift @tokens) eq '(') {
	    my @arr;
	    $schema_entry{$tag} = \@arr;
	    while(1) {
	      my $tmp = shift @tokens;
	      last if $tmp eq ')';
	      push @arr,$tmp unless $tmp eq '$';

              # Drop of end of list ?
	      die "Cannot parse [$val] {$tag}" unless @tokens;
	    }
	  }

          # Ensure items that can be lists are stored as array refs
	  $schema_entry{$tag} = [ $schema_entry{$tag} ]
	    if exists $listops{$tag} and !ref $schema_entry{$tag};
	}
        else {
          die "Cannot parse [$val] {$tag}";
        }
      }

      #
      # Extract the maximum length of a syntax
      #
      $schema_entry{max_length} = $1
	if exists $schema_entry{syntax} and $schema_entry{syntax} =~ s/{(\d+)}//;

      #
      # Force a name if we don't have one
      #
      $schema_entry{name} = $schema_entry{oid}
	unless exists $schema_entry{name};

      #
      # If we have multiple names, make the name be the first and demote the rest to aliases
      #
      if (ref $schema_entry{name}) {
	my $aliases;
	$schema_entry{name} = shift @{$aliases = $schema_entry{name}};
	$schema_entry{aliases} = $aliases if @$aliases;
      }

      #
      # Store the elements by OID
      #
      $schema->{oid}->{$oid} = \%schema_entry;

      #
      # We also index elements by name within each type
      #
      foreach my $name ( @{$schema_entry{aliases}}, $schema_entry{name} ) {
	my $lc_name = lc $name;
	$names{lc $name} =  \%schema_entry;
      }
    }
  }

  $schema->{entry} = $entry;
  return $schema;
}




#
# Get the syntax of an attribute
#
sub attribute_syntax {
  my $self = shift;
  my $attr = shift;
  my $syntax;

  while ($attr) {
    my $elem = $self->attribute( $attr ) or return undef;

    $syntax = $elem->{syntax} and return $self->syntax($syntax);

    $attr = ${$elem->{sup} || []}[0];
  }

  return undef
}


sub error {
  $_[0]->{error};
}

#
# Return base entry
#
sub entry {
  $_[0]->{entry};
}

1;
