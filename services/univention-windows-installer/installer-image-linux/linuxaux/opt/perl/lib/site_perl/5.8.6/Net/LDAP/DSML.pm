# Copyright (c) 2002-2004 Graham Barr. All rights reserved. This program is
# free software; you can redistribute it and/or modify it under the same
# terms as Perl itself.

package Net::LDAP::DSML;

use strict;
use vars qw(@ISA $VERSION);
use Carp;
use XML::SAX::Base;
use Net::LDAP::Entry;

@ISA = qw(XML::SAX::Base);
$VERSION = "0.12";

# OO purists will hate this :)
my %schema_typemap = qw(
	attribute-type		at
	objectclass-type	oc
);
#	syn
#	mr
#	mru
#	dts
#	dtc
#	nfm

sub new {
  my $pkg = shift;
  my %opt = @_;

  my $sax;

  if ($sax = $opt{output}) {
    unless (ref($sax) and eval { $sax->isa('XML::SAX::Base') }) {
      require XML::SAX::Writer;
      $sax = XML::SAX::Writer->new( Output => $sax );
    }

    $sax = Net::LDAP::DSML::pp->new( handler => $sax )
      if $opt{pretty_print};
  }
  else {
    $sax = Net::LDAP::DSML::output->new;
  }

  bless { @_, handler => $sax }, $pkg;
}

sub start_document {
  my ($self, $data) = @_;
  $self->{reader} = {};
}

my %start_jumptable = qw(
	entry			entry
	attr			entry_attr
	objectclass		entry_attr
	value			entry_value
	oc-value		entry_value
	directory-schema	schema
	attribute-type		schema_element
	objectclass-type	schema_element
	name			schema_name
	object-identifier	schema_value
	syntax			schema_syntax
	description		schema_value
	equality		schema_value
	substring		schema_value
	ordering		schema_value
	attribute		schema_attr
);

sub start_element {
  my ($self, $data) = @_;
  
  (my $tag = lc $data->{Name}) =~ s/^dsml://;

  my $label = $start_jumptable{$tag} or return;
  my $state = $self->{reader};
  goto $label;

entry:
  {
    $state->{entry} = { objectName => $data->{Attributes}{'{}dn'}{Value} };
    return;
  }

entry_attr:
  {
    my $name = $tag eq 'objectclass' ? $tag : lc $data->{Attributes}{'{}name'}{Value};
    $state->{attr} = $state->{attrs}{$name}
      ||= do {
	my $aref = [];
	push @{$state->{entry}{attributes}}, {
	  type => $data->{Attributes}{'{}name'}{Value},
	  vals => $aref
	};
	$aref;
      };
    return;
  }

entry_value:
  {
    push @{$state->{attr}}, '';
    $state->{value} = \${$state->{attr}}[-1];
    $state->{encoding} = $data->{Attributes}{'{}encoding'}{Value} || '';
    return;
  }

schema:
  {
    $state->{schema} = {};
    return;
  }

schema_element:
  {
    my $Attrs = $data->{Attributes};
    my $id = $Attrs->{'{}id'}{Value};
    my $elem = $state->{elem} = { type => $schema_typemap{$tag} };
    $state->{id}{$id} = $elem if $id;

    my $value;

    if (defined($value = $Attrs->{"{}type"}{Value})) {
      $elem->{lc $value} = 1;
    }

    foreach my $attr (qw(
	single-value
	obsolete
	user-modification
    )) {
      my $value = $Attrs->{"{}$attr"}{Value};
      $elem->{$attr} = 1 if defined $value and $value =~ /^true$/i;
    }

    $elem->{superior} = $value
      if defined($value = $Attrs->{"{}superior"}{Value});

    return;
  }

schema_name:
  {
    my $elem = $state->{elem};
    push @{$elem->{name}}, '';
    $state->{value} = \${$elem->{name}}[-1];
    return;
  }

schema_syntax:
  {
    my $elem = $state->{elem};
    my $bound = $data->{Attributes}{'{}bound'}{Value};
    $elem->{max_length} = $bound if defined $bound;

    $elem->{$tag} = '' unless exists $elem->{$tag};
    $state->{value} = \$elem->{$tag};
    return;
  }

schema_value:
  {
    my $elem = $state->{elem};
    $elem->{$tag} = '' unless exists $elem->{$tag};
    $state->{value} = \$elem->{$tag};
    return;
  }

schema_attr:
  {
    my $Attrs = $data->{Attributes};
    my $required = $data->{Attributes}{'{}required'}{Value} || 'false';
    my $ref = $data->{Attributes}{'{}ref'}{Value} or return;
    my $type = $required =~ /^false$/i ? 'may' : 'must';
    push @{$state->{elem}{$type}}, $ref;
    return;
  }
}

