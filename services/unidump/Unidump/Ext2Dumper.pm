# 	$Id: Ext2Dumper.pm,v 1.2.10.1 2004/07/01 13:21:46 thomas Exp $	
package Unidump::Ext2Dumper;
use base qw(Unidump::GenericDumper);
use strict;
use POSIX;
use IO::File;
use Cwd;
use Unidump::Logger qw(logmessage logmessage_debug);
use Unidump::Units qw(convert);
use vars qw($VERSION);
$VERSION = do{my @r = split(" ",qq$Revision: 1.2.10.1 $ );$r[1];};


sub check {
  logmessage_debug("Ext2Dumper::check: @_");
  my $self = shift;
  my ($rc, $out);
  ($rc, $out) = $self->checkcmd($self->ext2dump);
  die "command not found: " . $self->ext2dump if $rc;
  ($rc, $out) = $self->checkcmd($self->ext2restore);
  die "command not found: " . $self->ext2restore if $rc;
  $self->SUPER::check;
}

sub useqfa {
  logmessage_debug("Ext2Dumper::useqfa: @_");
  my $self = shift;
  my $qfa;
  if(@_) {
    $qfa = $self->set('useqfa', @_);
  } else {
    $qfa = ($self->get('useqfa') && $self->support_qfa());
  }
  return $qfa;
}

sub support_qfa {
  logmessage_debug("Ext2Dumper::support_qfa: @_");
  my $self = shift;
  return 1;			# modern dump can QFA
#    my $cmdline = $self->ext2dump;
#    unless(qx($cmdline -Q 2>&1) =~ /invalid option/i) {
#      return 1;
#    }
#    return 0;
}

sub eotcommand {
  logmessage_debug("Ext2Dumper::eotcommand: @_");
  my $self = shift;
  my $cmd;
  if(@_) {
    $cmd = $self->set('eotcommand', @_);
  } else {
    $cmd = $self->get('eotcommand');
    unless(defined $cmd) {
      $cmd = "sh -c 'exit 2'";
      $self->set('eotcommand', $cmd);
    }
  }
  return $cmd;
}

sub dumpid {
  logmessage_debug("Ext2Dumper::dumpid: @_");
# we cannot use the common uuid-labels here because
#  dump limits the length of the label to 15 chars
  my $self = shift;
  my $id;
  if(@_) {
    $id = $self->set('dumpid', @_);
  } else {
    $id = $self->get('dumpid');
    unless($id) {
      sleep(1);
      $id = sprintf("%08x-%04x",time(),$$); 
      $self->set('dumpid', $id);
    }
  }
  return $id;
}

sub excludeinodes {
  logmessage_debug("Ext2Dumper::excludeinodes: @_");
  my $self = shift;
  my @list = ();
  my $cwd = cwd();
  # Changed 1.07.2004 Thomas
  # lstat [0]=device [1]=inode
  #my $dev = (lstat($self->directory))[1];
  my $dev = (lstat($self->directory))[0];
  chdir $self->directory;
  foreach my $i ($self->exclude_list) {
    my @stat = lstat($i);
    next unless @stat;
    push(@list, $stat[1]) if $stat[0] == $dev;
  }
  chdir $cwd;
  return @list;
}

sub dumpcmdline {
  logmessage_debug("Ext2Dumper::dumpcmdline: @_");
  my $self = shift;
  my $cmdline = $self->ext2dump;
  my $logfile = $self->dumplogfile;
  my $directory = $self->directory;
  my $dump = $self->diskmode ? $self->dumpfile : $self->ntapedevice;
  $cmdline .= " -h 0 -a ";
  $cmdline .= " " . $self->writeflags if defined $self->writeflags;
  $cmdline .= " -" . $self->dumplevel;
  $cmdline .= " -b " . convert($self->blocksize)/1024 if $self->blocksize;
  $cmdline .= " -L " . $self->dumpid;
  $cmdline .= " -u" if $self->regulardump;
  $cmdline .= " -z" if $self->softcompression;

  # Changed 1.07.2004 Thomas
  # Inodes als kommaseparierte Liste angeben
  my $excludeinodeslist = "";
  foreach my $i ($self->excludeinodes) {
    if( length($excludeinodeslist) > 0 ) {
      $excludeinodeslist .= ",$i";
    }else{
      $excludeinodeslist = " -e $i";
    }
  }
  $cmdline .= $excludeinodeslist;

  unless($self->diskmode) {
    $cmdline .= " -F \"" . $self->eotcommand . "\"";
    $cmdline .= " -Q " . $self->dumpqfafile if $self->useqfa;
  } else {
    system("touch $dump");
  }
  $cmdline .= "  -f $dump $directory > $logfile 2>&1";
  return $cmdline;
}

