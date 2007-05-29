# 	$Id: Tape.pm,v 1.2 2003/09/08 07:14:37 thorsten Exp $	
package Unidump::Tape;
use base qw(Class::Accessor);
use strict;
use IO::File;
use Unidump::Logger qw(logmessage logmessage_debug);
use vars qw($VERSION);
use Exporter;
$VERSION = do{my @r = split(" ",qq$Revision: 1.2 $ );$r[1];};

Unidump::Tape->mk_accessors(qw(mt dd ntapedevice blocksize 
			       hwcompression magicfile mtcanlock stacker
			       tapelabel tapeid tapecycle));

use vars qw(%gmt_mesg);

%gmt_mesg = ( EOF => 'EOF (end of file)',
	      BOT => 'BOT (begin of tape)',
	      EOT => 'EOT (end of tape)',
	      SM  => 'SM (DDS setmark)',
	      EOD => 'EOD (end of data)',
	      WR_PROT => 'WR_PROT (write protected)',
	      ONLINE  => 'ONLINE (tape ready)',
	      D_6250  => 'D_6250',
	      D_1600  => 'D_1600',
	      D_800   => 'D_800',
	      DR_OPEN => 'DR_OPEN (door open / no tape)',
	      IM_REP_EN => 'IM_REP_EN (immediate report mode)');


sub GMT_EOF { $_[0] & 0x80000000; }
sub GMT_BOT { $_[0] & 0x40000000; }
sub GMT_EOT { $_[0] & 0x20000000; }
sub GMT_SM  { $_[0] & 0x10000000; }
sub GMT_EOD { $_[0] & 0x08000000; }
sub GMT_WR_PROT { $_[0] & 0x04000000; }
sub GMT_ONLINE { $_[0] & 0x01000000; }
sub GMT_D_6250 { $_[0] & 0x00800000; }
sub GMT_D_1600 { $_[0] & 0x00400000; }
sub GMT_D_800  { $_[0] & 0x00200000; }
sub GMT_DR_OPEN{ $_[0] & 0x00040000; }
sub GMT_IM_REP_EN{ $_[0] & 0x00010000; }



sub init {
 logmessage_debug("Tape::init: @_");
  my $self = shift;
  $self->rewind;
  if($self->hwcompression) {
    $self->enable_hwcompression;
  }
}

sub check {
  logmessage_debug("Tape::check: @_");
  my $self = shift;
  return scalar $self->status;
}

sub is_eod {
  my $self = shift;
  return grep(/^EOD$/, $self->status);
}

sub is_bot {
  my $self = shift;
  return grep(/^BOT$/, $self->status);
}

sub is_eot {
  my $self = shift;
  return grep(/^EOT$/, $self->status);
}

sub is_writeprotected {
  my $self = shift;
  return grep(/^WR_PROT$/, $self->status);
}

sub is_online {
  my $self = shift;
  return grep(/^ONLINE$/, $self->status);
}

sub is_open {
  my $self = shift;
  return grep(/^DR_OPEN$/, $self->status);
}

sub finalize {
 logmessage_debug("Tape::finalize: @_");
  my $self = shift;
  if($self->hwcompression) {
    $self->disable_hwcompression;
  }
  $self->retension;
}

sub runmt {
  logmessage_debug("Tape::runmt: @_");
  my $self = shift;
  my ($cmd, $out, $rc);
  $cmd = join(" ", $self->mt, "-f", $self->ntapedevice, @_, "2>&1");
  $out = qx($cmd);
  $rc = $?/256;
  die "command `$cmd' failed: $out" unless $rc == 0;
  logmessage_debug("mt retcode: $?, output: $out");
  return $out;
}

sub ddread { 
 logmessage_debug("Tape::ddread: @_");
  my $self = shift;
  local(*P, $/);
  my $bs = $self->blocksize ? "bs=" . $self->blocksize : "";
  my $cmd = 
    join(" ", $self->dd, $bs, "if=" . $self->ntapedevice, @_, "2> /dev/null");
  open(P, "$cmd |") or die "open pipe `$cmd |' failed: $!";
  undef($/);
  my $data = <P>;
  close(P) or die "close pipe `$cmd |' failed: $!";
  $data;
}

