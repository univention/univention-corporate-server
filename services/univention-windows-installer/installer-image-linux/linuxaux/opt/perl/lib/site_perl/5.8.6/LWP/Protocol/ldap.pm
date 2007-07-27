# Copyright (c) 1998-2004 Graham Barr <gbarr@pobox.com>. All rights reserved.
# This program is free software; you can redistribute it and/or
# modify it under the same terms as Perl itself.

package LWP::Protocol::ldap;

use Carp ();

use HTTP::Status ();
use HTTP::Negotiate ();
use HTTP::Response ();
use LWP::MediaTypes ();
require LWP::Protocol;
@ISA = qw(LWP::Protocol);

$VERSION = "1.10";

use strict;
eval {
  require Net::LDAP;
};
my $init_failed = $@ ? $@ : undef;

sub request {
  my($self, $request, $proxy, $arg, $size, $timeout) = @_;

  $size = 4096 unless $size;

  LWP::Debug::trace('()');

  # check proxy
  if (defined $proxy)
  {
    return new HTTP::Response &HTTP::Status::RC_BAD_REQUEST,
                 'You can not proxy through the ldap';
  }

  my $url = $request->url;
  if ($url->scheme ne 'ldap') {
    my $scheme = $url->scheme;
    return new HTTP::Response &HTTP::Status::RC_INTERNAL_SERVER_ERROR,
            "LWP::Protocol::ldap::request called for '$scheme'";
  }

  # check method
  my $method = $request->method;

  unless ($method eq 'GET') {
    return new HTTP::Response &HTTP::Status::RC_BAD_REQUEST,
                 'Library does not allow method ' .
                 "$method for 'ldap:' URLs";
  }

  if ($init_failed) {
    return new HTTP::Response &HTTP::Status::RC_INTERNAL_SERVER_ERROR,
            $init_failed;
  }

  my $host     = $url->host;
  my $port     = $url->port;
  my ($user, $password) = split(":", $url->userinfo, 2);

  # Create an initial response object
  my $response = new HTTP::Response &HTTP::Status::RC_OK, "Document follows";
  $response->request($request);

  my $ldap = new Net::LDAP($host, port => $port);

  my $mesg = $ldap->bind($user, password => $password);

  if ($mesg->code) {
    my $res = new HTTP::Response &HTTP::Status::RC_BAD_REQUEST,
         "LDAP return code " . $ldap->code;
    $res->content_type("text/plain");
    $res->content($ldap->error);
    return $res;
  }

  my $dn = $url->dn;
  my @attrs = $url->attributes;
  my $scope = $url->scope || "base";
  my $filter = $url->filter;
  my @opts = (scope => $scope);
  
  push @opts, "base" => $dn if $dn;
  push @opts, "filter" => $filter if $filter;
  push @opts, "attrs" => \@attrs if @attrs;

  $mesg = $ldap->search(@opts);
  if ($mesg->code) {
    my $res = new HTTP::Response &HTTP::Status::RC_BAD_REQUEST,
         "LDAP return code " . $ldap->code;
    $res->content_type("text/plain");
    $res->content($ldap->error);
    return $res;
  }
  else {
    my $content = "<head><title>Directory Search Results</title></head>\n<body>";
    my $entry;
    my $index;

    for($index = 0 ; $entry = $mesg->entry($index) ; $index++ ) {
      my $attr;

      $content .= $index ? qq{<tr><th colspan="2"><hr>&nbsp</tr>\n} : "<table>";

      $content .= qq{<tr><th colspan="2">} . $entry->dn . "</th></tr>\n";

      foreach $attr ($entry->attributes) {
        my $vals = $entry->get_value($attr, asref => 1);
        my $val;

        $content .= q{<tr><td align="right" valign="top"};
        $content .= q{ rowspan="} . scalar(@$vals) . q{"}
          if (@$vals > 1);
        $content .= ">" . $attr  . "&nbsp</td>\n";

        my $j = 0;
        foreach $val (@$vals) {
	  $val = qq!<a href="$val">$val</a>! if $val =~ /^https?:/;
	  $val = qq!<a href="mailto:$val">$val</a>! if $val =~ /^[-\w]+\@[-.\w]+$/;
          $content .= "<tr>" if $j++;
          $content .= "<td>" . $val . "</td></tr>\n";
        }
      }
    }

    $content .= "</table>" if $index;
    $content .= "<hr>";
    $content .= $index ? sprintf("%s Match%s found",$index, $index>1 ? "es" : "")
		       : "<b>No Matches found</b>";
    $content .= "</body>\n";
    $response->header('Content-Type' => 'text/html');
    $response->header('Content-Length', length($content));
    $response = $self->collect_once($arg, $response, $content)
	if ($method ne 'HEAD');

  }

  $ldap->unbind;

  $response;
}

1;
