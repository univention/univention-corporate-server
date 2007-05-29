# 	$Id: Tapelib.pm,v 1.2 2003/09/08 07:14:37 thorsten Exp $	
package Unidump::Tapelib;
use strict;
use Fcntl;
#use GDBM_File;
use Unidump::Logger qw(logmessage logmessage_debug);
use vars qw(@ISA @EXPORT @EXPORT_OK %EXPORT_TAGS $VERSION);
use Exporter;
$VERSION = do{ qq$Revision: 1.2 $ =~ /\d+\.\d+/, $&; };
@ISA = qw(Exporter);

@EXPORT = qw();
@EXPORT_OK = qw(tapelib_insert tapelib_get tapelib_get_tapelabel 
		tapelib_get_tapeid tapelib_get_tapecycle
		tapelib_set_tapelabel tapelib_set_tapecycle
		tapelib_lookup);
%EXPORT_TAGS = (all => [@EXPORT_OK]);

use vars qw($tapelibdir);

$tapelibdir = "/var/lib/unidump";
my %tapelib;

sub LOCK_SH { 1 }
sub LOCK_EX { 2 }
sub LOCK_NB { 4 }
sub LOCK_UN { 8 }


sub tapelibfile {
  $tapelibdir =~ s@/$@@;
  system("touch", "$tapelibdir/tapelib.txt") 
    unless(-f "$tapelibdir/tapelib.txt");
  return "$tapelibdir/tapelib.txt";
}

sub tapelib_insert {
  logmessage_debug("Tapelib::tapelib_insert: @_");
  my ($tapeid, $tapelabel, $tapecycle);
  if(ref($_[0]) =~ /HASH/) {
    ($tapeid, $tapelabel, $tapecycle) = 
      ($_[0]->{tapeid}, $_[0]->{tapelabel}, $_[0]->{tapecycle});
  } else {
    ($tapeid, $tapelabel, $tapecycle) = @_;
  }
  tapelib_read();
  $tapelib{$tapeid} = "$tapelabel $tapecycle";
  tapelib_write();
}

sub tapelib_write {
  logmessage_debug("Tapelib::tapelib_write:");
  my $tapelibfile = tapelibfile();
  unless(%tapelib) {
    logmessage("I won't write an empty tapelib file!");
    return;
  }
  unless(rename("$tapelibfile", "$tapelibfile.bak")) {
    logmessage("cannot rename file: $!");
    return;
  }
  local(*FH);
  unless(open (FH, "> $tapelibfile")) {
    logmessage("file not writable: $tapelibfile: $!");
    rename("$tapelibfile.bak", "$tapelibfile");
    return;
  }
  unless(flock(FH, LOCK_EX|LOCK_NB)) {
    logmessage("waiting to get exclusive lock on file ...");
    unless(flock(FH, LOCK_EX)) {
      logmessage("cannot get exclusive lock on file: $!");
      rename("$tapelibfile.bak", "$tapelibfile");
      return;
    }
  }
  my $i;
  while(my($k,$v) = each %tapelib) {
    print FH "$k $v\n" and $i++;
  }
  close(FH);
  return $i;
}

sub tapelib_read {
  logmessage_debug("Tapelib::tapelib_read:");
  my $tapelibfile = tapelibfile();
  local(*FH);
  unless(open (FH, "$tapelibfile")) {
    logmessage("file not readable: $tapelibfile: $!");
    return;
  }
  unless(flock(FH, LOCK_SH|LOCK_NB)) {
    logmessage("waiting to get shared lock on file ...");
    unless(flock(FH, LOCK_SH)) {
      logmessage("cannot get shared lock on file: $!");
      return;
    }
  }
  %tapelib = ();		# empty tapelib hash
  while(<FH>) {			# read tapelibfile line-by-line
    chomp;
    /^\s*$/ and next;		# skip blank lines
    my($k, $v) = split(' ', $_, 2);
    $tapelib{$k} = $v;
  }
  close(FH);
}

sub tapelib_get {
  logmessage_debug("Tapelib::tapelib_get: @_");
  my ($tapeid) = @_;
  my ($res, %res);
  tapelib_read unless %tapelib;
  if($tapeid) {
    $res = $tapelib{$tapeid};
  } else {
    %res = %tapelib;
  }
  if($tapeid) {
    return wantarray ? split(' ', $res) : $res;
  } else {
    return %res;
  }
}

sub tapelib_get_tapelabel { return (tapelib_get(@_))[0] if @_; }
sub tapelib_get_tapecycle { return (tapelib_get(@_))[1] if @_; }

sub tapelib_lookup {
  logmessage_debug("Tapelib::tapelib_lookup: @_");
  my ($tapeid, $tapelabel, $tapecycle);
  if(ref($_[0]) =~ /HASH/) {
    ($tapeid, $tapelabel, $tapecycle) = 
      ($_[0]->{tapeid}, $_[0]->{tapelabel}, $_[0]->{tapecycle});
  } else {
    ($tapeid, $tapelabel, $tapecycle) = @_;
  }
  
  my ($k, $v, %res, %h);
  %h = tapelib_get();
  while (($k, $v) = each %h) {
    my @l = split(' ', $v);
    $k    =~ /^$tapeid$/ and $res{$k} = $v, next;
    $l[0] =~ /^$tapelabel$/ and $res{$k} = $v, next;
    $l[1] =~ /^$tapecycle$/ and $res{$k} = $v, next;
  }
  return %res;
}

sub tapelib_set_tapecycle {
  logmessage_debug("Tapelib::tapelib_set_tapecycle: @_");
  my ($tapeid, $tapecycle) = @_;
  if($tapeid) {
    my $tapelabel = tapelib_get_tapelabel($tapeid);
    tapelib_insert($tapeid, $tapelabel, $tapecycle);
  }
}

sub tapelib_set_tapelabel {
  logmessage_debug("Tapelib::tapelib_set_tapelabel: @_");
  my ($tapeid, $tapelabel) = @_;
  if($tapeid) {
    my $tapecycle = tapelib_get_tapecycle($tapeid);
    tapelib_insert($tapeid, $tapelabel, $tapecycle);
  }
}


1;

__END__

 
