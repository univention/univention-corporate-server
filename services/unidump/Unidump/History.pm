# 	$Id: History.pm,v 1.21 2003/11/10 09:49:54 thorsten Exp $	
package Unidump::History;
use strict;
use Fcntl;
use Unidump::Logger qw(logmessage logmessage_debug);
use Unidump::Units qw(convert);
use vars qw(@ISA @EXPORT @EXPORT_OK %EXPORT_TAGS $VERSION);
use Exporter;
use IO::File;
use File::Copy qw (cp);
#use Data::Dumper;
$VERSION = do{ qq$Revision: 1.21 $ =~ /\d+\.\d+/, $&; };
@ISA = qw(Exporter);

@EXPORT = qw();
@EXPORT_OK = qw(hist_delete hist_dump_exist hist_dump_is_obsolete
		hist_insert hist_get hist_get_ancestors 
		hist_get_descendants hist_get_directory 
		hist_get_dumplevel hist_get_options hist_get_tapelabel 
		hist_get_tapeidx hist_get_tapeid hist_get_starttime
		hist_lookup hist_get_parent hist_get_restorelist
		hist_history_save hist_read hist_write);
%EXPORT_TAGS = (all => [@EXPORT_OK]);

use vars qw($historydir);

$historydir  = "/var/lib/unidump";
my %history;


sub LOCK_SH { 1 }
sub LOCK_EX { 2 }
sub LOCK_NB { 4 }
sub LOCK_UN { 8 }

sub historyfile {
  $historydir =~ s@/$@@;
  system("touch", "$historydir/history.txt") 
    unless(-f "$historydir/history.txt");
  return "$historydir/history.txt";
  
}

sub hist_insert {
  logmessage_debug("History::hist_insert: @_");
  my ($dumpid, $directory, $dumplevel, $tapelabel,
      $tapeidx, $tapeid, $starttime, $options);
  if(ref($_[0]) =~ /HASH/) {
    ($dumpid, $directory, $dumplevel, $tapelabel,
      $tapeidx, $tapeid, $starttime, $options) = 
	($_[0]->{dumpid}, $_[0]->{directory}, $_[0]->{dumplevel}, 
	 $_[0]->{tapelabel}, $_[0]->{tapeidx}, $_[0]->{tapeid}, 
	 $_[0]->{starttime}, $_[0]->{options});
  } else {
    ($dumpid, $directory, $dumplevel, $tapelabel, $tapeidx, 
     $tapeid, $starttime, $options) = @_;
  }
  hist_read();
  $history{$dumpid} = "$directory $dumplevel $tapelabel"
    . " $tapeidx $tapeid $starttime $options";
  hist_write();
}

sub hist_delete {
  logmessage_debug("History::hist_delete: @_");
  my @dumpids = @_;
  hist_read();
  cp(historyfile(), historyfile() . ".deleted");
  foreach my $did (@dumpids) {
    delete($history{$did}) if hist_dump_is_obsolete($did);
  }
  return hist_write();
}

sub hist_write {
  logmessage_debug("History::hist_write:");
  my $historyfile = historyfile();
  unless(%history) {
    logmessage("I won't write an empty history file!");
    return;
  }
  unless(rename("$historyfile", "$historyfile.bak")) {
    logmessage("cannot rename file: $!");
    return;
  }
  local(*FH);
  unless(open (FH, "> " . historyfile())) {
    logmessage("file not writable: $historyfile: $!");
    rename("$historyfile.bak", "$historyfile");
    return;
  }
  unless(flock(FH, LOCK_EX|LOCK_NB)) {
    logmessage("waiting to get exclusive lock on file ...");
    unless(flock(FH, LOCK_EX)) {
      logmessage("cannot get exclusive lock on file: $!");
      rename("$historyfile.bak", "$historyfile");
      return;
    }
  }
  my $i;
  while(my($k,$v) = each %history) {
    print FH "$k $v\n" and $i++;
  }
  close(FH);
  return $i;
}

sub hist_read {
  logmessage_debug("History::hist_read:");
  my $historyfile = historyfile();
  local(*FH);
  unless(open (FH, "$historyfile")) {
    logmessage("file not readable: $historyfile: $!");
    return;
  }
  unless(flock(FH, LOCK_SH|LOCK_NB)) {
    logmessage("waiting to get shared lock on file ...");
    unless(flock(FH, LOCK_SH)) {
      logmessage("cannot get shared lock on file: $!");
      return;
    }
  }
  %history = ();		# empty history hash
  while(<FH>) {			# read histfile line-by-line
    chomp;
    /^\s*$/ and next;		# skip blank lines
    my($k, $v) = split(' ', $_, 2);
    $history{$k} = $v;
  }
  close(FH);
}

