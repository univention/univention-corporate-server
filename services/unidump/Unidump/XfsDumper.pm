# 	$Id: XfsDumper.pm,v 1.2 2003/09/08 07:14:37 thorsten Exp $	
package Unidump::XfsDumper;
use base qw(Unidump::GenericDumper);
use strict;
use POSIX;
use Fcntl;
use IO::File;
use Cwd;
use File::Find qw(find finddepth);
use File::Remove ();
use File::Compare ();
use Unidump::Units qw(convert);
use Unidump::Logger qw(logmessage logmessage_debug);
use Unidump::History qw(hist_get_starttime hist_get_parent);
use vars qw($VERSION);
$VERSION = do{my @r = split(" ",qq$Revision: 1.2 $ );$r[1];};


sub check {
  logmessage_debug("XfsDumper::check: @_");
  my $self = shift;
  my ($rc, $out);
  ($rc, $out) = $self->checkcmd($self->xfsdump);
  die "command not found: " . $self->xfsdump if $rc;
  ($rc, $out) = $self->checkcmd($self->xfsrestore);
  die "command not found: " . $self->xfsrestore if $rc;
  $self->SUPER::check;
}
	
sub dumpcmdline {
  logmessage_debug("XfsDumper::dumpcmdline: @_");
  my $self = shift;
  my $cmdline = $self->xfsdump;
  my $logfile = $self->dumplogfile;
  my $directory = $self->directory;
  my $dump = $self->diskmode ? $self->dumpfile : $self->ntapedevice;
  if($self->exclude) {
    logmessage("WARNING: xfsdump does not support exclude lists!\n" .
	       "please use the attribute \"SGI_XFSDUMP_SKIP_FILE\" instead:\n" .
	       " attr -s SGI_XFSDUMP_SKIP_FILE -V 1 <path>\n");
  }
  $cmdline .= " -F -e -o";
  $cmdline .= " " . $self->writeflags if defined $self->writeflags;
  $cmdline .= " -l " . $self->dumplevel;
  $cmdline .= " -L " . $self->dumpid;
  $cmdline .= " -J " unless $self->regulardump;
  $cmdline .= " -c \"" . $self->eotcommand . "\"";
  if($self->softcompression) {
    my $bs = $self->blocksize ? "bs=" . $self->blocksize : "";
    $cmdline .= " - $directory 2> $logfile";
    $cmdline .= " | gzip -2 -c | dd $bs of=$dump 2> /dev/null";
  } else {
    $cmdline .= " -m -b " . convert($self->blocksize) if $self->blocksize;
    $cmdline .= " -f $dump";
    $cmdline .= " $directory > $logfile";
  }
  return $cmdline;
}

sub sizecmdline {
  logmessage_debug("XfsDumper::sizecmdline: @_");
  my $self = shift;
  my $cmdline = $self->xfsdump;
  $cmdline .= " -F -e -o -J";
  $cmdline .= " " . $self->writeflags if defined $self->writeflags;
  $cmdline .= " -l " . $self->dumplevel;
  $cmdline .= " -f /dev/null " . $self->directory;
  $cmdline .= q( | perl -l012 -ne '/dump.size[:\s=]+(\d+)/ && print $1');
  return $cmdline;
}

sub listcmdline {
  logmessage_debug("XfsDumper::listcmdline: @_");
  my $self = shift;
  my $dump = $self->diskmode ? $self->dumpfile : $self->ntapedevice;
  my $cmdline = $self->xfsrestore;
  $cmdline .= " -F -t";
  $cmdline .= " " . $self->readflags if defined $self->readflags;
  $cmdline .= " -m -b " . convert($self->blocksize) if $self->blocksize;

  if($self->softcompression) {
    my $bs = $self->blocksize ? "bs=" . $self->blocksize : "";
    $cmdline = "dd $bs if=$dump 2> /dev/null | gzip -dc | $cmdline -";
  } else {
    $cmdline .= " -f $dump";
  }

  $cmdline .= q( | perl -e '%d=(); $d{"d ."}++; while(<>){chomp; m@^xfsrestore:@ && next; print "- ./$_\n"; s@/[^/]*$@@; $d{"d ./$_"}++;} print join("\n", keys %d, "");');
  return "cd " . $self->restoredir  . " && $cmdline";
}

sub restorecmdline {
  logmessage_debug("XfsDumper::restorecmdline: @_");
  my $self = shift;
  my @restorelist = @_;
  my $dump = $self->diskmode ? $self->dumpfile : $self->ntapedevice;
  my $cmdline = $self->xfsrestore;
  $cmdline .= " -F";
  $cmdline .= " -r"  unless @restorelist;
  $cmdline .= " " . $self->readflags if defined $self->readflags;
  $cmdline .= " -m -b " . convert($self->blocksize) if $self->blocksize;
  if($self->softcompression) {
    my $bs = $self->blocksize ? "bs=" . $self->blocksize : "";
    $cmdline = "dd $bs if=$dump 2> /dev/null | gzip -dc | $cmdline -";
  } else {
    $cmdline .= " -f $dump";
  }
  foreach (@restorelist) {
    $cmdline .=  " -s '$_'";
  }
  $cmdline .=  " " . $self->restoredir;
  return $cmdline;
}

