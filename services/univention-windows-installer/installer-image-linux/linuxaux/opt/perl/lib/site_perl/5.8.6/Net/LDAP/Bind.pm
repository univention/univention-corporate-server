# Copyright (c) 1998-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package Net::LDAP::Bind;

use strict;
use Net::LDAP qw(LDAP_SASL_BIND_IN_PROGRESS LDAP_DECODING_ERROR LDAP_SUCCESS);
use Net::LDAP::Message;
use vars qw(@ISA $VERSION);

$VERSION = "1.02";
@ISA = qw(Net::LDAP::Message);

sub _sasl_info {
  my $self = shift;
  @{$self}{qw(dn saslctrl sasl)} = @_;
}

sub decode {
  my $self = shift;
  my $result = shift;
  my $bind = $result->{protocolOp}{bindResponse}
     or $self->set_error(LDAP_DECODING_ERROR,"LDAP decode error")
    and return;

  my $sasl = $self->{sasl};
  my $ldap = $self->parent;

  $ldap->{net_ldap_socket} = $sasl->securesocket($ldap->{net_ldap_socket})
    if $sasl and $bind->{resultCode} == LDAP_SUCCESS;

  return $self->SUPER::decode($result)
    unless $bind->{resultCode} == LDAP_SASL_BIND_IN_PROGRESS;

  # tell our LDAP client to forget us as this message has now completed
  # all communications with the server
  $ldap->_forgetmesg($self);

  $self->{mesgid} = Net::LDAP::Message->NewMesgID(); # Get a new message ID

  my ($resp) = $sasl->client_step($bind->{serverSaslCreds})
    or $self->set_error(LDAP_DECODING_ERROR,"LDAP decode error"), return;

  $self->encode(
    bindRequest => {
    version => $ldap->version,
    name    => $self->{dn},
    authentication => {
      sasl    => {
        mechanism   => $sasl->mechanism,
        credentials => $resp
      }
    },
    control => $self->{saslcontrol}
  });

  $ldap->_sendmesg($self);
}

1;