sub hist_get {
  logmessage_debug("History::hist_get: @_");
  my ($dumpid) = @_;
  hist_read() unless %history;
  if($dumpid) {
    my $res = $history{$dumpid};
    return unless $res;
    return wantarray ? split(' ', $res) : $res;
  } else {
    my @res = keys %history;
    return @res;
  }
}

sub hist_get_directory { return (hist_get(@_))[0] if @_; }
sub hist_get_dumplevel { return (hist_get(@_))[1] if @_; }
sub hist_get_tapelabel { return (hist_get(@_))[2] if @_; }
sub hist_get_tapeidx { return (hist_get(@_))[3] if @_; }
sub hist_get_tapeid { return (hist_get(@_))[4] if @_; }
sub hist_get_starttime { return (hist_get(@_))[5] if @_; }
sub hist_get_options { return (hist_get(@_))[6] if @_; }

sub hist_lookup {
  logmessage_debug("History::hist_lookup: @_");
  my ($dumpid, $directory, $dumplevel, $tapelabel,
      $tapeidx, $tapeid, $starttime, $before, $after);
  if(ref($_[0]) =~ /HASH/) {
    ($dumpid, $directory, $dumplevel, $tapelabel,
      $tapeidx, $tapeid, $starttime, $before, $after) = 
	($_[0]->{dumpid}, $_[0]->{directory}, $_[0]->{dumplevel}, 
	 $_[0]->{tapelabel}, $_[0]->{tapeidx}, $_[0]->{tapeid}, 
	 $_[0]->{starttime}, $_[0]->{before}, $_[0]->{after})
  } else {
    ($dumpid, $directory, $dumplevel, $tapelabel, $tapeidx, 
     $tapeid, $starttime) = @_;
  }
  
  my (%res, @h);
  @h = hist_get();
  foreach my $k (hist_get()) {
    my $v = hist_get($k);
    my @l = split(' ', $v);
    if (defined $dumpid)    { next unless ($k    =~ /^$dumpid$/); }
    if (defined $directory) { next unless ($l[0] =~ /^$directory$/); }
    if (defined $dumplevel) { next unless ($l[1] =~ /^$dumplevel$/); }
    if (defined $tapelabel) { next unless ($l[2] =~ /^$tapelabel$/); }
    if (defined $tapeidx)   { next unless ($l[3] =~ /^$tapeidx$/); }
    if (defined $tapeid)    { next unless ($l[4] =~ /^$tapeid$/); }
    if (defined $starttime) { next unless ($l[5] =~ /^$starttime$/); }
    if (defined $before)    { next unless ($l[5] < $before); }
    if (defined $after)     { next unless ($l[5] > $after); }
    $res{$k} = $v;
  }
  return %res;
}

sub hist_get_parent {
  logmessage_debug("History::hist_get_parent: @_");
  my ($directory, $dumplevel, $starttime);
  if(ref($_[0]) =~ /HASH/) {
    ($directory, $dumplevel, $starttime) = 
	($_[0]->{directory}, $_[0]->{dumplevel}, $_[0]->{starttime});
  } else {
    ($directory, $dumplevel, $starttime) = @_;
  }
  
  return if $dumplevel =~ /^\*?0$/;

  my @parent;
  my %hist = hist_lookup({directory => $directory});
  $starttime = time() unless defined $starttime;
  while(my ($key, $val) = each %hist) {
    my @val = split(' ', $val); 
    next unless ($val[1] =~ /^[0-9]$/);	# skip over non-regular dumps *n
    next unless ($val[1] < $dumplevel);	# skip over equal or higher level dumps
    next unless ($val[5] < $starttime);	# skip over newer dumps
    if ($val[5] > ($parent[6] || 0)) {
      @parent = ($key, @val);
    }
  }
#  return unless(hist_dump_exist($parent[0]));
  return wantarray ? @parent : $parent[0];
}

sub hist_dump_exist {
  logmessage_debug("History::hist_dump_exist: @_");
  my $key  = shift;
  my ($tape, $date) = (hist_get($key))[4,5];
  return 0 if hist_lookup({tapeid => $tape, after => $date});
  return 1;
}

sub hist_get_ancestors {
  logmessage_debug("History::hist_get_ancestors: @_");
  my $thisdump  = shift;
  my @dumps = $thisdump;
  while(hist_get_dumplevel($dumps[0])) {
    my ($d, $l, $t) = (hist_get($dumps[0]))[0,1,5];
    my $parent = hist_get_parent($d, $l, $t);
    last unless $parent; # leave the loop if we didn't get a parent
    unshift(@dumps, $parent);
  }
  pop @dumps;			# remove $thisdump from list
  return reverse @dumps;	# return newest first
}