sub dumpstatus {
  logmessage_debug("XfsDumper::dumpstatus: @_");
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
    /Dump\s+Status:\s+SUCCESS/i and $rc=0, $mesg="OK", last;
  }
  undef($fh);
  return wantarray ? ($rc, $mesg) : $rc;
}


my $cmp_out;			# we need this for communication
sub compare {
  logmessage_debug("XfsDumper::compare: @_");
  my $self = shift;
  my $odir = $self->directory;
  my $rdir = $self->restoredir;
  my $pdump= hist_get_parent
    ($self->directory, $self->dumplevel, $self->starttime);
  my $ptime = $pdump ? hist_get_starttime($pdump) : 0;
  my ($rc, $mesg, $path);
  my $cwd = getcwd();
  $cmp_out = "";
  my @list = grep { s@^d\s*\./@./@ } $self->list;
  foreach $path (uniq(sort grep {s@\./@@; s@/.*$@@} @list)) {
    ($rc, $mesg) = $self->restore($path);
    if($rc) {
      $cmp_out .= "$path: cannot compare because restore failed: $mesg\n";
      next;
    }
    logmessage_debug("XfsDumper::compare: compare $odir/$path $rdir/$path");
    unless(chdir $odir) { 
      $cmp_out .= 
	"$path: cannot compare because chdir to $path failed: $!";
      next;
    }
    my $wanted = mk_wanted($rdir, $ptime);
    finddepth($wanted, "$path");
  }
  chdir $cwd;  
  logmessage_debug("XfsDumper::compare: output: $cmp_out");
  wantarray ? ($rc, $cmp_out) : $rc;
}

sub uniq {
  my ($x, $x_last, @out);
  $x_last = !$_[0];
  while($x = pop(@_)) {
    next if $x eq $x_last;
    push(@out, $x);
    $x_last = $x;
  }
  return @out;
}

sub mk_wanted {
  my($rbasedir, $ptime) = @_;
  return sub {
   
    local($^W);
    $^W = 0;
    my $odir  = $File::Find::dir;
    my $opath = $_;
    my $rdir  = "$rbasedir/$File::Find::dir";
    my $rpath = "$rbasedir/$File::Find::name";
    my @ostat = lstat($opath) or $cmp_out .= "cannot stat $opath: $!\n";

    unless(@ostat) {
      $cmp_out .= "$File::Find::name unknown (maybe removed since dump?)\n";
    } else {			
      # if this is a incremental dump, the file won't be there
      # if it wasn't modified since our parent dump
      # this does not work for directories, so we skip all directories
      # that do not exist in dump
      if(-d and ! -l) {
	return unless(-e $rpath);
      } else {
	return if (($ostat[9] < $ptime) && ($ostat[10] < $ptime));
      }
    }

    my @rstat = lstat($rpath) or $cmp_out .= "cannot stat $rpath: $!\n";

    unless(@rstat) {
      $cmp_out .= 
	" $File::Find::name missing (maybe created since dump?)\n";
      return;
    }

    if(-l) {
      unlink($rpath) or
	$cmp_out .= "cannot remove temporary file $rpath: $!\n"
	  . "  this is probably harmless, please remove $rbasedir\n";
      return;
    }

    if(-d) {
      unless(rmdir $rpath) {
	local(*D);
	opendir(D, $rpath);
	my @d = grep {!/^\.\.?$/} readdir(D);
	closedir(D);
	if(@d) {
	  $cmp_out .= 
	    " $File::Find::name unknown content (maybe removed since dump?): @d\n";
#	File::Remove::remove \1, $rpath;
	} else {
	  $cmp_out .= "unexpected error: cannot remove $rpath: $!\n"
	    . "  this is probably harmless, please remove $rbasedir\n";
	}
      }
      return;
    }

    if(-f) {
      unless ("@rstat[2,4,5]" eq "@ostat[2,4,5]") {
	$cmp_out .= " $File::Find::name status has changed (dump/disk): ";
	$cmp_out .= "mode: $rstat[2]/$ostat[2] ";
	$cmp_out .= "uid: $rstat[4]/$ostat[4] ";
	$cmp_out .= "gid: $rstat[5]/$ostat[5]\n";
      }
      unless(File::Compare::compare($rpath, $_) == 0) {
	$cmp_out .= " $File::Find::name has changed\n";
      }
    } else {
      unless ("@rstat[2,4..6]" eq "@ostat[2,4..6]") {
	$cmp_out .= " $File::Find::name status has changed (dump/disk): ";
	$cmp_out .= "mode: $rstat[2]/$ostat[2] ";
	$cmp_out .= "uid: $rstat[4]/$ostat[4] ";
	$cmp_out .= "gid: $rstat[5]/$ostat[5] ";
	$cmp_out .= "rdev: $rstat[6]/$ostat[6]\n";
      }
    }

    unlink($rpath) or
      $cmp_out .= "cannot remove file $rpath: $!\n"
	. "  this is probably harmless, please remove $rbasedir\n";
  }
}

sub histoptions {
  logmessage_debug("XfsDumper::histoptions: @_");
  my $self = shift;
  my $opt = "xfsdump";
  $opt .= "," . $self->blocksize if $self->blocksize;
  unless($self->diskmode) {
    $opt .= ",hw" if $self->tape->hwcompression;
  }
  $opt .= ",gzip" if $self->softcompression;
  return $opt;
}


1;
__END__

