# Copyright (c) 1998-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Extension;

use vars qw(@ISA $VERSION);

@ISA = qw(Net::LDAP::Message);
$VERSION = "1.01";

#fetch the response name
sub response_name { 
  my $self = shift;

  $self->sync unless exists $self->{Code};

  exists $self->{responseName}
    ? $self->{responseName}
    : undef;
}

# fetch the response.
sub response {
  my $self = shift;

  $self->sync unless exists $self->{Code};

  exists $self->{response}
    ? $self->{response}
    : undef;
}

1;
