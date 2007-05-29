# 	$Id: StarDumper.pm,v 1.2 2003/09/08 07:14:37 thorsten Exp $	
package Unidump::StarDumper;
use base qw(Unidump::GenericDumper);
use strict;
use POSIX;
use IO::File;
use Unidump::Logger qw(logmessage logmessage_debug);
use vars qw($VERSION);
$VERSION = do{my @r = split(" ",qq$Revision: 1.2 $ );$r[1];};


sub check {
  logmessage_debug("StarDumper::check: @_");
  my $self = shift;
  my ($rc, $out);
  ($rc, $out) = $self->checkcmd($self->star);
  die "command not found: " . $self->star if $rc;
  $self->SUPER::check;
}
	
sub dumpcmdline {
  logmessage_debug("StarDumper::dumpcmdline: @_");
  my $self = shift;
  my $cmdline = $self->ext2dump;
  return $cmdline;
}

sub sizecmdline {
  logmessage_debug("StarDumper::sizecmdline: @_");
    my $self = shift;
    my $cmdline = $self->ext2dump;
  return $cmdline;
}

sub listcmdline {
  logmessage_debug("StarDumper::listcmdline: @_");
    my $self = shift;
    my $cmdline = $self->ext2restore;
  return $cmdline;
}

1;
__END__