sub sizecmdline {
  logmessage_debug("Ext2Dumper::sizecmdline: @_");
  my $self = shift;
  my $cmdline = $self->ext2dump;
  $cmdline .= " -S";
  $cmdline .= " " . $self->writeflags if defined $self->writeflags;
  $cmdline .= " -" . $self->dumplevel;
  $cmdline .= " -b " . convert($self->blocksize)/1024 if $self->blocksize;

  # Changed 1.07.2004 Thomas
  # Inodes als kommaseparierte Liste angeben
  my $excludeinodeslist = "";
  foreach my $i ($self->excludeinodes) {
    if( length($excludeinodeslist) > 0 ) {
      $excludeinodeslist .= ",$i";
    }else{
      $excludeinodeslist = " -e $i";
    }
  }
  $cmdline .= $excludeinodeslist;

  $cmdline .= " " . $self->directory;
  $cmdline .= q( | perl -ne '/^\s*\d+\s*$/ && print');
  return $cmdline;
}

sub comparecmdline {
  logmessage_debug("Ext2Dumper::comparecmdline: @_");
  my $self = shift;
  my $dump = $self->diskmode ? $self->dumpfile : $self->ntapedevice;
  my $cmdline = $self->ext2restore;
  $cmdline .= " -C";
  $cmdline .= " " . $self->readflags if defined $self->readflags;
  $cmdline .= " -b " . convert($self->blocksize)/1024 if $self->blocksize;
  $cmdline .= " -f $dump";

  return $cmdline;
}

  
sub support_compression {
  logmessage_debug("Ext2Dumper::support_compression: @_");
  my $self = shift;
  return 1;			# modern dump support this
#    my $cmdline = $self->ext2dump;
#    unless(qx($cmdline -z 2>&1) =~ /invalid option/i) {
#      return 1;
#    }
#    return 0;
}
  
#  sub internalcompression {
#    logmessage_debug("Ext2Dumper::internalcompression: @_");
#    my $self = shift;
#    my $z;
#    if(@_) {
#      $z = $self->set('internalcompression', @_);
#    } else {
#      $z = $self->get('internalcompression');
#      unless(defined $z) {
#        $z = $self->support_compression;
#        $self->set('internalcompression', $z);
#      }
#    }
#    return $z;
#  }

sub listcmdline {
  logmessage_debug("Ext2Dumper::listcmdline: @_");
  my $self = shift;
  my $dump = $self->diskmode ? $self->dumpfile : $self->ntapedevice;
  my $cmdline = $self->ext2restore;
  $cmdline .= " -t -v";
  $cmdline .= " " . $self->readflags if defined $self->readflags;
  $cmdline .= " -b " . convert($self->blocksize)/1024 if $self->blocksize;
  $cmdline .= " -f $dump";
  $cmdline .= " 2> /dev/null";
  $cmdline .= q( | perl -ne 's/^dir\s+\d+\s+/d / || s/^leaf\s+\d+\s+/- / and print;');
  return $cmdline;
}

sub restorecmdline {
  logmessage_debug("Ext2Dumper::restorecmdline: @_");
  my $self = shift;
  my @restorelist = @_;
  my $dump = $self->diskmode ? $self->dumpfile : $self->ntapedevice;
  my $cmdline = $self->ext2restore;
#  $cmdline .= " -y";
  $cmdline .= @restorelist ? " -x" : " -r";
  $cmdline .= " " . $self->readflags if defined $self->readflags;
  $cmdline .= " -b " . convert($self->blocksize)/1024 if $self->blocksize;
  $cmdline .= " -Q " . $self->dumpqfafile 
    if ($self->useqfa && -f $self->dumpqfafile);
  $cmdline .= " -f $dump";
  foreach (@restorelist) {
    $cmdline .= " '$_'";
  }
#  $cmdline .= " 2> /dev/null";
#  $cmdline = "cd " . $self->restoredir . " && $cmdline";
  return $cmdline;
}

sub dumpstatus {
  logmessage_debug("Ext2Dumper::dumpstatus: @_");
  my $self = shift;
  my ($rc, $logfile) = @_;
  my $mesg = "ERROR: see $logfile for details";
  my $id = $self->dumpid;
  my $fh = IO::File->new($logfile) or
    return wantarray ? (-2, "cannot open logfile") : -2;
  $rc = -1;
  while(<$fh>) {
    chomp;
    s/^\s+//; s/\s+$//;
    /DUMP\s+IS\s+DONE/i and $rc=0,$mesg="OK", last;
  }
  undef($fh);
  return wantarray ? ($rc, $mesg) : $rc;
}

sub histoptions {
  logmessage_debug("Ext2Dumper::histoptions: @_");
  my $self = shift;
  my $opt = "ext2dump";
  $opt .= "," . $self->blocksize if $self->blocksize;
  unless($self->diskmode) {
    $opt .= ",qfa" if $self->useqfa;
    $opt .= ",hw" if $self->tape->hwcompression;
  }
  $opt .= ",z" if $self->softcompression;
  return $opt;
}

sub parenttime {
  logmessage_debug("Ext2Dumper::parenttime: @_");
  my $self = shift;
  my $fh = IO::File->new($self->dumplogfile, 'r') or  return -2;
  my $date = -1;
  while(<>) {
    /\s*DUMP:\s+Date\s+of\s+last\s+level\s+\d\s+dump:\s*/ 
      and $date = str2time($'), last;
  }
  return $date;
}

1;
__END__