my %end_jumptable = qw(
	entry			entry
	attr			entry_attr
	objectclass		entry_attr
	value			value
	oc-value		value
	syntax			value
	description		value
	equality		value
	substring		value
	ordering		value
	name			value
	object-identifier	value
	attribute-type		schema_element
	objectclass-type	schema_element
	directory-schema	schema
);

sub end_element {
  my ($self, $data) = @_;
  (my $tag = lc $data->{Name}) =~ s/^dsml://;

  my $label = $end_jumptable{$tag} or return;
  my $state = $self->{reader};
  goto $label;

entry:
  {
    my $entry = Net::LDAP::Entry->new;
    $entry->{asn} = delete $state->{entry};
    if (my $handler = $self->{entry}) {
      $handler->($entry);
    }
    else {
      push @{$state->{entries}}, $entry;
    }
    return;
  }

entry_attr:
  {
    delete $state->{attr};
    return;
  }

value:
  {
    delete $state->{value};
    delete $state->{encoding};
    return;
  }

schema_element:
  {
    my $elem = delete $state->{elem};
    my $oid  = $elem->{oid};
    my $name;

    if (my $aliases = $elem->{name}) {
      $name = $elem->{name} = shift @$aliases;
      $elem->{aliases} = $aliases if @$aliases;
    }
    elsif ($oid) {
      $name = $oid;
    }
    else {
	croak "Schema element without a name or object-identifier";
    }

    $elem->{oid} ||= $name;
    $state->{schema}{oid}{$oid} = $state->{schema}{$elem->{type}}{lc $name} = $elem;
 
    return;
  }

schema:
  {
    my $id = $state->{id};
    my $schema = $state->{schema};
    foreach my $elem (values %{$schema->{oc}}) {
      if (my $sup = $elem->{superior}) {
        $sup =~ /#(.*)|(.*)/;
	if (my $ref = $id->{$+}) {
	  $elem->{superior} = $ref->{name};
	}
	else {
	  $elem->{superior} = $+;
	}
      }
      foreach my $mm (qw(must may)) {
	if (my $mmref = $elem->{$mm}) {
	  my @mm = map {
	    /#(.*)|(.*)/;
	    my $ref = $id->{$+};
	    $ref ? $ref->{name} : $+;
	  } @$mmref;
	  $elem->{$mm} = \@mm;
	}
      }
    }
    require Net::LDAP::Schema;
    bless $schema, 'Net::LDAP::Schema'; # Naughty :-)
    if (my $handler = $self->{schema}) {
      $handler->($schema);
    }
    return;
  }

}

sub characters {
  my ($self, $data) = @_;
  my $state = $self->{reader};
  if (my $sref = $state->{value}) {
    $$sref = ($state->{encoding}||'') eq 'base64'
	? do { require MIME::Base64; MIME::Base64::decode_base64($data->{Data}) }
	: $data->{Data};
  }
}