sub ddwrite { 
  logmessage_debug("Tape::ddwrite: @_");
  my $self = shift;
  local(*P);
  my $data = shift;
  my $bs;
  if($self->blocksize) {
    $bs  = "bs=" . $self->blocksize;
    $bs .= " conv=block cbs=" . $self->blocksize;
  }
  my $cmd = 
    join(" ", $self->dd, $bs, "of=" . $self->ntapedevice, @_, "2> /dev/null");
  open(P, "| $cmd") or die "open pipe `| $cmd' failed: $!";
  print P $data;
  close(P) or die "close pipe `| $cmd' failed: $!";
}
  
sub ddreadblock { 
 logmessage_debug("Tape::ddreadblock: @_");
  my $self = shift;
  return $self->ddread("count=1 @_"); 
}

sub ddwriteblock { 
 logmessage_debug("Tape::ddwriteblock: @_");
  my $self = shift;
  return $self->ddwrite(shift, "count=1 @_"); 
}

sub status { 
  logmessage_debug("Tape::status: @_");
  my $self = shift; 
  my $version = $self->mtversion;
  my ($i, $stat, @stat, $mesg, @mesg);
  for ($i=0;;$i++) {
    return wantarray ? ("no response from tape") : undef if $i > 60;
    eval {
      $mesg = $self->runmt('status');
    };
    if($@) {			# we got an error
      chomp($@);
      if($@ =~ /input.output.error/i) { # we ignore I/O errors for 60 sec
	logmessage_debug("I/O error from tape, waiting 1 sec");
	sleep(1), next if ($i < 60);
      }
      if($@ =~ /no.medium.found/i) { # GNU mt returns an error in this case
	logmessage_debug("tapestatus: $@");
	return wantarray ? ($@, "DR_OPEN") : undef; # fake mt-st output
      }
      if($@ =~ /device.or.resource.busy/i) { 
	logmessage_debug("tape busy, waiting 1 sec");
	sleep(1), next if ($i < 60);
      }
      logmessage_debug("tapestatus: ERROR: $@");
      return wantarray ? ($@) : undef;
    }
    chomp($mesg);
    @mesg = split(/\n/, $mesg);
    chomp(@mesg);
#      if($version =~ /mt-st/) {
#        @stat = split(' ', pop(@mesg));
#        @stat = grep { !/^IM_REP_EN$/ } @stat; # weed out the IM_REP_EN reply
#      } else {
#        @stat = (@mesg, "ONLINE"); # fake mt-st output; should be ok, GNU mt
#  				# returns an error if it isn't online
#      }
    my $bits;
    BITS: foreach my $l (@mesg) {
      if($l =~ /general.status.bits[^\d]*((0x)?\d+)/i) {
	$bits = hex($1);
	last BITS;
      }
      if($l =~ /gstat[^\d]*((0x)?\d+)/i) {
	$bits = hex($1);
	last BITS;
      }
    };
    logmessage_debug("tape status bits: $bits");
    foreach my $b ($bits) {
      GMT_EOF($b) && push(@stat, 'EOF'); 
      GMT_BOT($b) && push(@stat, 'BOT');
      GMT_EOT($b) && push(@stat, 'EOT'); 
      GMT_SM($b) && push(@stat, 'SM'); 
      GMT_EOD($b) && push(@stat, 'EOD');
      GMT_WR_PROT($b) && push(@stat, 'WR_PROT');  
      GMT_ONLINE($b) && push(@stat, 'ONLINE');
      GMT_D_6250($b) && push(@stat, 'D_6250'); 
      GMT_D_1600($b) && push(@stat, 'D_1600'); 
      GMT_D_800($b) && push(@stat, 'D_800'); 
      GMT_DR_OPEN($b) && push(@stat, 'DR_OPEN');
      GMT_IM_REP_EN($b) && push(@stat, 'IM_REP_EN');    
    }

    last if @stat;		# break out the loop if we got an answer
    logmessage_debug("no response from tape, waiting 1 sec");
    sleep(1);
  }
  logmessage_debug("tapestatus: @stat");
  $stat = grep(/^ONLINE$/, @stat) ? "ONLINE" : undef;
  return wantarray ? @stat : $stat;
}

