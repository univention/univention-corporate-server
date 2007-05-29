# 	$Id: Logger.pm,v 1.2 2003/09/08 07:14:37 thorsten Exp $	
package Unidump::Logger;
use strict;
use POSIX;
use Unix::Syslog qw(:macros :subs);
use IO::File;
use vars qw(@ISA @EXPORT @EXPORT_OK %EXPORT_TAGS $VERSION);
use Exporter;
$VERSION = do{my @r = split(" ",qq$Revision: 1.2 $ );$r[1];};
@ISA = qw(Exporter);

@EXPORT = qw();
@EXPORT_OK = qw(logmessage syslogmessage unilogmessage
		logmessage_debug syslogmessage_debug unilogmessage_debug);
%EXPORT_TAGS = (all => [@EXPORT_OK]);

use vars qw($debug $useunilog $usesyslog $unilogfile 
	    $sysloglevel $syslogfacility $sysloglabel
	    $usestderr);

$debug = 0;
$useunilog = 1;
$usestderr = 0;
$usesyslog = 1;
$unilogfile = "/var/log/unidump.log";

$sysloglevel = LOG_INFO;
$syslogfacility = LOG_USER;
$sysloglabel = "UNIDUMP";

sub logmessage {
  syslogmessage(@_);
  unilogmessage(@_);
  stderrmessage(@_);
}

sub logmessage_debug {
  my @caller = caller;
  if($debug) {
    print STDERR "DEBUG: @_ at @caller\n";
  }
}

sub syslogmessage {
  if($usesyslog) {
    openlog($sysloglabel, LOG_PID|LOG_CONS, $syslogfacility);
    syslog($sysloglevel, "@_");
    closelog();
  }
}

sub unilogmessage {
  if($useunilog) {
    my $mode = ">>";
    $mode = ">" unless -f $unilogfile;
    my $fh = IO::File->new($mode . $unilogfile) or 
      syslogmessage("cannot open logfile: $!"), $useunilog = 0, return;
    print($fh strftime("[%Y/%m/%d %T] ", localtime()), "@_\n") or
      syslogmessage("cannot write to logfile: $!"), $useunilog = 0, return;
    undef($fh);
  }
}

sub stderrmessage {
  if($usestderr) {
    print STDERR "@_\n";
  }
}


sub syslogmessage_debug {
  if($debug) {
    local $sysloglevel = LOG_DEBUG;
    syslogmessage(@_);
  }
}

sub unilogmessage_debug {
  if($debug) {
    unilogmessage("DEBUG: ", @_);
  }
}

sub stderrmessage_debug {
  if($debug) {
    stderrmessage("DEBUG: ", @_);
  }
}

1;

__END__

=head1 NAME

  Logger -- a package for UNIDUMP system logging

=head1 SYNOPSIS

  syslogmessage(@message);
  unilogmessage(@message);
  logmessage(@message);

  syslogmessage_debug(@message);
  unilogmessage_debug(@message);
  logmessage_debug(@message);

=head1 DESCRIPTION

  B<syslogmessage> writes messages to syslog, B<unilogmessage> 
  writes messages to a simple file. B<logmessage> does both. There
  are variables to change the default behaviour.
  The *_debug only writes messages if $debug is set to a true value.


=head2 Variables

=over

=item $debug (default = 0)

  Enable/disable debugging functions. B<unilogmessage_debug> writes
  to $unilogfile as usual. B<syslogmessage_debug> writes to syslog 
  with priority LOG_DEBUG, which is on most systems not seen by default.
  Probably there must be added a line like this be added to 
  /etc/syslog.conf: 

             user.=debug   /var/log/debug.log

  Unlike B<logmessage> B<logmessage_debug> writes only to stderr.


=item $useunilog (default = 1)

  Enable/disable syslog logging. If disabled make B<syslogmessage> 
  a dummy function. 

=item $useunilog (default = 1)

  Enable/disable file logging. If disabled make B<unilogmessage> 
  a dummy function. 

=item $unilogfile (default = '/var/log/unidump.log')

  Specify the file where unilog messages go.

=item $sysloglevel (default = LOG_INFO)

  Priority which is used for syslog messages.

=item $syslogfacility (default = LOG_USER)

  Facility which is used for syslog messages, should not be changed.

=item $sysloglabel (default = 'UNIDUMP')

  Label which is used for syslog messages.


=back


  