sub _dsml_context {
  my ($self, $new) = @_;
  my $context = $self->{writer}{context};
  my $handler = $self->{handler};

  unless ($context) {
    $context = $self->{writer}{context} = [];
    $handler->start_document;

    $handler->xml_decl({
      Standalone => '',
      Version    => '1.0',
      Encoding   => 'utf-8'
    });
  }

  while (@$context and ($context->[-1] ne 'dsml' or $new eq '')) {
    my $old = pop @$context;
    $handler->end_element({
      Name         => "dsml:$old",
      LocalName    => $old,
      NamespaceURI => 'http://www.dsml.org/DSML',
      Prefix       => 'dsml'
    });

    $handler->end_prefix_mapping({
      NamespaceURI => 'http://www.dsml.org/DSML',
      Prefix       => 'dsml'
    }) if $old eq 'dsml';
  }

  if (!$new) {
    $handler->end_document;
    delete $self->{writer}{context};
  }
  elsif (!@$context or $context->[-1] ne $new) {
    $self->_dsml_context('dsml') unless $new eq 'dsml' or @$context;
    push @$context, $new;
    my %data = (
      Name	   => "dsml:$new",
      LocalName	   => $new,
      NamespaceURI => 'http://www.dsml.org/DSML',
      Prefix	   => 'dsml',
    );

    if ($new eq 'dsml') {
      $handler->start_prefix_mapping({
	NamespaceURI => 'http://www.dsml.org/DSML',
	Prefix       => 'dsml'
      });
      $data{Attributes} = {
	'{http://www.w3.org/2000/xmlns/}dsml' => {
	  Name         => 'xmlns:dsml',
	  LocalName    => 'dsml',
	  NamespaceURI => 'http://www.w3.org/2000/xmlns/',
	  Value        => 'http://www.dsml.org/DSML',
	  Prefix       => 'xmlns'
	}
      };
    }
    $handler->start_element(\%data);
  }
}

sub start_dsml {
  my $self = shift;

  $self->_dsml_context('') if $self->{writer}{context};
  $self->_dsml_context('dsml');
}

sub end_dsml {
  my $self = shift;
  $self->_dsml_context('') if $self->{writer} and $self->{writer}{context};
}

sub write_entry {
  my $self = shift;
  my $handler = $self->{handler};

  $self->_dsml_context('directory-entries');

  my %attr;
  my %data = (
    NamespaceURI => 'http://www.dsml.org/DSML',
    Prefix       => 'dsml',
    Attributes   => \%attr,
  );
  foreach my $entry (@_) {
    my $asn = $entry->asn;
    @data{qw(Name LocalName)} = qw(dsml:entry entry);
    %attr = ( '{}dn' => { Value => $asn->{objectName}, Name => "dn"} );
    $handler->start_element(\%data);

    foreach my $attr ( @{$asn->{attributes}} ) {
      my $name = $attr->{type};
      my $is_oc = lc($name) eq "objectclass";

      if ($is_oc) {
	@data{qw(Name LocalName)} = qw(dsml:objectclass objectclass);
	%attr = ();
	$handler->start_element(\%data);
	@data{qw(Name LocalName)} = qw(dsml:oc-value oc-value);
      }
      else {
	@data{qw(Name LocalName)} = qw(dsml:attr attr);
	%attr = ( "{}name" => { Value => $name, Name => "name" } );
	$handler->start_element(\%data);
	@data{qw(Name LocalName)} = qw(dsml:value value);
      }

      my %chdata;
      foreach my $val (@{$attr->{vals}}) {
	if ($val =~ /(^[ :]|[\x00-\x1f\x7f-\xff])/) {
	  require MIME::Base64;
	  $chdata{Data} = MIME::Base64::encode($val,"");
	  %attr = ( '{}encoding' => { Value => 'base64', Name => "encoding"} );
	}
	else {
	  $chdata{Data} = $val;
	  %attr = ();
	}
	$handler->start_element(\%data);
	$handler->characters(\%chdata);
	%attr = ();
	$handler->end_element(\%data);
      }

      @data{qw(Name LocalName)} = $is_oc
	? qw(dsml:objectclass objectclass)
	: qw(dsml:attr attr);
      %attr = ();
      $handler->end_element(\%data);
    }

    @data{qw(Name LocalName)} = qw(dsml:entry entry);
    %attr = ();
    $handler->end_element(\%data);
  }
}