sub hist_get_descendants {
  logmessage_debug("History::hist_get_descendants: @_");
  my $thisdump  = shift;
  my @descendants;
  my @ancestors;
  my ($thisdir, $thislevel, $thisdate) = (hist_get($thisdump))[0,1,5];
  return unless $thisdir;
  return unless $thislevel =~ /^\d$/;
  foreach my $d (hist_get()) {
    my ($dir, $level, $date) = (hist_get($d))[0,1,5];
    next unless ($dir eq $thisdir);
    $level =~ s/^[^\d]//;
    next unless ($level > $thislevel);
    next unless ($date > $thisdate);
    my @ancestors = hist_get_ancestors($d);
    push(@descendants, $d)
      if (grep { /^$thisdump$/ } @ancestors);
  }
  return @descendants;
}

sub hist_get_restorelist {
  logmessage_debug("History::hist_get_restorelist: @_");
  my ($directory, $starttime);
  if(ref($_[0]) =~ /HASH/) {
    ($directory, $starttime) = 
      ($_[0]->{directory}, $_[0]->{starttime});
    if($_[0]->{dumpid}) {
      ($directory, $starttime) = (hist_get($_[0]->{dumpid}))[0,5];
    }
  } else {
    ($directory, $starttime) = @_;
  }
  
  # we fetch all ever-made dumps of directory older than starttime
  my %alldumps = hist_lookup({ directory => $directory,
			       before => $starttime });


  # buils a time-sorted list of the dumpids (oldest first)
  my @alldumps = 
    sort { hist_get_starttime($a) <=> hist_get_starttime($b) } keys %alldumps;

  #warn "alldumps:" . join(" ", @alldumps);

  # now we lookup the newest dump which wasn't overwritten
  my ($lastdump, @dumps);
  OUTER: while ($lastdump = pop @alldumps) {
    next unless hist_dump_exist($lastdump);
    
    #warn "lastdump: $lastdump";

    # now build the list of ancestors of $lastdump (oldest first)
    @dumps = ($lastdump);
    #warn "dumps: @dumps";
    INNER: while(! (hist_get_dumplevel($dumps[0]) =~ /\*?0$/)) {
      my ($d, $l, $t) = (hist_get($dumps[0]))[0,1,5];
      my $parent = hist_get_parent($d, $l, $t);
      #warn "parent of ($d, $l, $t): $parent\n";
      next OUTER unless $parent; # leave the loop if we didn't get a parent
      next OUTER unless hist_dump_exist($parent); # leave the loop if a dump is missing
      unshift(@dumps, $parent);
    }
    return @dumps;
  }
  return;			# no data restorable, sorry
}

sub hist_dump_is_obsolete {
  logmessage_debug("History::hist_dump_is_obsolete: @_");
  my $thisdump = shift;
  # a dump entry is obsolete, if the dump was on a tape that is 
  # overwritten by a new dump. 
  # If the dump is on holdingdisk, is is obsolete if the tape 
  # on that the dump should have been written has been re-used.
  # As we don't know a tapeid here, we use the tapelabel instead.

  my %newdumps;
  my $thistlabel = hist_get_tapelabel($thisdump);
  my $thistid    = hist_get_tapeid($thisdump);
  my $thistidx   = hist_get_tapeidx($thisdump);
  my $thistime = hist_get_starttime($thisdump);
  
  if($thistidx =~ /\d/) {	# the dump is on a tape
    # now look for a newer dump on the same tape
    %newdumps = hist_lookup({tapeid => $thistid,
			     after => $thistime});
  } else {
    %newdumps = hist_lookup({tapelabel => $thistlabel,
			     after => $thistime});
  }
  return %newdumps ? 1 : 0;
}

 
#  sub hist_history_save {
#    logmessage_debug("History::hist_history_save: @_");
#    my($tar, $dev) = @_;
#    my $hdir  = $historydir;
#    my $hfile = historyfile();
#    $hfile =~ s@.*/@@;
#    my $cmdline = "$tar -c -C $hdir -f $dev $hfile";
#    logmessage("DUMP[history_save]: $cmdline");
#    logmessage_debug("running cmd: $cmdline");
#    system("$cmdline"); 
#    logmessage_debug("cmd retcode: $?");
#    my ($rc, $mesg) = ($?/256, $!);
#    if($rc) {
#      logmessage("DUMP[history_save]: ERROR ($mesg)");
#    } else {
#      logmessage("DUMP[history_save]: DONE");
#    }
#    return wantarray ? ($rc, $mesg) : $rc;
#  }

