# 	$Id: GenericDumper.pm,v 1.2 2003/09/08 07:14:37 thorsten Exp $	
package Unidump::GenericDumper;
use base qw(Class::Accessor);
use strict;
use POSIX;
use IO::File;
use Fcntl;
#use UUID;
use Unidump::Logger qw(logmessage logmessage_debug);
use Unidump::Strategy;
use Unidump::History qw(hist_insert);
use Unidump::Units qw(convert);
use vars qw($VERSION);
$VERSION = do{my @r = split(" ",qq$Revision: 1.2 $ );$r[1];};


Unidump::GenericDumper->mk_accessors
  (qw(blocksize debug directory diskmode dumpid dumpfile dumplevel 
      exclude ext2dump ext2restore group
      gtar historyfile holdingdisk holdingdisksize internalcompression
      logfile logfiledir ntapedevice 
      postcommand precommand  eotcommand readflags regulardump 
      restorelist softcompression star starttime strategy 
      support_compression tape tapeid tapeidx tapelabel tapelibfile 
      tocfiledir unidir useqfa usesyslog
      useunilog verify writeflags xfsdump xfsrestore));

sub init {
  logmessage_debug("GenericDumper::init: @_");
  my $self = shift;
  my ($pattern, $cmd, $out, $rc);
  $self->check;
  $cmd = $self->precommand;
 logmessage_debug("executing precmd: $cmd") if $cmd;
  $out = qx($cmd) if $cmd;
  $rc = $?/256;
 logmessage_debug("ERROR: retcode: $?, out: $out") 
   if $cmd;
 logmessage("ERROR($rc): $cmd: $!") if $rc;
  return wantarray ? ($rc, $out) : $rc;
}

sub check {
  logmessage_debug("GenericDumper::check: @_");
  my $self = shift;
  die "no such directory: " . $self->directory unless(-d $self->directory);
  die "no such directory: " . $self->unidir unless(-d $self->unidir);
}
	
sub finalize {
  logmessage_debug("GenericDumper::finalize: @_");
  my $self = shift;
  my ($cmd, $out, $rc);
  $cmd = $self->postcommand;
  if($cmd) {
  logmessage_debug("executing postcmd: $cmd");
    $out = qx($cmd) if $cmd;
    $rc = $?/256;
  logmessage_debug("cmd retcode: $?, out: $out");
  logmessage("ERROR($rc): $cmd: $!") if $rc;
  }
  return wantarray ? ($rc, $out) : $rc;
}

#  sub dumpid {
#    logmessage_debug("GenericDumper::dumpid: @_");
#    my $self = shift;
#    my $id;
#    if(@_) {
#      $id = $self->set('dumpid', @_);
#    } else {
#      $id = $self->get('dumpid');
#      unless($id) {
#        my($uuid);
#      UUID::generate($uuid); UUID::unparse($uuid, $id);
#        $self->set('dumpid', $id);
#      }
#    }
#    return $id;
#  }


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


sub dumpfile {
  logmessage_debug("GenericDumper::dumpfile: @_");
  my $self = shift;
  my $file;
  if(@_) {			# set the dumpfile
    $file = $self->set('dumpfile', @_);
  } else {
    $file = $self->get('dumpfile');
    unless($file) {
      my $hd = $self->holdingdisk;
      my $id = $self->dumpid;
      unless(-d $hd) {
	mkdir $hd, 0777 or die "cannot create holdingdisk $hd: $!";
      }
      $file = "$hd/$id.dump";
      $self->set('dumpfile', "$file");
    }
  }
  return $file;
}

sub dumplogfile {
  logmessage_debug("GenericDumper::dumplogfile: @_");
  my $self = shift;
  my $dir = $self->logfiledir;
  unless(-d $dir) {
    mkdir $dir, 0777 or die "cannot create logdir $dir: $!";
  }
  return "$dir/" . $self->dumpid . ".dumplog";
}

sub dumptocfile {
  logmessage_debug("GenericDumper::dumptocfile: @_");
  my $self = shift;
  my $dir = $self->tocfiledir;
  unless(-d $dir) {
    mkdir $dir, 0777 or die "cannot create tocdir $dir: $!";
  }
  return "$dir/" . $self->dumpid . ".toc";
}


sub dumpqfafile {
  logmessage_debug("GenericDumper::dumpqfafile: @_");
  my $self = shift;
  my $dir = $self->tocfiledir;
  return unless $self->useqfa;
  unless(-d $dir) {
    mkdir $dir, 0777 or die "cannot create qfadir $dir: $!";
  }
  return "$dir/" . $self->dumpid . ".qfa";
}