sub write_schema {
  my ($self, $schema) = @_;
  my $handler = $self->{handler};

  $self->_dsml_context('dsml');
  my %attr;
  my %data = (
    NamespaceURI => 'http://www.dsml.org/DSML',
    Prefix       => 'dsml',
    Attributes   => \%attr,
  );
  @data{qw(Name LocalName)} = qw(dsml:directory-schema directory-schema);
  $handler->start_element(\%data);
  my %id;

  foreach my $attr ($schema->all_attributes) {
    $id{$attr->{name}} = 1;
    %attr = ( '{}id' => { Value => "#$attr->{name}", Name => 'id'});

    if (my $sup = $attr->{superior}) {
      my $sup_a = $schema->attribute($sup);
      $attr{"{}superior"} = {
	Value => "#" . ($sup_a ? $sup_a->{name} : $sup),
	Name  => 'superior'
      };
    }
    foreach my $flag (qw(obsolete single-value)) {
      $attr{"{}$flag"} = {
	Value => 'true', Name => $flag
      } if $attr->{$flag};
    }
    $attr{"{}user-modification"} = {
      Value => 'false',
      Name => 'user-modification',
    } unless $attr->{'user-modification'};

    @data{qw(Name LocalName)} = qw(dsml:attribute-type attribute-type);
    $handler->start_element(\%data);
    %attr = ();
    unless (($attr->{name} || '') eq ($attr->{oid} || '')) {
      @data{qw(Name LocalName)} = qw(dsml:name name);
      $handler->start_element(\%data);
      $handler->characters({Data => $attr->{name}});
      $handler->end_element(\%data);
    }
    if (my $aliases = $attr->{aliases}) {
      @data{qw(Name LocalName)} = qw(dsml:name name);
      foreach my $name (@$aliases) {
	$handler->start_element(\%data);
	$handler->characters({Data => $name});
	$handler->end_element(\%data);
      }
    }
    if (my $oid = $attr->{oid}) {
      @data{qw(Name LocalName)} = ("dsml:object-identifier","object-identifier");
      $handler->start_element(\%data);
      $handler->characters({Data => $oid});
      $handler->end_element(\%data);
    }
    foreach my $elem (qw(
	description
	equality
	ordering
	substring
    )) {
      defined(my $text = $attr->{$elem}) or next;
      @data{qw(Name LocalName)} = ("dsml:$elem",$elem);
      $handler->start_element(\%data);
      $handler->characters({Data => $text});
      $handler->end_element(\%data);
    }
    if (my $syn = $attr->{syntax}) {
      if (defined(my $bound = $attr->{max_length})) {
	$attr{'{}bound'} = {
	  Value => $bound,
	  Name => 'bound',
	};
      }
      @data{qw(Name LocalName)} = qw(dsml:syntax syntax);
      $handler->start_element(\%data);
      $handler->characters({Data => $syn});
      $handler->end_element(\%data);
    }
    @data{qw(Name LocalName)} = qw(dsml:attribute-type attribute-type);
    $handler->end_element(\%data);
  }

  foreach my $oc ($schema->all_objectclasses) {
    my $id = $oc->{name};
    $id = $oc->{'object-identifier'} if $id{$id};

    %attr = ( '{}id' => { Value => "#$id", Name => 'id'});

    if (my $sup = $oc->{superior}) {
      my $sup_a = $schema->objectclass($sup);
      $attr{"{}superior"} = {
	Value => "#" . ($sup_a ? $sup_a->{name} : $sup),
	Name  => 'superior'
      };
    }
    if (my $type = (grep { $oc->{$_} } qw(structural abstract auxilary))[0]) {
      $attr{"{}type"} = {
	Value => $type,
	Name  => 'type',
      };
    }
    if ($oc->{obsolete}) {
      $attr{"{}type"} = {
	Value => 'true',
	Name  => 'obsolete',
      };
    }

    @data{qw(Name LocalName)} = qw(dsml:objectclass-type objectclass-type);
    $handler->start_element(\%data);
    %attr = ();

    unless (($oc->{name} || '') eq ($oc->{'object-identifier'} || '')) {
      @data{qw(Name LocalName)} = qw(dsml:name name);
      $handler->start_element(\%data);
      $handler->characters({Data => $oc->{name}});
      $handler->end_element(\%data);
    }
    if (my $aliases = $oc->{aliases}) {
      @data{qw(Name LocalName)} = qw(dsml:name name);
      foreach my $name (@$aliases) {
	$handler->start_element(\%data);
	$handler->characters({Data => $name});
	$handler->end_element(\%data);
      }
    }
    foreach my $elem (qw(
	description
	object-identifier
    )) {
      defined(my $text = $oc->{$elem}) or next;
      @data{qw(Name LocalName)} = ("dsml:$elem",$elem);
      $handler->start_element(\%data);
      $handler->characters({Data => $text});
      $handler->end_element(\%data);
    }
    @data{qw(Name LocalName)} = qw(dsml:attribute attribute);
    foreach my $mm (qw(must may)) {
      %attr = (
	'{}required' => {
	  Value => ($mm eq 'must' ? 'true' : 'false'),
	  Name => 'required'
	},
	'{}ref' => {
	  Name => 'ref'
	},
      );
      my $mmref = $oc->{$mm} or next;
      foreach my $attr (@$mmref) {
	my $a_ref = $schema->attribute($attr);
	$attr{'{}ref'}{Value} = $a_ref ? $a_ref->{name} : $attr;
	$handler->start_element(\%data);
	$handler->end_element(\%data);
      }
    }

    @data{qw(Name LocalName)} = qw(dsml:objectclass-type objectclass-type);
    $handler->end_element(\%data);
  }

  %attr = ();
  @data{qw(Name LocalName)} = qw(dsml:directory-schema directory-schema);
  $handler->end_element(\%data);
}


