# 	$Id: GtarDumper.pm,v 1.2 2003/09/08 07:14:37 thorsten Exp $	
package Unidump::GtarDumper;
use base qw(Unidump::GenericDumper);
use strict;
use POSIX;
use IO::File;
use Unidump::Logger qw(logmessage logmessage_debug);
use Unidump::History qw(:all);
use Unidump::Units qw(convert);
use vars qw($VERSION);
$VERSION = do{my @r = split(" ",qq$Revision: 1.2 $ );$r[1];};


sub check {
  logmessage_debug("GtarDumper::check: @_");
  my $self = shift;
  my ($rc, $out);
  ($rc, $out) = $self->checkcmd($self->gtar);
  die "command not found: " . $self->gtar if $rc;
  $self->SUPER::check;
}

sub snapshotfile {
  logmessage_debug("GtarDumper::snapshotfile: @_");
  my $self = shift;
  my $did  = shift;
  $did = $self->dumpid unless $did;
  my $dir = $self->tocfiledir;
  unless(-d $dir) {
    mkdir $dir, 0777 or die "cannot create dir $dir: $!";
  }
  return "$dir/$did.inc";
}

sub dumpcmdline {
  logmessage_debug("GtarDumper::dumpcmdline: @_");
  my $self = shift;
  my $cmdline;
  my $snapshotfile = $self->snapshotfile;
  my $parent = hist_get_parent($self->directory, $self->dumplevel, $self->starttime);
  if($parent) {
    my $parent_snapshotfile = $self->snapshotfile($parent);
    $cmdline = "cp $parent_snapshotfile $snapshotfile;"; 
  }
  my $logfile = $self->dumplogfile;
  my $directory = $self->directory;
  my $dump = $self->diskmode ? $self->dumpfile : $self->ntapedevice;
  $cmdline .= $self->gtar;
  $cmdline .= " --create --one-file-system --sparse --totals";
  $cmdline .= " " . $self->writeflags if defined $self->writeflags;
  $cmdline .= " --blocking-factor=" . convert($self->blocksize)/512 
    if $self->blocksize;
  $cmdline .= " --gzip" if $self->softcompression;
  $cmdline .= " --label=" . $self->dumpid;
  $cmdline .= " --listed-incremental=$snapshotfile";
  foreach my $i ($self->exclude_list) {
    $cmdline .= " --exclude=$i";
  }
  $cmdline .= " --file=$dump --directory=$directory . > $logfile 2>&1";
  return $cmdline;
}

sub sizecmdline {
  logmessage_debug("GtarDumper::sizecmdline: @_");
  my $self = shift;
  my $dumpid = $self->dumpid;
  my $cmdline;
  my $snapshotfile = "/tmp/$dumpid.inc";
  my $parent = hist_get_parent($self->directory, $self->dumplevel, $self->starttime);
  if($parent) {
    my $parent_snapshotfile = $self->snapshotfile($parent);
    $cmdline = "cp $parent_snapshotfile $snapshotfile;"; 
  }
  my $directory = $self->directory;
  $cmdline .= $self->gtar;
  $cmdline .= " --create --one-file-system --sparse";
  $cmdline .= " " . $self->writeflags if defined $self->writeflags;
  $cmdline .= " --blocking-factor=" . convert($self->blocksize)/512 if $self->blocksize;
  $cmdline .= " --listed-incremental=$snapshotfile";
  foreach my $i ($self->exclude_list) {
    $cmdline .= " --exclude=$i";
  }
  $cmdline .= " --file=- --directory=$directory . | wc -c";
  return $cmdline;
}

sub comparecmdline {
  logmessage_debug("GtarDumper::comparecmdline: @_");
  my $self = shift;
  my $dump = $self->diskmode ? $self->dumpfile : $self->ntapedevice;
  my $snapshotfile = $self->snapshotfile;
  my $cmdline = $self->gtar;
  $cmdline .= " --compare";
  $cmdline .= " " . $self->readflags if defined $self->readflags;
  $cmdline .= " --blocking-factor=" . convert($self->blocksize)/512 if $self->blocksize;
  $cmdline .= " --gzip" if $self->softcompression;
  $cmdline .= " --listed-incremental=$snapshotfile";
  foreach my $i ($self->exclude_list) {
    $cmdline .= " --exclude=$i";
  }
  $cmdline .= " --file=$dump";
  return $cmdline;
}

sub listcmdline {
  logmessage_debug("GtarDumper::listcmdline: @_");
  my $self = shift;
  my $dump = $self->diskmode ? $self->dumpfile : $self->ntapedevice;
  my $cmdline = $self->gtar;
  $cmdline .= " --list";
  $cmdline .= " " . $self->readflags if defined $self->readflags;
  $cmdline .= " --blocking-factor=" . convert($self->blocksize)/512 if $self->blocksize;
  $cmdline .= " --gzip" if $self->softcompression;
  $cmdline .= " --file=$dump";
  $cmdline .= q( | perl -e '<>; while(<>) { s@(.*)/$@d $1@ || s/^/- /; print; }');
  return $cmdline;
}

sub restorecmdline {
  logmessage_debug("GtarDumper::restorecmdline: @_");
  my $self = shift;
  my @restorelist = @_;
  my $dump = $self->diskmode ? $self->dumpfile : $self->ntapedevice;
  my $snapshotfile = $self->snapshotfile;
  my $cmdline = $self->gtar;
  $cmdline .= " --extract --preserve";
  $cmdline .= " " . $self->readflags if defined $self->readflags;
  $cmdline .= " --blocking-factor=" . convert($self->blocksize)/512 
    if $self->blocksize;
  $cmdline .= " --listed-incremental=$snapshotfile" if (-f $snapshotfile);
  $cmdline .= " --gzip" if $self->softcompression;
  $cmdline .= " --file=$dump";
  foreach (@restorelist) {
    $cmdline .= " '$_'";
  }
  return $cmdline;
}

sub dumpstatus {
  logmessage_debug("GtarDumper::dumpstatus: @_");
  my $self = shift;
  my ($rc, $logfile) = @_;
  my $mesg = ($rc == 0) ? "OK" : "ERROR: see $logfile for details";
  my $fh = IO::File->new($logfile) or
    return wantarray ? (-2, "cannot open logfile") : -2;
  wantarray ? ($rc, $mesg) : $rc;
}

sub histoptions {
  logmessage_debug("Ext2Dumper::histoptions: @_");
  my $self = shift;
  my $opt = "gtar";
  $opt .= "," . $self->blocksize if $self->blocksize;
  unless($self->diskmode) {
    $opt .= ",hw" if $self->tape->hwcompression;
  }
  $opt .= ",z" if $self->softcompression;
  return $opt;
}



1;
__END__