sub hist_history_save {
  logmessage_debug("History::hist_history_save: @_");
  my($tar, $dev, $unidir) = @_;
  my $fh = new IO::File;
  my ($tmpdir, %nonroot, %nonrootdisk, $rootdisk, $rootdisk_bare, 
      $rootpart, $rootfs, $bootpart, $bootfs, @swappart, %nonrootdir);
  my $hfile = historyfile();
  do {
    $tmpdir = POSIX::tmpnam;
  } until mkdir $tmpdir;
  system "cp $hfile $tmpdir";
  system "cp $unidir/magic $tmpdir";
  system "cp /usr/bin/file $tmpdir";
  system "cp $unidir/scripts/restore_root.sh $tmpdir";
  system "cp $unidir/scripts/functions.sh $tmpdir";

  # get the devices from /etc/mtab
  if($fh->open("< /etc/mtab")) {
    while(<$fh>) {
      next if /^\s*$/;
      my @line = split(' ');
      next if $line[0] eq "none";
      next unless $line[0] =~ "^/";
      next if $line[1] =~ "^/proc";
      next if $line[2] eq "iso9660";
      next if $line[2] eq "vfat";
      next if $line[2] eq "fat";
      next if $line[2] eq "nfs";
      next if $line[3] =~ "\bnoauto\b";
      next if $line[3] =~ "\bnoauto\b";
      
      if($line[1] eq '/') {
	($rootpart, $rootdisk, $rootfs) = @line[0,0,2];
	$rootdisk =~ s/\d+$//;
	$rootdisk_bare = do { $rootdisk =~ m@[^/]+$@; $&; };
      } elsif($line[1] eq '/boot') {
	($bootpart, $bootfs) = @line[0,2];
      } else {
	my ($part, $disk, $fs) = @line[0,0,2];
	$disk =~ s/\d+$//;
	$nonroot{$line[1]} = {};
	$nonroot{$line[1]}->{'disk'} = $disk;
	$nonroot{$line[1]}->{'disk_bare'} = do { $disk =~ m@[^/]+$@; $&; };
	$nonroot{$line[1]}->{'part'} = $part;
	$nonroot{$line[1]}->{'fs'} = $fs;
	$nonrootdisk{$disk}++ 
	  if ($disk ne $rootdisk and $disk =~ m@^/dev/[hs]d[a-z]+$@);
      }
    }
  } else {
    die "cannot open /etc/mtab: $!";
  }
  
  # get swap devices
  if($fh->open("< /proc/swaps")) {
    while(<$fh>) {
      next if /^\s*$/;
      my @line = split(' ');
      next unless $line[1] eq "partition";
      push(@swappart, $line[0]);
    }
  } 


  $fh->open(">$tmpdir/rootfs.disk") 
    or die "cannot open $tmpdir/rootfs.disk: $!";
  print $fh "$rootdisk\n";
  $fh->open(">$tmpdir/rootfs.part") 
    or die "cannot open $tmpdir/rootfs.part: $!";
  print $fh "$rootpart\n";
  system("sfdisk -d $rootdisk | grep -E -e '^(unit|/dev|\$)' > $tmpdir/$rootdisk_bare.ptable")
    && die "cannot write partition table to $tmpdir/$rootdisk_bare.ptable: $!";
  system("sfdisk -l -uM $rootdisk > $tmpdir/$rootdisk_bare.ptable.txt")
    && warn 
      "cannot write partition table to $tmpdir/$rootdisk_bare.ptable.txt: $!";
  $fh->open(">$tmpdir/rootfs.mkfs.sh") || 
    die "cannot open $tmpdir/rootfs.mkfs.sh: $!";
 SWITCH: for($rootfs) {
   /ext2/ and do { print $fh "#!/bin/sh\nmke2fs \$*\n"; last; };
   /ext3/ and do { print $fh "#!/bin/sh\nmke2fs -j \$*\n"; last; };
   /xfs/  and do { print $fh "#!/bin/sh\nmkfs.xfs -f \$*\n"; last; };
   print $fh "#!/bin/sh\nmkfs.$rootfs \$*\n"; last;
 }
  $fh->open(">$tmpdir/rootfs.restore.sh") 
    || die "cannot open $tmpdir/rootfs.restore.sh: $!";
  print $fh join("\n",
		 '#!/bin/sh',
		 '. functions.sh',
		 'myself=`echo $0 | sed "s@.*/@@"`;',
		 '[ "$#" = "1" ] || error_exit "usage: $myself <directory>"',
		 'cd_or_die $1;', '');
  foreach my $did (hist_get_restorelist("/", time())) {
    my $tlabel = hist_get_tapelabel($did);
    my $tid    = hist_get_tapeid($did);
    my $tidx   = hist_get_tapeidx($did);
    my $level  = hist_get_dumplevel($did);
    my $dopts  = hist_get_options($did);
    my $bs     = do { $dopts =~ /\b\d+[kMG]?\b/; $&; };
    $bs        = convert($bs);
    my $zip    = do { $dopts =~ /\b(gzip|bzip2|z)\b/; $&; };
    my $hwc    = do { $dopts =~ /\bhw\b/ ? 1 : 0 ; };
    my $dfmt   = do { $dopts =~ /^\w+/; $&; };
    $zip = '' unless $zip;

    print $fh 
      "\n# restore dump level $level\n",
      "ask_for_tape $dev $bs $tlabel $tid;\n",
      "mt -f $dev datcompression $hwc;\n",
      "mt -f $dev asf $tidx;\n",
      "check_dumplabel $dev $bs $did;\n",
      "mt -f $dev asf $tidx;\n",
      "f_restore $dev $bs $dfmt $did $zip;\n",
      "mt -f $dev rewind\n";
  }

  
  if (defined $bootpart) {
    $fh->open(">$tmpdir/bootfs.part") 
      or die "cannot open $tmpdir/bootfs.part: $!";
    print $fh "$bootpart\n";
    
    $fh->open(">$tmpdir/bootfs.mkfs.sh") || 
      die "cannot open $tmpdir/bootfs.mkfs.sh: $!";
  SWITCH: for($bootfs) {
    /ext2/ and do { print $fh "#!/bin/sh\nmke2fs \$*\n"; last; };
    /ext3/ and do { print $fh "#!/bin/sh\nmke2fs -j \$*\n"; last; };
    /xfs/  and do { print $fh "#!/bin/sh\nmkfs.xfs -f \$*\n"; last; };
    print $fh "#!/bin/sh\nmkfs.$bootfs \$*\n"; last;
  }
    
    $fh->open(">$tmpdir/bootfs.restore.sh") 
      || die "cannot open $tmpdir/bootfs.restore.sh: $!";
    print $fh join("\n",
		   '#!/bin/sh',
		   '. functions.sh',
		   'myself=`echo $0 | sed "s@.*/@@"`;',
		   '[ "$#" = "1" ] || error_exit "usage: $myself <directory>"',
		   'cd_or_die $1;', '');
    foreach my $did (hist_get_restorelist("/boot", time())) {
      my $tlabel = hist_get_tapelabel($did);
      my $tid    = hist_get_tapeid($did);
      my $tidx   = hist_get_tapeidx($did);
      my $level  = hist_get_dumplevel($did);
      my $dopts  = hist_get_options($did);
      my $bs     = do { $dopts =~ /\b\d+[kMG]?\b/; $&; };
      $bs        = convert($bs);
      my $zip    = do { $dopts =~ /\b(gzip|bzip2|z)\b/; $&; };
      my $hwc    = do { $dopts =~ /\bhw\b/ ? 1 : 0 ; };
      my $dfmt   = do { $dopts =~ /^\w+/; $&; };
      $zip = '' unless $zip;
      
      print $fh 
	"\n# restore dump level $level\n",
	"ask_for_tape $dev $bs $tlabel $tid;\n",
	"mt -f $dev datcompression $hwc;\n",
	"mt -f $dev asf $tidx;\n",
	"check_dumplabel $dev $bs $did;\n",
	"mt -f $dev asf $tidx;\n",
	"f_restore $dev $bs $dfmt $did $zip;\n",
	"mt -f $dev rewind\n";
    }
  } 				# end of (defined $bootpart)


  # -------------------------------------------------------------------------------------------------------------
    
  $fh->open(">$tmpdir/restore_nonroot.sh") 
    || die "cannot open $tmpdir/restore_nonroot.sh: $!";

  print $fh join("\n",
		 '#!/bin/sh',
		 '. functions.sh',
		 'myself=`echo $0 | sed "s@.*/@@"`;',
		 'mydir=`pwd`;',
		 'mkdir -p mnt',
         'umount -a >/dev/null 2>&1',
         'rwmount;',
		 '');
    my $raid = "0";
    my $raidf = "2";                                                                        # Merker für RAID Failover
    my $raidpoint ="";                                                                      # Merker für Mountpoint
    
    foreach my $d (sort keys %nonroot) {
    my $p    = $nonroot{$d}->{part};
    my $fs   = $nonroot{$d}->{fs};

    my $raus = "0";                                                                       
    
    # Partitionen durchlaufen ...., wir merken uns RAID für später !
    if ($p=~/\/dev\/md[0-9]{1,2}/) {                                                       # RAID vorhanden ?
        $raid="1"; $raus="1"; 
        $raidf=system("which nfs-failover-init >/dev/null 2>&1");                          # nfs-failover-init auch vorhanden ?(0/255)
        $raidpoint=$d;                                                                     # merke Mountpoint...
    }
    next if "$raus" == "1";                                                                # nächster Wert, wenn Raid gefunden,
                                                                                           # wollen wir hier nix machen...
    print $fh
      "if yesno \\\n",
      "  \"Do you want to write a new filesystem on $p (was $d)?\" \"n\";\n",
      "then\n";
  SWITCH: for($fs) {
    /ext2/ and do { print $fh "mke2fs $p\n"; last; };
    /ext3/ and do { print $fh "mke2fs -j $p\n"; last; };
    /xfs/  and do { print $fh "mkfs.xfs -f $p\n"; last; };
    print $fh "mkfs.$fs $p\n"; last;
  }
    print $fh "fi\n\n";
  }

  do {
    my %h = hist_lookup({ directory => '/.+' });
    foreach my $did (keys %h) {
      $nonrootdir{hist_get_directory($did)}++;
    }
  };
  
  foreach my $dir (reverse sort keys %nonrootdir) {
      if ($dir eq $raidpoint) {
        if ($raid == "1") {
          if ( $raidf == "0") {
              print $fh
              "which nfs-failover-init >/dev/null 2>&1 && nfs-failover-init \n";
          }
          else 
          {
              print $fh
              "raidstart \n";
          }
        }
      }
              
      
      print $fh 
      "\nif yesno \"Do you want to restore $dir?\" n;\n",
      "then\n",
      " yesno_exec \"Do you want to mount $dir?\" n mount $dir\n",
      " cd $dir;\n",
      " test -e lost+found && rm -rf lost+found/ \n"; 
    foreach my $did (hist_get_restorelist($dir, time())) {
      my $tlabel = hist_get_tapelabel($did);
      my $tid    = hist_get_tapeid($did);
      my $tidx   = hist_get_tapeidx($did);
      my $level  = hist_get_dumplevel($did);
      my $dopts  = hist_get_options($did);
      my $bs     = do { $dopts =~ /\b\d+[kMG]?\b/; $&; };
      $bs        = convert($bs);
      my $zip    = do { $dopts =~ /\b(gzip|bzip2|z)\b/; $&; };
      my $hwc    = do { $dopts =~ /\bhw\b/ ? 1 : 0 ; };
      my $dfmt   = do { $dopts =~ /^\w+/; $&; };
      $zip = '' unless $zip;
      
      print $fh 
	"#  restore dump level $level\n",
	" ask_for_tape $dev $bs $tlabel $tid;\n",
	" mt -f $dev datcompression $hwc;\n",
	" mt -f $dev asf $tidx;\n",
	" check_dumplabel $dev $bs $did;\n",
	" mt -f $dev asf $tidx;\n",
	" f_restore $dev $bs $dfmt $did $zip;\n";
    }
    print $fh 
      " cd \$mydir;\n", 
      " yesno_exec \"Do you want to umount $dir?\" n umount $dir\n",
      "fi\n";
  }

# alle Partitionen abgearbeitet ...
# nun kopieren wir die HISTORY.TXT nach /var/lib/unidump 
# zum Abschluss nochmal lilo, falls der Anwender /boot erneut restauriert hat
  print $fh
      "mount -a \n",
      "rwmount \n",
      "cp history.txt /var/lib/unidump/ && echo \"restaurierte History zrückkopiert.\" \n",
      "lilo\n";
      
# --------------------------------------------------------

  if(@swappart) {
    $fh->open(">$tmpdir/restore_swap.sh") 
      || die "cannot open $tmpdir/mk_swap.sh: $!";
    print $fh "#!/bin/sh\n. functions.sh\n\n";
    foreach my $sp (@swappart) {
      print $fh 
	"if yesno \\\n",
	"  \"Do you want to create a swap partition on $sp?\" \"n\";\n",
	"then mkswap $sp\nfi\n\n";
    }
  }

  if(%nonrootdisk) {
    $fh->open(">$tmpdir/part_nonroot.sh") 
      || die "cannot open $tmpdir/part_nonroot.sh: $!";
    print $fh "#!/bin/sh\n. functions.sh\n\n";
    foreach my $d (keys %nonrootdisk) {
      print $fh 
	"if yesno \\\n",
	"  \"Do you want to write a new partition table on disk $d?\" \"n\";\n",
	"then part_disk $d\nfi\n\n";
    }
    foreach my $d (keys %nonrootdisk) {
      my $dd  = do { $d =~ m@[^/]+$@; $&; };
      system("sfdisk -d $d | grep -E -e '^(unit|/dev|\$)' > $tmpdir/$dd.ptable")
	&& die "cannot write partition table to $tmpdir/$dd.ptable: $!";
    }
  }

#    if(%nonroot) {
#      $fh->open(">$tmpdir/restore_nonroot.sh") 
#        || die "cannot open $tmpdir/restore_nonroot.sh: $!";
#      print $fh 
#        "#!/bin/sh\n",
#        ". functions.sh\n\n",
#        "mkdir -p mnt\n";
#      foreach my $d (keys %nonroot) {
#        my $p  = $nonroot{$d}->{part};
#        my $fs = $nonroot{$d}->{fs};
#        print $fh
#  	"if yesno \\\n",
#  	"  \"Do you want to write a new filesystem on partition $p (was $d)?\" \"n\";\n",
#  	"then\n";
#      SWITCH: for($fs) {
#        /ext2/ and do { print $fh "mke2fs $p\n"; last; };
#        /ext3/ and do { print $fh "mke2fs -j $p\n"; last; };
#        /xfs/  and do { print $fh "mkfs.xfs $p\n"; last; };
#        print $fh "mkfs.$fs $p\n"; last;
#      }
#        print $fh "fi\n\n";
#      }
#      print $fh "sh nonrootfs.restore.sh\n";
#    }


  $fh->open(">$tmpdir/restore_lvm.sh") 
    || die "cannot open $tmpdir/restore_lvm.sh: $!";
  my ($vgname, %vg);
  %vg = hist_lvmstruct();
  foreach $vgname (keys %vg) {

    my($pesize, $pvname, $i, $lvname, $lvsize);

    $pesize = $vg{$vgname}->{pesize};
    
    foreach $pvname (@{$vg{$vgname}->{pvname}}) {
      print $fh "pvcreate $pvname\n";
    }

    print $fh "[ -c /dev/$vgname/group ] && rm -r /dev/$vgname\n"; 
    print $fh "vgcreate -s $pesize $vgname @{$vg{$vgname}->{pvname}}\n";
  
    for ($i=0; $i< scalar @{$vg{$vgname}->{lvname}}; $i++) {
      $lvname = do { @{$@{$vg{$vgname}->{lvname}}->[$i] =~ m@[^/]+$@; $&; } };
      $lvsize = @{$@{$vg{$vgname}->{lvsize}}->[$i]};
      print $fh "lvcreate -L $lvsize -n $lvname $vgname\n";
    }
  }

  chmod 0755, <$tmpdir/*.sh>;
  my $cmdline = "$tar -c -C $tmpdir -f $dev .";
  logmessage("DUMP[history_save]: $cmdline");
  logmessage_debug("running cmd: $cmdline");
  system("$cmdline"); 
  logmessage_debug("cmd retcode: $?");
  my ($rc, $mesg) = ($?/256, $!);
  if($rc) {
    logmessage("DUMP[history_save]: ERROR ($mesg)");
  } else {
    logmessage("DUMP[history_save]: DONE");
    unlink <$tmpdir/*>;
    rmdir $tmpdir;
  }

  return wantarray ? ($rc, $mesg) : $rc;
}

sub hist_lvmstruct {
  logmessage_debug("History::hist_lvm_struct: "); 
  -f "/etc/lvmtab" or return;	# return if no lvm in use
  open(P, "vgdisplay -v |") or return; # return if no lvm tools
  my($mode, $vgname, $lvname, $lvsize, $pvname, $pesize);
  my %vg = ();

  while(<P>) {
    chomp;
    s/^\s+//;
    s/\s+$//;
    
    /^-/ and undef($mode);

    /^-+\s*volume group/i    and do {
      $mode = "vg";
      undef($vgname);
      undef($lvname);
      undef($lvsize);
      undef($pvname);
      undef($pesize);
    };

    /^-+\s*logical volume/i  and $mode = "lv";
    /^-+\s*physical volume/i and $mode = "pv";

    /^VG Name\s*/i and $vgname = $';
    /^PE Size\s+(\S+)\s+(\S*)/i and do {
      $pesize = int($1);
      my $u = $2;
      $pesize .= "k" if ($u =~ /^k/i);
      $pesize .= "m" if ($u =~ /^m/i);
      $pesize .= "g" if ($u =~ /^g/i);
      $pesize .= "t" if ($u =~ /^t/i);
    };

    /^LV Name\s*/i and $lvname = $';
    /^LV Size\s+(\S+)\s+(\S*)/i and do {
      $lvsize = int($1);
      my $u = $2;
      $lvsize .= "k" if ($u =~ /^k/i);
      $lvsize .= "m" if ($u =~ /^m/i);
      $lvsize .= "g" if ($u =~ /^g/i);
      $lvsize .= "t" if ($u =~ /^t/i);
    };

    /^PV Name \(\#\)\s*(\S+)/i and $pvname = $1;  
  
    next unless $mode;
  
    /^\s*$/ and do {		# blank line marks end of a block

    SWITCH: {

      ($mode eq "vg") and do {
	$vg{$vgname} = { 'lvname' => [],
			 'lvsize' => [], 
			 'pvname' => [],
			 'pesize' => $pesize }; 
      };

      ($mode eq "lv") and do {
	#$vg{$vgname}->{lvname} = [@{$vg{$vgname}->{lvname}}, $lvname];
	#$vg{$vgname}->{lvsize} = [@{$vg{$vgname}->{lvsize}}, $lvsize];
	push(@{$vg{$vgname}->{lvname}}, $lvname);
	push(@{$vg{$vgname}->{lvsize}}, $lvsize);
      };

      ($mode eq "pv") and do {
	#$vg{$vgname}->{pvname} = [@{$vg{$vgname}->{pvname}}, $pvname];
	push(@{$vg{$vgname}->{pvname}}, $pvname);
      };
      
    }

      undef($mode);
    };
  }
  return %vg;
}