package Net::LDAP::DSML::pp;

sub new {
  my $pkg = shift;
  bless { @_ }, $pkg;
}

sub start_element {
  my ($self, $data) = @_;
  my $handler = $self->{handler};
  $handler->start_element($data);
  unless ($data->{Name} =~ /^(?:dsml:)?(?:
	 value
	|oc-value
	|name
	|syntax
	|equality
	|substring
	|object-identifier
	|description
	|ordering
	|attribute
	)$/ix
  ) {
    $handler->ignorable_whitespace({Data => "\n"});
  }
}

sub end_element {
  my $self = shift;
  my $handler = $self->{handler};
  $handler->end_element(@_);
  $handler->ignorable_whitespace({Data => "\n"});
}

sub xml_decl {
  my $self = shift;
  my $handler = $self->{handler};
  $handler->xml_decl(@_);
  $handler->ignorable_whitespace({Data => "\n"});
}

use vars qw($AUTOLOAD);

sub DESTROY {}

sub AUTOLOAD {
  (my $meth = $AUTOLOAD) =~ s/^.*:://;
  no strict 'refs';
  *{$meth} = sub { shift->{handler}->$meth(@_) };
  goto &$meth;
}

package Net::LDAP::DSML::output;

sub new { bless {} }

use vars qw($AUTOLOAD);

sub DESTROY {}

sub AUTOLOAD {
  (my $meth = $AUTOLOAD) =~ s/^.*:://;
  require XML::SAX::Writer;
  my $self = shift;
  $self->{handler} = XML::SAX::Writer->new;
  bless $self, 'Net::LDAP::DSML::pp';
  $self->$meth(@_);
}

1;

__END__

=head1 NAME

NET::LDAP::DSML -- A DSML Writer for Net::LDAP

=head1 SYNOPSIS

 For a directory entry;

 use Net::LDAP;
 use Net::LDAP::DSML;
 use IO::File;


 my $server = "localhost";
 my $file = "testdsml.xml";
 my $ldap = Net::LDAP->new($server);
 
 $ldap->bind();


 #
 # For file i/o
 #
 my $file = "testdsml.xml";

 my $io = IO::File->new($file,"w") or die ("failed to open $file as filehandle.$!\n");

 my $dsml = Net::LDAP::DSML->new(output => $io, pretty_print => 1 )
      or die ("DSML object creation problem using an output file.\n");
 #      OR
 #
 # For file i/o
 #

 open (IO,">$file") or die("failed to open $file.$!");

 my $dsml = Net::LDAP::DSML->new(output => *IO, pretty_print => 1)
     or die ("DSML object creation problem using an output file.\n");

 #      OR
 #
 # For array usage.
 # Pass a reference to an array.
 #

 my @data = ();
 $dsml = Net::LDAP::DSML->new(output => \@data, pretty_print => 1) 
     or die ("DSML object cration problem using an output array.\n");


  my $mesg = $ldap->search(
                           base     => 'o=airius.com',
                           scope    => 'sub',
                           filter   => 'ou=accounting',
                           callback => sub {
					 my ($mesg,$entry) =@_;
					 $dsml->write_entry($entry) 
                                          if (ref $entry eq 'Net::LDAP::Entry');
				       }
                            );  

 die ("search failed with ",$mesg->code(),"\n") if $mesg->code();

 For directory schema;

 A file or array can be used for output, in the following example
 only an array will be used.

 my $schema = $ldap->schema();
 my @data = ();
 my $dsml = Net::LDAP::DSML->new(output => \@data, pretty_print => 1 )
      or die ("DSML object creation problem using an output array.\n");
 
 $dsml->write_schema($schema);

 print "Finished printing DSML\n";

