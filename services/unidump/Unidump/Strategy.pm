# 	$Id: Strategy.pm,v 1.2 2003/09/08 07:14:37 thorsten Exp $
package Unidump::Strategy;
use strict;
use POSIX qw(strftime setlocale LC_ALL LC_CTYPE);
use Unidump::Logger qw(logmessage logmessage_debug);
use vars qw(@ISA @EXPORT @EXPORT_OK %EXPORT_TAGS $VERSION);
use Exporter;
$VERSION = do{my @r = split(" ",qq$Revision: 1.2 $);$r[1];};
@ISA = qw(Exporter);

@EXPORT = qw();
@EXPORT_OK = qw(nextdump);
%EXPORT_TAGS = (all => [@EXPORT_OK]);

sub nextdump {
  logmessage_debug("Strategy::nextdump: @_");
  my($strategy, $group, $time) = @_;
  $strategy = "" unless defined $strategy;
  $time = time() unless $time;
  my ($fulldumpday, $fulldumpweek, $dumpinc);
  if($group) {
    $dumpinc = do { $group =~ s/_?\+([0-8]+)//; $1; };
    $fulldumpweek = do { $group =~ s/_?([1-5]+)//; $1; };
  }
  if($strategy =~ /^simple/) {
    $fulldumpday = do { $strategy =~ /^simple_?/; $'; };
    return nextdump_simple($fulldumpday, $fulldumpweek, $dumpinc, $time);
  }
  if($strategy =~ /^gfs/) {
    $fulldumpday = do { $strategy =~ /^gfs_?/; $'; };
    return nextdump_simple($fulldumpday, $fulldumpweek, $dumpinc, $time);
  }
  if($strategy =~ /^distrib/) {
    $fulldumpday = do { $group =~ /_?(mo|tu|we|th|fr|sa|su)/i; $1; };
    return nextdump_distrib($fulldumpday, $fulldumpweek, $dumpinc, $time);
  }

  $dumpinc = 0;
#  $dumpinc = 0 unless $dumpinc;
  return wantarray ? ($dumpinc, $strategy) : $dumpinc;
}

sub nextdump_simple($$$$) {
  logmessage_debug("Strategy::nextdump_simple: ", grep {$_ ? $_ : ''} @_);
  my($fulldumpday, $fulldumpweek, $dumpinc, $time) = @_;
  $fulldumpday = "fr" unless $fulldumpday;
  $fulldumpweek = "12345" unless $fulldumpweek;
  $dumpinc = 0 unless defined $dumpinc;
  my @ltime = localtime($time);
  my $week =  POSIX::floor(($ltime[3]-1)/7)+1;
  my $mon  = $ltime[4];
  setlocale( LC_ALL, "C" );
  my $wday = POSIX::strftime("%A", @ltime);
  my $tapelabel = $wday;
  if($wday =~ /^$fulldumpday/i) {
    $tapelabel .= "_week$week";
    if(scalar grep {/$week/} split('', $fulldumpweek)) {
      return wantarray ? ($dumpinc, $tapelabel) : $dumpinc;
    }
  }
  if($wday =~ /^(sat|sun)/i) {
    return wantarray ? ($dumpinc, "<none>") : $dumpinc;
  }
  return wantarray ? ($dumpinc+1, $tapelabel) : $dumpinc+1;
}

sub nextdump_distrib($$$$) {
  logmessage_debug("Strategy::nextdump_distrib: ", grep {$_ ? $_ : ''} @_);
  my($fulldumpday, $fulldumpweek, $dumpinc, $time) = @_;
  $fulldumpday = "fr" unless $fulldumpday;
  $fulldumpweek = "12345" unless $fulldumpweek;
  $dumpinc = 0 unless defined $dumpinc;
  my @ltime = localtime($time);
  my $week =  POSIX::floor(($ltime[3]-1)/7)+1;
  my $mon  = $ltime[4];
  setlocale( LC_ALL, "C" );
  my $wday = POSIX::strftime("%A", @ltime);
  if($wday =~ /^(sat|sun)/i) {
    return wantarray ? ($dumpinc, "<none>") : $dumpinc;
  }
  my $tapelabel = $wday;
  $tapelabel .= "_week$week";
  if($wday =~ /^$fulldumpday/i) {
    if(scalar grep {/$week/} split('', $fulldumpweek)) {
      return wantarray ? ($dumpinc, $tapelabel) : $dumpinc;
    }
  }
  return wantarray ? ($dumpinc+1, $tapelabel) : $dumpinc+1;
}

1;

__END__

=head1 NAME

  Unidump::Strategy - Backup-Strategy

=head1 SYNOPSIS

  use Unidump::Strategy qw(nextdump);
  ($dumplevel, $tapelabel) = nextdump($strategy, $group, $time);

=head1 DESCRIPTION

This module implements the dump strategy. It exports a single
function B<nextdump>. The function returns the dumplevel and
the expected tapelabel of the next dump.

=over

=item gfs (simple)

This is the simplest strategy, that is implemented yet. The simplest
form of this strategy does a level 1 dump daily from monday to
thursday and a level 0 dump on friday. The level 1 tapes are
weekly overwritten, the level 0 tapes are monthly overwritten.
This leads to daily backups for the last week and weekly backups
for the last month. There are 9 tapes needed in this strategy. As
there are two 5th fridays a year you might save these tapes
forever. The table shows, which tapes are written during the
backup-cycle (1 month):

        | Monday | Tuesday | Wednesday | Thursday | Friday
  level | level 1| level 1 | level 1   | level 1  | level 0
  ------+--------+---------+-----------+----------+-------------
  week1 | Monday | Tuesday | Wednesday | Thursday | Friday_week1
  week2 | Monday | Tuesday | Wednesday | Thursday | Friday_week2
  week3 | Monday | Tuesday | Wednesday | Thursday | Friday_week3
  week4 | Monday | Tuesday | Wednesday | Thursday | Friday_week4
  week5 | Monday | Tuesday | Wednesday | Thursday | Friday_week5

If you prefer to do your fulldumps at a different weekday, you might
use strategy "gfs_mo", "gfs_tu", .. for fulldumps on
monday, tuesday, ... Note, that you cannot specify different
weekdays for your disks (but see also the  B<distrib> strategy below).

As the strategy is a global configuration you might fine-tune your
dumps by setting a "group". The group is a disk-specific
configuration. By setting group to "+<n>" the integer value n is
added to the normaly choosen dumplevel. E.g. group="+3" leads to
dumps level 4 on monday to thursday and level 3 on friday. Of course
there must be at least one level 0 dump. This can be done using an
"archiv*" strategy (see below).


=item distrib

In case you have to backup several disks, the full dumps may be
too big to fit on a single tape in parallel. This strategy
performs fulldumps on different weekdays for each disk.
Use group B<mo> for mondays fulldumps, group B<tu> for
tuesdays fulldumps etc. Choose different days for your disks. The
table shows the dumplevel for each day and group. 

   group | Monday | Tuesday | Wednesday | Thursday | Friday
   ------+--------+---------+-----------+----------+-------
     mo  |   0    |    1    |     1     |     1    |   1
     tu  |   1    |    0    |     1     |     1    |   1
     we  |   1    |    1    |     0     |     1    |   1
     th  |   1    |    1    |     1     |     0    |   1
     fr  |   1    |    1    |     1     |     1    |   0

The dumplevel can be increased by a constant value by setting the
group to "<day>+<n>", eg. "mo+2" for level 2 dumps on monday and
level 3 dumps otherwise. 

Note, that you cannot overwrite your daily tapes on a weekly base!
Instead you must use uniq tapes for every week. You should overwrite
your tapes monthly. This leads to daily backups for the last 4
weeks. Note, that it does not make sense to archiv any tapes from
this strategy (as the tapes of the 5th week might contain only level
1 dumps that will become useless in the next month). The table shows
the expected tapes for one month: 

    Monday    |   Tuesday   |   Wednesday   |   Thursday   |   Friday
  ------------+-------------+---------------+--------------+------------
  Monday_week1|Tuesday_week1|Wednesday_week1|Thursday_week1|Friday_week1
  Monday_week2|Tuesday_week2|Wednesday_week2|Thursday_week2|Friday_week2
  Monday_week3|Tuesday_week3|Wednesday_week3|Thursday_week3|Friday_week3
  Monday_week4|Tuesday_week4|Wednesday_week4|Thursday_week4|Friday_week4
  Monday_week5|Tuesday_week5|Wednesday_week5|Thursday_week5|Friday_week5


=item archiv*

It is possible to perform on-demand backups. This is done by choosing
an "archiv" strategy. Use any string not  matching /^gfs/ or /^simple/ or
/^distrib/) as strategy. The dumplevel will be 0 unless a group like
"+<n>" is specified. The tapelabel must match the string used for
strategy.

E.g. to perform a fulldump of disk "home", label a tape as
"archiv_home" and use strategy "archiv_home". 

=back