1;

__END__

=head1 NAME

  History -- UNIDUMP module to handle history file

=head1 SYNOPSIS
  
  use Unidump::History qw(:all);

=head1 DESCRIPTION
 
 This module deals with the UNIDUMP history-file. The file lives in 
 $historydir/history.txt (see Variables below). The module holds a
 copy of the historyfile in memory.

=head2 Methods

=over 2

=item  hist_insert

 hist_insert({dumpid => $did,
	       directory => $dir,
	       dumplevel => $level,
	       tapelabel => $tlabel,
	       tapeidx => $tidx,
	       tapeid => $tid,
	       starttime => $unixtime,
	       options => $opts});
  hist_insert($did, $dir, $level, $tlabel, $tidx,
	      $tid, $unixtime, $opts);
	       
 Inserts a history entry. After inserting the in-memory
 history will be synced to disk.
 
=item hist_get

 @list_of_all_dumpids = hist_get();
  ($dir, $level, $tlabel, $tidx, $tid, $unixtime, $opts)
     = hist_get($dumpid);
  
  Without an argument retrieve a list of all history entries.
  With one dumpid as argument, retrieve that history entry as list in
  array context or as whitespace joined list in scalar context.

=item hist_get_*

      hist_get_directory($dumpid);
      hist_get_dumplevel($dumpid);
      hist_get_tapelabel($dumpid);
      hist_get_tapeidx($dumpid);
      hist_get_tapeid($dumpid);
      hist_get_starttime($dumpid);
      hist_get_options($dumpid);
      
      Retrieve the corresponding part of the history entry.
      