=head1 DESCRIPTION

Directory Service Markup Language (DSML) is the XML standard for
representing directory service information in XML.

At the moment this module only writes DSML entry and schema entities. 
Reading DSML entities is a future project.

Eventually this module will be a full level 2 consumer and producer
enabling you to give you full DSML conformance.  Currently this 
module has the ability to be a level 2 producer.  The user must 
understand the his/her directory server will determine the 
consumer and producer level they can achieve.  

To determine conformance, it is useful to divide DSML documents into 
four types:

  1.Documents containing no directory schema nor any references to 
    an external schema. 
  2.Documents containing no directory schema but containing at 
    least one reference to an external schema. 
  3.Documents containing only a directory schema. 
  4.Documents containing both a directory schema and entries. 

A producer of DSML must be able to produce documents of type 1.
A producer of DSML may, in addition, be able to produce documents of 
types 2 thru 4.

A producer that can produce documents of type 1 is said to be a level 
1 producer. A producer than can produce documents of all four types is 
said to be a level 2 producer.

=head1 CALLBACKS

The module uses callbacks to improve performance (at least the appearance
of improving performance ;) and to reduce the amount of memory required to
parse large DSML files. Every time a single entry or schema is processed
we pass the Net::LDAP object (either an Entry or Schema object) to the
callback routine.

=head1 CONSTRUCTOR 

=over 4

=item new ()

Creates a new Net::LDAP::DSML object.  There are 2 options
to this method.

OUTPUT is a reference to either a file handle that has already
been opened or to an array.

PRETTY_PRINT is an option to print a new line at the end of
each element sequence.  It makes the reading of the XML output
easier for a human.

B<Example>

  my $dsml = Net::LDAP::DSML->new();  
  Prints xml data to standard out.

  my $dsml = Net::LDAP::DSML->new(output => \@array);  
  my $dsml = Net::LDAP::DSML->new(output => *FILE);  
  Prints xml data to a file or array.

  my $dsml = Net::LDAP::DSML->new(output => \@array, pretty_print => 1);  
  my $dsml = Net::LDAP::DSML->new(output => *FILE, pretty_print => 1);  
  Prints xml data to a file or array in pretty print style.

=back


=head1 METHODS

=over 4

=item start_dsml ()

Start a DSML file.

=item end_dsml ()

End a DSML file.

=item write_entry ( ENTRY )

Entry is a Net::LDAP::Entry object. The write method will parse
the LDAP data in the Entry object and put it into DSML XML
format.

B<Example>

  my $entry = $mesg->entry();
  $dsml->write_entry($entry);

=item write_schema ( SCHEMA )

Schema is a Net::LDAP::Schema object. The write_schema method will 
parse the LDAP data in the Schema object and put it into DSML XML
format.

B<Example>

  my $schema = $ldap->schema();
  $dsml->write_schema($schema);

=back

=head1 AUTHOR

Graham Barr   gbarr@pobox.com

=head1 SEE ALSO

L<Net::LDAP>,
L<XML::SAX::Base>

=head1 COPYRIGHT

Copyright (c) 2002-2004 Graham Barr. All rights reserved. This program is
free software; you can redistribute it and/or modify it under the same
terms as Perl itself.

=cut