sub status_gmt {
  logmessage_debug("Tape::status: @_");
  my $self = shift; 
  my ($i, $stat, @stat, $mesg, @mesg);
  for ($i=0;;$i++) {
    return wantarray ? ("no response from tape") : undef if $i > 60;
    eval {
      $mesg = $self->runmt('status');
    };
    if($@) {			# we got an error
      chomp($@);
      if($@ =~ /input.output.error/i) { # we ignore I/O errors for 60 sec
	logmessage_debug("I/O error from tape, waiting 1 sec");
	sleep(1), next if ($i < 60);
      }
      logmessage_debug("tapestatus: ERROR: $@");
      return wantarray ? ($@) : undef;
    }
    chomp($mesg);
    @mesg = split(/\n/, $mesg);
    chomp(@mesg);
    @stat = split(' ', pop(@mesg));
    @stat = grep { !/^IM_REP_EN$/ } @stat; # weed out the IM_REP_EN reply
    last if @stat;		# break out the loop if we got an answer
    logmessage_debug("no response from tape, waiting 1 sec");
    sleep(1);
  }
  logmessage_debug("tapestatus: @stat");
  $stat = grep(/^ONLINE$/, @stat) ? "ONLINE" : undef;
  return wantarray ? @stat : $stat;
}




sub rewind { 
 logmessage_debug("Tape::rewind: @_");
  my $self = shift; 
  $self->runmt('rewind') 
}

sub retension { 
 logmessage_debug("Tape::retension: @_");
  my $self = shift; 
  $self->runmt('retension'); 
}

sub erase { 
 logmessage_debug("Tape::erase: @_");
  my $self = shift; 
 logmessage_debug("erasing tape");
  $self->runmt("erase");
}

sub eod {
 logmessage_debug("Tape::eod: @_");
  my $self = shift; 
 logmessage_debug("spacing tape to EOD");
  $self->runmt("eod"); 
}

sub eject { 
 logmessage_debug("Tape::eject: @_");
  my $self = shift; 
  $self->offline; 
}

sub lock { 
 logmessage_debug("Tape::lock: @_");
  my $self = shift; 
  for($self->mtversion) {
    /mt-st/ and $self->runmt("lock");
  }
  return;
}

sub unlock {  
 logmessage_debug("Tape::unlock: @_");
  my $self = shift; 
  for($self->mtversion) {
    /mt-st/ and $self->runmt("unlock");
  }
  return;
}

sub load { 
 logmessage_debug("Tape::load: @_");
  my $self = shift; 
  for($self->mtversion) {
    /mt-st/ and $self->runmt("load");
  }
  return;
}

sub offline { 
 logmessage_debug("Tape::offline: @_");
  my $self = shift; 
  $self->runmt("offline");
}

sub fileno {
  logmessage_debug("Tape::fileno: @_");
  my $self = shift; 
  my ($file, $block, $part);
  if(@_) {
    logmessage_debug("spacing tape to file: @_");
    my $n = shift;
    if($n =~ /^[+-]\d+/) {
      if(int($n) < 0) {
	$self->runmt(join(" ", "bsfm", - int($n)));
      } else {
	$self->runmt(join(" ", "fsf", int($n)));
      }
    } else {
      $self->runmt(join(" ", "asf", int($n)));
    }
  }
  logmessage_debug("getting fileno of tape");
  $self->status;		# wait for tape to come up
  foreach(split(/\n/, $self->runmt('status'))) {
    /(file\s*number)[\s=:]+(\d+)/i and $file = $2;
    /(block\s*number)[\s=:]+(\d+)/i and $block = $2;
    /(partition\s*number)[\s=:]+(\d+)/i and $part = $2;
  }
  return $file;
#  return wantarray ? ($file, $block, $part) : $file;
}

sub enable_hwcompression { 
 logmessage_debug("Tape::enable_hwcompression: @_");
  my $self = shift;
  my ($rc, $out);
  for($self->mtversion) {
    /GNU/   and ($rc, $out) = $self->runmt("datcompression 2");
    /mt-st/ and ($rc, $out) = $self->runmt("compression 1");
  }
  return wantarray ? ($rc, $out) : $rc;
}

sub disable_hwcompression { 
 logmessage_debug("Tape::disable_hwcompression: @_");
  my $self = shift;
  my ($rc, $out);
  for($self->mtversion) {
    /GNU/   and ($rc, $out) = $self->runmt("datcompression 0");
    /mt-st/ and ($rc, $out) = $self->runmt("compression 0");
  }
  return wantarray ? ($rc, $out) : $rc;
}


sub nexttape {
 logmessage_debug("Tape::nexttape: @_");
  my $self = shift; 
  if($self->stacker) {
    $self->offline();
    $self->load();
  }
}
		