sub restorelogfile {
  logmessage_debug("GenericDumper::restorelogfile: @_");
  my $self = shift;
  my $dir = $self->logfiledir;
  my $id = $self->dumpid;
  unless(-d $dir) {
    mkdir $dir, 0777 or die "cannot create logdir $dir: $!";
  }
  for(my $i=1;;$i++) {
    my $f = "$dir/{$id}_$i.restlog";
    return $f unless -f $f;
  }
}

sub checkcmd {
  logmessage_debug("GenericDumper::checkcmd: @_");
  my $self = shift;
  my $out = qx(which @_ 2> /dev/null);
  my $rc = $?/256;
 logmessage_debug("cmd retcode: $?, out: $out");
 logmessage("ERROR: which @_: $!") if $rc;
  return wantarray ? ($rc, $out) : $rc;
}


sub dumpcmdline {
  logmessage_debug("GenericDumper::dumpcmdline: @_");
  my $self = shift;
 logmessage
   ("ERROR: this method should never be called: GenericDumper::dumpcmdline");
  return "this_is_a_dummy_method";
}

sub listcmdline {
  logmessage_debug("GenericDumper::listcmdline: @_");
  my $self = shift;
 logmessage
   ("ERROR: this method should never be called: GenericDumper::listcmdline");
  return "this_is_a_dummy_method";
}

sub sizecmdline {
  logmessage_debug("GenericDumper::sizecmdline: @_");
  my $self = shift;
 logmessage
   ("ERROR: this method should never be called: GenericDumper::sizecmdline");
  return "this_is_a_dummy_method";
}

sub comparecmdline {
  logmessage_debug("GenericDumper::comparecmdline: @_");
  my $self = shift;
 logmessage
   ("ERROR: this method should never be called: GenericDumper::comparecmdline");
  return "this_is_a_dummy_method";
}

sub restorecmdline {
  logmessage_debug("GenericDumper::restorecmdline: @_");
  my $self = shift;
 logmessage
   ("ERROR: this method should never be called: GenericDumper::restorecmdline");
  return "this_is_a_dummy_method";
}

sub dump {
  logmessage_debug("GenericDumper::dump: @_");
  my $self = shift;
  my $cmdline = $self->dumpcmdline;
  my $logfile = $self->dumplogfile;
  my $id = $self->dumpid;
  $self->tape->fileno($self->tapeidx) unless $self->diskmode;
  logmessage("DUMP[$id]: $cmdline");
  logmessage_debug("running cmd: $cmdline");
  system("$cmdline"); 
  logmessage_debug("cmd retcode: $?");
  my ($rc, $mesg) = $self->dumpstatus($?/256, $logfile);
  if($rc) {
    logmessage("DUMP[$id]: ERROR ($mesg)");
  } else {
    logmessage("DUMP[$id]: DONE ($mesg)");
    $self->log_history;
  }
  return wantarray ? ($rc, $mesg) : $rc;
}

sub dumpstatus {
  logmessage_debug("GenericDumper::dumpstatus: @_");
  my $self = shift;
  my ($rc, $logfile) = @_;
  wantarray ? ($rc, "ERROR: see $logfile for details") : $rc;
}

sub size {
  logmessage_debug("GenericDumper::size: @_");
  my $self = shift;
  my $cmdline = $self->sizecmdline;
  my $id = $self->dumpid;
  logmessage_debug("running cmd: $cmdline");
  my $out = qx($cmdline); 
  chomp($out);
  logmessage_debug("cmd retcode: $?, output: $out");
  my $rc = $?/256;
  logmessage("DUMP[$id]: ERROR size cmd failed ($rc)") if $rc;
  return $rc == 0 ? $out : 0;
}

sub compare {
  logmessage_debug("GenericDumper::compare: @_");
  my $self = shift;
  my $cmdline = $self->comparecmdline;
  my $id = $self->dumpid;
  $self->tape->fileno($self->tapeidx) unless $self->diskmode;
  logmessage_debug("running cmd: $cmdline 2>&1");
  my $out = qx($cmdline 2>&1); 
  logmessage_debug("cmd retcode: $?, output: $out");
  my $rc = $?/256;
  return wantarray ? ($rc, $out) : $rc;
}

sub restore {
  logmessage_debug("GenericDumper::restore: @_");
  my $self = shift;
  my $cmdline = $self->restorecmdline(@_);
  my $id = $self->dumpid;
  $self->tape->fileno($self->tapeidx) unless $self->diskmode;
  logmessage_debug("running cmd: $cmdline 2>&1");
  logmessage("RESTORE[$id]: $cmdline 2>&1");
  my $cwd = POSIX::getcwd;
  chdir($self->restoredir) or 
    die "cannot access dir " .  $self->restoredir . " $!";
  my $mesg = qx($cmdline 2>&1); 
#  my $mesg = "dummy";
#  system($cmdline);
  
  chdir($cwd);
  logmessage_debug("cmd retcode: $?");
  my $rc = $?/256;
  if($rc) {
    logmessage("RESTORE[$id]: ERROR ($mesg)");
  } else {
    logmessage("RESTORE[$id]: DONE");
  }
  return wantarray ? ($rc, $mesg) : $rc;
}