=item hist_delete

  hist_delete(@list_of_dumpids);
  
  Remove entries from history but only if the dump is obsolete.

=item hist_write

      hist_write;
      
      Sync the in-memory copy of history on disk. This is mainly for
      internal use, but you might do it by yourself. hist_write is
      called internally after every hist_insert.

=item hist_read
      
      hist_read;
      
      Read the history file from disk into memory. This is mainly for
      internal use, but you might do it by yourself.
	
=item hist_lookup
      
      %hash = hist_lookup({
	          dumpid => $did,
	          directory => $dir,
		  dumplevel => $level,
		  tapelabel => $tlabel,
		  tapeidx => $tidx,
		  tapeid => $tid,
		  starttime => $unixtime,
		  before => $unixtime,
		  after => $unixtime});

      Retrieve a hash of matching dumps. Everything is optional
      here. Everything thas is specified is interpreted as regular
      expression that is matched as /^$your_expr_here$/ against the
      history entries. 

=item hist_get_parent

      @parent = hist_get_parent({directory => $dir, 
                                 dumplevel => $level, 
                                 starttime => $unixtime});
      @parent = hist_get_parent($dir, $level, $unixtime);
	
      Fetch the parent of a dump. That is the last dump of the same
      directory $dir but with a lower level than $level and older than
      $unixtime. Note, that it is not necessary that either dump
      actually exist. You might test for a parent of a non-existing dump
      (e.g. what would be the parent if I'd perform a dump now?). It
      is even not guaranteed that the returned parent still
      exist. Test this with B<hist_dump_exit>. 
      B<hist_get_parent> returns the dumpid in scalar context or the
      complete list  ($dir, $level, $tlabel, $tidx, $tid, $unixtime,
      $opts) in array context. 

=item hist_get_ancestors

      @dumpid_list = hist_get_ancestors($dumpid);

      Fetch the full list of ancestors of the given dump. Think of a
      recursive B<hist_get_parent>. 

=item hist_get_descendants

      @dumpid_list = hist_get_descendants($dumpid);

      Fetch all ever made descendants of $dumpid. They might be
      overwritten or they might still exist. Test with B<hist_dump_exit>. 

=item hist_get_restorelist

      @dumpid_list = hist_get_restorelist($dir, $unixtime);
      @dumpid_list = hist_get_restorelist({
				directory => $dir,
				starttime => $unixtime});

      Fetch a list of dumps to restore the data of the given time. The
      list contains only dumps that still exist (according to history;
      at least they are not overwritten by unidump).
      
=item hist_history_save

      hist_history_save($tar, $device);
      
      Create a tar-archiv of the historyfile and write it to the given
      device. This is used to backup the historyfile.

=back
 
=head2 Variables

=over 2

=item $historydir 

      default = "/var/lib/unidump"

=back


  