sub getblocksize {
  logmessage_debug("Tape::getblocksize: @_");
  my $self = shift; 
  logmessage_debug("guessing blocksize of tape");
  my ($block, $rc);
  my $bs=8*1024*1024; # start guessing with 4MB blocksize
  $self->set("blocksize", undef);
  for(;;) {
    $bs /= 2;
    die "cannot determine blocksize" if $bs < 1;
    $self->rewind;
    eval {
      $block = $self->ddread("bs=$bs count=1 2>/dev/null");
    };
    next if $@;
    last if $block;
  }
  return length($block);
}

sub gen_tapelabel {
 logmessage_debug("Tape::gen_tapelabel: @_");
  my $self = shift;
  pack("Z8Z6Z30Z3Z38Z6Z5", 
       "UNIDUMP", "LABEL", $self->tapelabel, 
       "ID", $self->tapeid, "CYCLE", $self->tapecycle);
}

sub parse_tapelabel {
 logmessage_debug("Tape::parse_tapelabel: @_");
  my $self = shift;
  my ($t, $l, $id, $c);
  ($t, undef, $l, undef, $id, undef, $c) = 
    unpack("Z8Z6Z30Z3Z38Z6Z5", shift);
  return unless $t =~ /^UNIDUMP$/i;
  $self->tapelabel($l);
  $self->tapeid($id);
  $self->tapecycle($c);
  return wantarray ? ($l, $id, $c) : 1;
}

sub gmt_mesg {
 logmessage_debug("Tape::gmt_mesg: @_");
  my $self = shift;
  my @mesg;
  while(@_) {
    my $key = shift;
    unshift(@mesg, $gmt_mesg{$key});
  }
  return @mesg;
}

sub mtversion {
  logmessage_debug("Tape::mtversion: @_");
  my $self = shift;
  foreach (split (/\n/, $self->runmt('--version'))) {
    /GNU/ and return 'GNU';
    /mt-st/ and return 'mt-st';
  }
  return;
}

sub dumptype {
  logmessage_debug("Tape::filetype: @_");
  my $self = shift;
  my $magicfile = $self->magicfile;
  my $tapeidx = $self->fileno();
  my $compress = 0;
  my $tmpfile;
  my @res;

  do {
    $tmpfile = POSIX::tmpnam;
  } until sysopen(TMP, $tmpfile, O_RDWR|O_CREAT|O_EXCL, 0600);
  print TMP $self->ddreadblock;
  close(TMP);
  my $file = qx(cat $tmpfile | file -b -m $magicfile - 2> /dev/null);
  if($file =~ /compressed/i) {
    $file = qx(gzip -dc $tmpfile | file -b -m $magicfile - 2> /dev/null);
    $compress = 1;
  }
  $self->fileno("-1");
  $self->fileno($tapeidx) unless (scalar($self->fileno) == $tapeidx);
  
  #logmessage_debug("Tape::filetype: for $file");
 SWITCH: for ($file) {
   /unidump/i and do {
     @res = ("unidump", undef, undef);
     last SWITCH;
   };
   /xfs dump/i and do {
     /session.?label\s+([\w-]+)[\s,]+/i;
     @res = ("xfsdump", $1, $compress);
     last SWITCH;
   };
   /dump/i    and do {
     /label\s+([\w-]+)[\s,]+/i;
     @res = ("dump", $1, $compress);
     last SWITCH;
   };
   /tar/ and do {
     /POSIX/ and do { 
       @res = ("star", undef, $compress);
       last SWITCH;
     };
     my $z = $compress ? '-z' : ''; 
     if(open(P, "tar -tv $z -f $tmpfile 2> /dev/null |")) { 
       my $l = <P>;
       chomp($l);
       if($l =~ /^V/) {
	 $l =~ s/--Volume Header--$//;
	 my @l = split(' ', $l, 6);
	 @res = ("gtar", $l[5], $compress);
	 #logmessage_debug("Tape::filetype: tar: $l=$l, res=(@res)");
	 last SWITCH;
       }
     };
     @res = ("gtar", undef, $compress);
     last SWITCH;
   };
   /empty/i and do {
     @res = ("empty", 0, 0);
     last SWITCH;
   };
 }
  unlink($tmpfile);
  return @res;
}
  
1;

__END__