sub tocfile {
  logmessage_debug("GenericDumper::tocfile: @_");
  my $self = shift;
  my $cmdline = $self->listcmdline;
  my $tocfile = $self->dumptocfile;
  my $id = $self->dumpid;
  $self->tape->fileno($self->tapeidx) unless $self->diskmode;
  logmessage_debug ("running cmd: $cmdline > $tocfile");
  system("$cmdline > $tocfile"); 
  logmessage_debug("cmd retcode: $?");
  my $rc = $?/256;
  return $rc;
}

sub list {
  logmessage_debug("GenericDumper::list: @_");
  my $self = shift;
  my $cmdline = $self->listcmdline;
  my $tocfile = $self->dumptocfile;
  my $id = $self->dumpid;
  my @toc;
  if(-f $tocfile) {		# we use the tocfile
  logmessage_debug("GenericDumper::list: using $tocfile");
    my $fh = IO::File->new($tocfile) or 
      die "cannot open tocfile: $tocfile";
    @toc = <$fh>;
  } else {
    $self->tape->fileno($self->tapeidx) unless $self->diskmode;
    logmessage_debug("GenericDumper::list:running cmd: $cmdline");
    @toc = qx($cmdline); 
    my $rc = $?/256;
    logmessage_debug("cmd retcode: $?");
    logmessage("ERROR: $cmdline: $!") if $rc;
  } 
  chomp @toc;
  logmessage_debug
    ("GenericDumper::list: number of toc-lines: " . scalar @toc);
  return wantarray ? @toc : join("\n", @toc);
}
  
sub log_history {
  logmessage_debug("GenericDumper::log_history: @_");
  my $self = shift;
  hist_insert
    ({ dumpid => $self->dumpid,
       directory => $self->directory,
       dumplevel => 
	 $self->regulardump ? $self->dumplevel : '*' . $self->dumplevel,
	 tapelabel => $self->tapelabel, 
	 tapeidx => $self->tapeidx, 
	 tapeid => $self->diskmode ? $self->dumpfile : $self->tapeid,
	 starttime => $self->starttime,
	 options => $self->histoptions,
	 tocfile => $self->dumptocfile});
}

sub histoptions {
  logmessage_debug("GenericDumper::histoptions: @_");
  return;
}

sub apply_strategy {
  logmessage_debug("GenericDumper::apply_strategy: @_");
  my $self = shift;
  my $mesg = $self->strategy;
  $mesg .= " group " . $self->group if  $self->group;
  my ($level, $label) = 
  Unidump::Strategy::nextdump($self->strategy, $self->group, $self->starttime);
  $self->dumplevel($level);
  $self->tapelabel($label);
}

sub restoredir {
  logmessage_debug("GenericDumper::restoredir: @_");
  my $self = shift;
  my $dir;
  if(@_) {
    $dir = shift;
    $self->set('restoredir', $dir);
  }
  $dir = $self->get('restoredir');
  unless(-d $dir) {
    mkdir $dir, 0777 or die "cannot create restoredir $dir: $!";
  }
  unless(-x $dir || -w $dir) {
    my $mode = (lstat($dir))[2];
    chmod $mode|0700, $dir || die "cannot set permissions in $dir: $!";
  }

#  warn "return from restoredir: $dir";

  return $dir;
}


sub holdingdisk_ok {
  logmessage_debug("GenericDumper::holdingdisk_ok: @_");
  my $self = shift;
  my $hd = $self->holdingdisk;
  my $maxsize = convert($self->holdingdisksize);
  my $size = $self->size; 

  return unless $maxsize;
  if($maxsize >= 0) {
    my $hdsize = (split(' ', qx(du -bs $hd)))[0];
    return $maxsize > ($hdsize + $size/2) ? 1 : 0;
  }
  my $hdfree = 1024*(split(' ', qx(df -k $hd | tail +2)))[3]
    + $maxsize;

  return $hdfree > $size/2 ? 1 : 0; 
}

sub support_compression {
  logmessage_debug("GenericDumper::support_compression: @_");
  my $self = shift;
  return 0;
}

sub exclude_list {
  logmessage_debug("GenericDumper::exclude_list: @_");
  my $self = shift;
  return unless $self->exclude;
  return split(/(?<=[^\\]):/, $self->exclude);
}

1;
__END__
