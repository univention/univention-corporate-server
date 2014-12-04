#!/usr/bin/perl -w
#
# make_disc_trees
#
# From the list of packages we have, lay out the CD trees

use strict;
use Digest::MD5;
use Digest::SHA;
use File::stat;
use File::Find;
use File::Basename;
use Compress::Zlib;

my %pkginfo;
my ($basedir, $mirror, $tdir, $codename, $archlist, $mkisofs, $maxcds,
    $maxisos, $maxjigdos, $extranonfree, $nonfree, $contrib, $use_local);
my $mkisofs_base_opts = "";
my $mkisofs_opts = "";
my $mkisofs_dirs = "";
my (@arches, @arches_nosrc, @overflowlist, @pkgs_added);
my (@exclude_packages, @unexclude_packages, @excluded_package_list);
my %firmware_package;
my $current_checksum_type = "";
my %descriptions;

undef @pkgs_added;
undef @exclude_packages;
undef @unexclude_packages;
undef @excluded_package_list;

$basedir = shift;
$mirror = shift;
$tdir = shift;
$codename = shift;
$archlist = shift;
$mkisofs = shift;
$mkisofs_base_opts = shift;

require "$basedir/tools/link.pl";

my $iso_blksize = 2048;
my $log_opened = 0;
my $old_split = $/;
my $security = read_env('SECURITY', $mirror);
my $localdebs = read_env('LOCALDEBS', $mirror);
my $symlink_farm = read_env('SYMLINK', 0);
my $link_verbose = read_env('VERBOSE', 0);
my $link_copy = read_env('COPYLINK', 0);

# MAXCDS is the hard limit on the MAXIMUM number of images to
# make. MAXJIGDOS and MAXISOS can only make this number smaller; we
# will use the higher of those 2 numbers as the last image to go to,
# if they're set
$maxcds = read_env('MAXCDS', 9999);

$maxisos = read_env('MAXISOS', 9999);
if ($maxisos =~ 'ALL' || $maxisos =~ 'all') {
    $maxisos = 9999;
}

$maxjigdos = read_env('MAXJIGDOS', 9999);
if ($maxjigdos =~ 'ALL' || $maxjigdos =~ 'all') {
    $maxjigdos = 9999;
}

if ($maxisos > $maxjigdos) {
    $maxjigdos = $maxisos;
}

if ($maxjigdos > $maxisos) {
    $maxisos = $maxjigdos;
}

if ($maxisos < $maxcds) {
    $maxcds = $maxisos;
}

$extranonfree = read_env('EXTRANONFREE', 0);
$nonfree = read_env('NONFREE', 0);
$contrib = read_env('CONTRIB', 0);
$use_local = read_env('LOCAL', 0);
	
my $list = "$tdir/list";
my $bdir = "$tdir/$codename";
my $log = "$bdir/make_disc_tree.log";
open(LOG, ">> $log") or die ("Can't open logfile $log for writing: $!\n");

# Print out the details of genisoimage/xorriso etc.
my $mkisofs_version = `$mkisofs -version`;
print "$mkisofs -version says:\n$mkisofs_version\n";
print LOG "$mkisofs -version says:\n$mkisofs_version\n";

foreach my $arch (split(' ', $archlist)) {
	push(@arches, $arch);
	if (! ($arch eq "source")) {
		push(@arches_nosrc, $arch);
	}
    # Pre-cache all the package information that we need
    load_packages_cache($arch);
}

if (! ($archlist eq "source")) {
    load_descriptions("main");
    if ($contrib) {
        load_descriptions("contrib");
    }
    if ($nonfree || $extranonfree) {
        load_descriptions("non-free");
    }
    if ($use_local) {
        load_descriptions("local");
    }
}

my $disknum = 1;
my $max_done = 0;
my $size_check = "";

# Constants used for space calculations
my $MiB = 1048576;
my $MB = 1000000;
my $GB = 1000000000;
my $blocksize = 2048;
my ($maxdiskblocks, $diskdesc);
my $cddir;

my $disktype = $ENV{'DISKTYPE'};
my $size_swap_check;
my $hfs_extra = 0;
my $hfs_mult = 1;

# And count how many packages added since the last size check was done
# - the estimation code is getting very accurate, so let's reduce the
# number of times we fork mkisofs
my $count_since_last_check = 0;
my $size_check_period = 10;

my $pkgs_this_cd = 0;
my $pkgs_done = 0;
my $size = 0;
my $guess_size = 0;
my @overflowpkg;
my $mkisofs_check = "$mkisofs $mkisofs_base_opts -r -print-size -quiet";
my $debootstrap_script = read_env('DEBOOTSTRAP_SCRIPT', "");

chdir $bdir;

# Size calculation is slightly complicated:
#
# 1. At the start, ask mkisofs for a size so far (including all the
#    stuff in the initial tree like docs and boot stuff
#
# 2. After that, add_packages will tell us the sizes of the files it
#    has added. This will not include directories / metadata so is
#    only a rough guess, but it's a _cheap_ guess
#
# 3. Once we get >90% of the max size we've been configured with,
#    start asking mkisofs after each package addition. This will
#    be slow, but we want to be exact at the end

$cddir = "$bdir/CD$disknum";
get_disc_size();
# Space calculation for extra HFS crap
if ($archlist =~ /m68k/ || $archlist =~ /powerpc/) {
    $hfs_mult = 1.2;
    $hfs_extra = int($maxdiskblocks * 8 / $blocksize);
    print LOG "arches require HFS hybrid, multiplying sizes by $hfs_mult and marking $hfs_extra blocks for HFS use\n";
}

print "Starting to lay out packages into images:\n";

if (-e "$bdir/firmware-packages") {
    open(FWLIST, "$bdir/firmware-packages") or die "Unable to read firmware-packages file!\n";
    while (defined (my $pkg = <FWLIST>)) {
        chomp $pkg;
        $firmware_package{$pkg} = 1;
    }
    close(FWLIST);
}

open(INLIST, "$bdir/packages") or die "No packages file!\n";
while (defined (my $pkg = <INLIST>)) {
    chomp $pkg;
    $cddir = "$bdir/CD$disknum";
    my $opt;
    if (! -d $cddir) {
        if ($disknum > $maxcds) {
            print LOG "Disk $disknum is beyond the configured MAXCDS of $maxcds; exiting now...\n";
            $max_done = 1;
            last;
        }
        print LOG "Starting new disc $disknum at " . `date` . "\n";
        start_disc();
        print LOG "  Specified size: $diskdesc, $maxdiskblocks 2K-blocks maximum\n";
        print "  Placing packages into image $disknum\n";
        if ( -e "$bdir/$disknum.mkisofs_opts" ) {
            open(OPTS, "<$bdir/$disknum.mkisofs_opts");
            while (defined($opt = <OPTS>)) {
                chomp $opt;
                $mkisofs_opts = "$mkisofs_opts $opt";
            }
            close(OPTS);
        } else {
            $mkisofs_opts = "";
        }
        if ($disknum <= $maxjigdos) {
            $mkisofs_opts = "$mkisofs_opts -jigdo-jigdo /dev/null";
            $mkisofs_opts = "$mkisofs_opts -jigdo-template /dev/null";
            $mkisofs_opts = "$mkisofs_opts -md5-list /dev/null";
            $mkisofs_opts = "$mkisofs_opts -o /dev/null";
        }
        if ( -e "$bdir/$disknum.mkisofs_dirs" ) {
            open(OPTS, "<$bdir/$disknum.mkisofs_dirs");
            while (defined($opt = <OPTS>)) {
                chomp $opt;
                $mkisofs_dirs = "$mkisofs_dirs $opt";
            }
            close(OPTS);
        } else {
            $mkisofs_dirs = "";
        }

        $size_check = "$mkisofs_check $mkisofs_opts $mkisofs_dirs";
        $size=`$size_check $cddir`;
        chomp $size;
        $size += $hfs_extra;
        print LOG "CD $disknum: size is $size before starting to add packages\n";

        $pkgs_this_cd = 0;

        # If we have some unexcludes for this disc and have already
        # previously excluded some packages, check now if the two
        # lists intersect and we should re-include some packages
        if (scalar @unexclude_packages && scalar @excluded_package_list) {
            foreach my $reinclude_pkg (@excluded_package_list) {
                my ($arch, $component, $pkgname, $pkgsize) = split /:/, $reinclude_pkg;
                foreach my $entry (@unexclude_packages) {
                    if (($pkgname =~ /^\Q$entry\E$/m)) {
                        print LOG "Re-including $reinclude_pkg due to match on \"\^$entry\$\"\n";
                        $guess_size = int($hfs_mult * add_packages($cddir, $reinclude_pkg));
                        $size += $guess_size;
                        print LOG "CD $disknum: GUESS_TOTAL is $size after adding $reinclude_pkg\n";
                        $pkgs_this_cd++;
                        $pkgs_done++;
                        push (@pkgs_added, $entry);
                    }
                }
            }
        }
        while (scalar @overflowlist) {
            my $overflowpkg = pop @overflowlist;
            print LOG "Adding a package that failed on the last disc: $overflowpkg\n";
            $guess_size = int($hfs_mult * add_packages($cddir, $overflowpkg));
            $size += $guess_size;
            print LOG "CD $disknum: GUESS_TOTAL is $size after adding $overflowpkg\n";
            $pkgs_this_cd++;
            $pkgs_done++;
            push (@pkgs_added, $overflowpkg);
        }
    } # end of creating new CD dir

    if (should_exclude_package($pkg)) {
        push(@excluded_package_list, $pkg);
    } elsif (should_start_extra_nonfree($pkg)) {
        print LOG "Starting on extra non-free CDs\n";
        finish_disc($cddir, "");
        # And reset, to start the next disc
        $size = 0;
        $disknum++;
        undef(@pkgs_added);
        # Put this package first on the next disc
        push (@overflowlist, $pkg);
    } else {
        $guess_size = int($hfs_mult * add_packages($cddir, $pkg));
        $size += $guess_size;
        push (@pkgs_added, $pkg);
        print LOG "CD $disknum: GUESS_TOTAL is $size after adding $pkg\n";
        if (($size > $maxdiskblocks) ||
            (($size > $size_swap_check) &&
             ($count_since_last_check > $size_check_period))) {
            $count_since_last_check = 0;
            # Recompress files as needed before the size check
            find (\&recompress, "$cddir/dists");
            print LOG "Running $size_check $cddir\n";
            $size = `$size_check $cddir`;
            chomp $size;
            print LOG "CD $disknum: Real current size is $size blocks after adding $pkg\n";
        }
        if ($size > $maxdiskblocks) {
            while ($size > $maxdiskblocks) {
                $pkg = pop(@pkgs_added);
                print LOG "CD $disknum over-full ($size > $maxdiskblocks). Rollback!\n";
                $guess_size = int($hfs_mult * add_packages("--rollback", $cddir, $pkg));
                # Recompress files as needed before the size check
                find (\&recompress, "$cddir/dists");
                $size=`$size_check $cddir`;
                chomp $size;
                print LOG "CD $disknum: Real current size is $size blocks after rolling back $pkg\n";
                # Put this package first on the next disc
                push (@overflowlist, $pkg);
            }
            # Special-case for source-only discs where we don't care
            # about the ordering. If we're doing a source-only build
            # and we've overflowed, allow us to carry on down the list
            # for a while to fill more space. Stop when we've skipped
            # 5 packages (arbitrary choice of number!) #613751
            if (!($archlist eq "source") or (scalar @overflowlist >= 5)) {
                finish_disc($cddir, "");
                # And reset, to start the next disc
                $size = 0;
                $disknum++;
                undef(@pkgs_added);
            } else {
                print LOG "SOURCE DISC: continuing on to see if anything else will fit, " . scalar @overflowlist . " packages on the overflow list at this point\n";
            }
        } else {
            $pkgs_this_cd++;
            $pkgs_done++;
            $count_since_last_check++;
        }	
    }
}
close(INLIST);

if ($max_done == 0) {
	finish_disc($cddir, " (not)");
}

print LOG "Finished: $pkgs_done packages placed\n";
print "Finished: $pkgs_done packages placed\n";
system("date >> $log");

close(LOG);

#############################################
#
#  Local helper functions
#
#############################################
# Load up information about all the packages
sub load_packages_cache {
    my $arch = shift;
    my @pkglist;
    my ($p);
    my $num_pkgs = 0;

    $ENV{'LC_ALL'} = 'C'; # Required since apt is now translated
    $ENV{'ARCH'} = $arch;

    open(INLIST, "$bdir/packages.$arch")
        or die "No packages file $bdir/packages.$arch for $arch!\n";

    while (defined (my $pkg = <INLIST>)) {
        chomp $pkg;
        my ($junk, $component, $pkgname, $pkgsize) = split /:/, $pkg;
        push @pkglist, $pkgname;
    }
    close INLIST;

    print "Reading in package information for $arch:\n";
    print LOG "Reading in package information for $arch:\n";

    $/ = ''; # Browse by paragraph
    while (@pkglist) {
        my (@pkg) = splice(@pkglist,0,200);
        if ($arch eq "source") {
            open (LIST, "$basedir/tools/apt-selection cache showsrc @pkg |")
                || die "Can't fork : $!\n";
        } else {
            open (LIST, "$basedir/tools/apt-selection cache show @pkg |")
                || die "Can't fork : $!\n";
        }
        while (defined($_ = <LIST>)) {
            m/^Package: (\S+)/m and $p = $1;
            push @{$pkginfo{$arch}{$p}}, $_;
            $num_pkgs++;
        }
        close LIST;
        print LOG "load_packages_cache: Read details of $num_pkgs packages for $arch\n";
    }
    $/ = $old_split; # Browse by line again
    print "  Done: Read details of $num_pkgs packages for $arch\n";
}

# Load all the translated descriptions we can find
sub load_descriptions {
    my $suite = shift;
    my $lang;
	my $dh;
    my ($p);
    my $num_total = 0;
    my $num_files = 0;
    my $dir = "$mirror/dists/$codename/$suite/i18n";
    if ($suite =~ /local/) {
        $dir = "$localdebs/dists/$codename/$suite/i18n";
    }
    my @files;

    if (-d $dir) {
        print "Reading in translated package descriptions for $suite:\n";
        print LOG "Reading in translated package descriptions for $suite:\n";
        opendir($dh, $dir) || die "can't opendir $dir: $!\n";
        @files = readdir($dh);
        $/ = ''; # Browse by paragraph
        foreach my $file (@files) {
            if ($file =~ /Translation-(.*).bz2/) {
                my $num_descs = 0;
                $lang = $1;
                open(BZ, "bzip2 -cd $dir/$file |") ||
                    die "can't open description file $dir/$file for reading: $!\n";
                $num_files++;
                print LOG "  Parsing $file\n";
                while (defined($_ = <BZ>)) {
                    m/^Package: (\S+)/m and $p = $1;
                    $descriptions{"$lang"}{$p}{"data"} = $_;
                    $descriptions{"$lang"}{$p}{"used"} = 0;
                    $num_descs++;
                    $num_total++;
                }
                close(BZ);
                print LOG "    $num_descs descriptions\n";
            }
        }
        $/ = $old_split; # Browse by line again
        print "  Done: read $num_total entries for $num_files languages\n";
        print LOG "  Done: read $num_total entries for $num_files languages\n";
    } else {
        print "WARNING: no translated descriptions found for $codename/$suite\n";
    }
}

sub should_start_extra_nonfree {
    my $pkg = shift;
    my ($arch, $component, $pkgname, $pkgsize) = split /:/, $pkg;

	if ( ($component eq "non-free") && $extranonfree) {
		$extranonfree = 0; # Flag that we don't need to start new next time!
		return 1;
	}
	
	return 0;
}

sub should_exclude_package {
    my $pkg = shift;
    my ($arch, $component, $pkgname, $pkgsize) = split /:/, $pkg;
    my $should_exclude = 0;

    foreach my $entry (@exclude_packages) {
	if (($pkgname =~ /^\Q$entry\E$/m)) {
            print LOG "Excluding $pkg due to match on \"\^$entry\$\"\n";
            $should_exclude++;
        }
    }

    if ($should_exclude) {
        # Double-check that we're not being asked to include *and*
        # exclude the package at the same time. If so, complain and
        # bail out
        foreach my $entry (@unexclude_packages) {
            if (($pkgname =~ /^\Q$entry\E$/m)) {
                print LOG "But ALSO asked to unexclude $pkg due to match on \"\^$entry\$\"\n";
                print LOG "Make your mind up! Bailing out...\n";
                die "Incompatible exclude/unexclude entries for $pkg...\n";
            }
        }
        return 1;
    }
    return 0;
}

sub check_base_installable {
	my $arch = shift;
	my $cddir = shift;
	my $ok = 0;
	my (%on_disc, %exclude);
	my $packages_file = "$cddir/dists/$codename/main/binary-$arch/Packages";
	my $p;
	my $db_error = 0;
	my $error_string = "";

	open (PLIST, $packages_file)
		|| die "Can't open Packages file $packages_file : $!\n";
	while (defined($p = <PLIST>)) {
		chomp $p;
		$p =~ m/^Package: (\S+)/ and $on_disc{$1} = $1;
	}
	close PLIST;

	$packages_file = "$cddir/dists/$codename/local/binary-$arch/Packages";
	if (open (PLIST, $packages_file)) {
		while (defined($p = <PLIST>)) {
			chomp $p;
			$p =~ m/^Package: (\S+)/ and $on_disc{$1} = $1;
		}
		close PLIST;
	}

	if (defined($ENV{'BASE_EXCLUDE'})) {
		open (ELIST, $ENV{'BASE_EXCLUDE'})
			|| die "Can't open base_exclude file $ENV{'BASE_EXCLUDE'} : $!\n";
		while (defined($p = <ELIST>)) {
			chomp $p;
			$exclude{$p} = $p;
		}
		close ELIST;
	}
		
	open (DLIST, "debootstrap --arch $arch --print-debs $codename $tdir/debootstrap_tmp file:$mirror $debootstrap_script 2>/dev/null | tr ' ' '\n' |")
		 || die "Can't fork debootstrap : $!\n";
	while (defined($p = <DLIST>)) {
        if ($p =~ m/^E:/) {
            $db_error = 1;
        }
		chomp $p;
        if ($db_error) {
            $error_string = "$error_string $p";
        } else {
            if (length $p > 1) {
                if (!defined($on_disc{$p})) {
                    if (defined($exclude{$p})) {
                        print LOG "Missing debootstrap-required $p but included in $ENV{'BASE_EXCLUDE'}\n";
                    } else {
                        $ok++;
                        print LOG "Missing debootstrap-required $p\n";
                    }
                }
            }
        }
    }
    close DLIST;
    if ($db_error) {
        print LOG "Debootstrap reported error: $error_string\n";
        die "Debootstrap reported error: $error_string\n";
    }
	system("rm -rf $tdir/debootstrap_tmp");
	return $ok;
}

# If missing, create an empty local Packages file for an architecture.
# Only create an uncompressed Packages file; the call to recompress will
# create the compressed version.
sub add_missing_Packages {
	my ($filename);

	$filename = $File::Find::name;

	if ((-d "$_") && ($filename =~ m/\/main\/binary-[^\/]*$/)) {
		if ((-f "$_/Packages") && (! -d "../local/$_/")) {
			mkdir "../local/$_/" || die "Error creating directory local/$_: $!\n";
			open(LPFILE, ">../local/$_/Packages") or die "Error creating local/$_/Packages: $!\n";
			close LPFILE;
			print "  Created empty Packages file for local/$_\n";
		}
	}
}

sub checksum_file {
	my $filename = shift;
	my $alg = shift;
	my ($checksum, $st);

	open(CHECKFILE, $filename) or die "Can't open '$filename': $!\n";
	binmode(CHECKFILE);
	if ($alg eq "md5") {
	    $checksum = Digest::MD5->new->addfile(*CHECKFILE)->hexdigest;
	} elsif ($alg =~ /^sha\d+$/) {
	    $checksum = Digest::SHA->new($alg)->addfile(*CHECKFILE)->hexdigest;
	} else {
	    die "checksum_file: unknown alorithm $alg!\n";
	}
	close(CHECKFILE);
	$st = stat($filename) || die "Stat error on '$filename': $!\n";
	return ($checksum, $st->size);
}

sub recompress {
	# Recompress various files
	my ($filename);

	$filename = $File::Find::name;

    # Packages and Sources files; workaround for bug #402482
    if ($filename =~ m/\/.*\/(Packages|Sources)$/o) {
		system("gzip -9c < $_ >$_.gz");
	}
    # Translation files need to be compressed in .gz format on CD?
	if ($filename =~ m/\/.*\/i18n\/(Translation.*)$/o &&
        ! ($filename =~ m/\/.*\/i18n\/(Translation.*gz)$/o)) {
		system("gzip -9 $_");
	}
}	

sub find_and_checksum_files_for_release {
	my ($checksum, $size, $filename);

	$filename = $File::Find::name;

	if ($filename =~ m/\/.*\/(Packages|Sources|Release|Translation)/o) {
		$filename =~ s/^\.\///g;
		($checksum, $size) = checksum_file($_, $current_checksum_type);
		printf RELEASE " %s %8d %s\n", $checksum, $size, $filename;
	}
}	

sub checksum_files_for_release {
    # ICK: no way to pass arguments to the
    # find_and_checksum_files_for_release() function that I can see,
    # so using a global here...
	print RELEASE "MD5Sum:\n";
	$current_checksum_type = "md5";
	find (\&find_and_checksum_files_for_release, ".");
	print RELEASE "SHA1:\n";
	$current_checksum_type = "sha1";
	find (\&find_and_checksum_files_for_release, ".");
	print RELEASE "SHA256:\n";
	$current_checksum_type = "sha256";
	find (\&find_and_checksum_files_for_release, ".");
	print RELEASE "SHA512:\n";
	$current_checksum_type = "sha512";
	find (\&find_and_checksum_files_for_release, ".");
}    

sub md5_files_for_md5sum {
	my ($md5, $size, $filename);

	$filename = $File::Find::name;
	if (-f $_) {
		($md5, $size) = checksum_file($_, "md5");
		printf MD5LIST "%s  %s\n", $md5, $filename;
	}
}

sub get_disc_size {
    my $hook;
    my $error = 0;
    my $reserved = 0;
    my $chosen_disk = $disktype;
    my $disk_size_hack = "";

    if (defined($ENV{'RESERVED_BLOCKS_HOOK'})) {
        $hook = $ENV{'RESERVED_BLOCKS_HOOK'};
        print "  Calling reserved_blocks hook: $hook\n";
        $reserved = `$hook $tdir $mirror $disknum $cddir \"$archlist\"`;
		chomp $reserved;
		if ($reserved eq "") {
			$reserved = 0;
		}
        print "  Reserving $reserved blocks on CD $disknum\n";
    }

    # See if we've been asked to switch sizes for the whole set
    $disk_size_hack = read_env('FORCE_CD_SIZE', "");
    if ($disk_size_hack) {
       print LOG "HACK HACK HACK: FORCE_CD_SIZE found:\n";
       print LOG "  forcing use of a $disk_size_hack disk instead of $chosen_disk\n";
       $chosen_disk = $disk_size_hack;
    }

    # If we're asked to do a specific size for *this* disknum, over-ride again
    $disk_size_hack = read_env("FORCE_CD_SIZE$disknum", "");
    if ($disk_size_hack) {
       print LOG "HACK HACK HACK: FORCE_CD_SIZE$disknum found:\n";
       print LOG "  forcing use of a $disk_size_hack disk instead of $chosen_disk\n";
       $chosen_disk = $disk_size_hack;
    }

    # Calculate the maximum number of 2K blocks in the output images
    if ($chosen_disk eq "BC") {
        $maxdiskblocks = int(680 * $MB / $blocksize) - $reserved;
        $diskdesc = "businesscard";
    } elsif ($chosen_disk eq "NETINST") {
        $maxdiskblocks = int(680 * $MB / $blocksize) - $reserved;
        $diskdesc = "netinst";
    } elsif ($chosen_disk =~ /CD$/) {
        $maxdiskblocks = int(680 * $MB / $blocksize) - $reserved;
        $diskdesc = "650MiB CD";
    } elsif ($chosen_disk eq "CD700") {
        $maxdiskblocks = int(737 * $MB / $blocksize) - $reserved;
        $diskdesc = "700MiB CD";
    } elsif ($chosen_disk eq "DVD") {
        $maxdiskblocks = int(4700 * $MB / $blocksize) - $reserved;
        $diskdesc = "4.7GB DVD";
    } elsif ($chosen_disk eq "DLDVD") {
        $maxdiskblocks = int(8500 * $MB / $blocksize) - $reserved;
        $diskdesc = "8.5GB DVD";
    } elsif ($chosen_disk eq "BD") {
		# Useable capacity, found by checking some disks
        $maxdiskblocks = 11230000 - $reserved;
        $diskdesc = "25GB BD";
    } elsif ($chosen_disk eq "DLBD") {
		# Useable capacity, found by checking some disks
        $maxdiskblocks = 23652352 - $reserved;
        $diskdesc = "50GB DLBD";
    } elsif ($chosen_disk eq "STICK1GB") {
        $maxdiskblocks = int(1 * $GB / $blocksize) - $reserved;
        $diskdesc = "1GB STICK";
    } elsif ($chosen_disk eq "STICK2GB") {
        $maxdiskblocks = int(2 * $GB / $blocksize) - $reserved;
        $diskdesc = "2GB STICK";
    } elsif ($chosen_disk eq "STICK4GB") {
        $maxdiskblocks = int(4 * $GB / $blocksize) - $reserved;
        $diskdesc = "4GB STICK";
    } elsif ($chosen_disk eq "STICK8GB") {
        $maxdiskblocks = int(8 * $GB / $blocksize) - $reserved;
        $diskdesc = "8GB STICK";
    } elsif ($chosen_disk eq "CUSTOM") {
        $maxdiskblocks = $ENV{'CUSTOMSIZE'} - $reserved || 
            die "Need to specify a custom size for the CUSTOM disktype\n";
        $diskdesc = "User-supplied size";
    }

    $ENV{'MAXDISKBLOCKS'} = $maxdiskblocks;
    $ENV{'DISKDESC'} = $diskdesc;

    # How full should we let the disc get before we stop estimating and
    # start running mkisofs?
    $size_swap_check = $maxdiskblocks - (40 * $MB / $blocksize);
}

sub start_disc {
	my $error = 0;

	$error = system("$basedir/tools/start_new_disc $basedir $mirror $tdir $codename \"$archlist\" $disknum");
	if ($error != 0) {
		die "    Failed to start disc $disknum, error $error\n";
	}

	get_disc_size();

    print "Starting new \"$archlist\" $disktype $disknum at $basedir/$codename/CD$disknum\n";
    print "  Specified size for this image: $diskdesc, $maxdiskblocks 2K-blocks maximum\n";
	# Grab all the early stuff, apart from dirs that will change later
	print "  Starting the md5sum.txt file\n";
	chdir $cddir;
	system("find . -type f | grep -v -e ^\./\.disk -e ^\./dists | xargs md5sum >> md5sum.txt");
	chdir $bdir;

	$mkisofs_opts = "";
	$mkisofs_dirs = "";

    undef @exclude_packages;
    undef @unexclude_packages;

    if (defined ($ENV{"EXCLUDE"})) {
        my $excl_file = $ENV{"TASKDIR"} . "/" . $ENV{"EXCLUDE"};
        print LOG "Adding excludes from $excl_file\n";
        open (EXCLUDE_FILE, "< $excl_file") || die "Can't open exclude file $excl_file: $!\n";
        while (defined (my $excl_pkg = <EXCLUDE_FILE>)) {
            chomp $excl_pkg;
            push(@exclude_packages, $excl_pkg);
        }
        close (EXCLUDE_FILE);
    }
    if (defined ($ENV{"EXCLUDE$disknum"})) {
        my $excl_file = $ENV{"TASKDIR"} . "/" . $ENV{"EXCLUDE$disknum"};
        print LOG "Adding excludes from $excl_file\n";
        open (EXCLUDE_FILE, "< $excl_file") || die "Can't open exclude file $excl_file: $!\n";
        while (defined (my $excl_pkg = <EXCLUDE_FILE>)) {
            chomp $excl_pkg;
            push(@exclude_packages, $excl_pkg);
        }
        close (EXCLUDE_FILE);
    }
    if (defined ($ENV{"UNEXCLUDE$disknum"})) {
        my $excl_file = $ENV{"TASKDIR"} . "/" . $ENV{"UNEXCLUDE$disknum"};
        print LOG "Adding unexcludes from $excl_file\n";
        open (EXCLUDE_FILE, "< $excl_file") || die "Can't open unexclude file $excl_file: $!\n";
        while (defined (my $excl_pkg = <EXCLUDE_FILE>)) {
            chomp $excl_pkg;
            push(@unexclude_packages, $excl_pkg);
        }
        close (EXCLUDE_FILE);
    }
}

sub finish_disc {
	my $cddir = shift;
	my $not = shift;
	my $archok = 0;
	my $ok = 0;
	my $bytes = 0;
	my $ctx;
	my $hook;
	my $error = 0;

	if (defined($ENV{'DISC_FINISH_HOOK'})) {
		$hook = $ENV{'DISC_FINISH_HOOK'};
		print "  Calling disc_finish hook: $hook\n";
		$error = system("$hook $tdir $mirror $disknum $cddir \"$archlist\"");
		$error == 0 || die "DISC_FINISH_HOOK failed with error $error\n";
	}

	if (($disknum == 1) && !($archlist eq "source") && !($disktype eq "BC")) {
		foreach my $arch (@arches_nosrc) {
			print "  Checking base is installable for $arch\n";
			$archok = check_base_installable($arch, $cddir);
			if ($archok > 0) {
				print "    $arch is missing $archok files needed for debootstrap, look in $log for the list\n";
			}
			$ok += $archok;
		}
		if ($ok == 0) {
			system("touch $cddir/.disk/base_installable");
			print "  Found all files needed for debootstrap for all binary arches\n";
		} else {
			print "  $ok files missing for debootstrap, not creating base_installable\n";
			if ($disktype eq "BC") {
				print "  This is expected - building a BC\n";
			}
		}
	}

	chdir $cddir;

	# If we have a local packages directory, ensure we have a Packages file
	# for all included architectures as otherwise the Release file will be
	# invalid. This can happen if we do have local udebs but no local
	# regular packages, or multiple architectures with not all of them
	# having local packages.
	if (-d "./dists/$codename/local") {
		find (\&add_missing_Packages, "./dists/$codename/main/");
	}

	print "  Finishing off the Release file\n";
	chdir "dists/$codename";
	open(RELEASE, ">>Release") or die "Failed to open Release file: $!\n";
	find (\&recompress, ".");
	checksum_files_for_release();
	close(RELEASE);
	chdir("../..");

	print "  Finishing off md5sum.txt\n";
	# Just md5 the bits we won't have seen already
	open(MD5LIST, ">>md5sum.txt") or die "Failed to open md5sum.txt file: $!\n";
	find (\&md5_files_for_md5sum, ("./.disk", "./dists"));
	close(MD5LIST);

	# And sort; it should make things faster for people checking
	# the md5sums, as ISO9660 dirs are sorted alphabetically
	system("LANG=C sort -uk2 md5sum.txt | grep -v \./md5sum.txt > md5sum.txt.tmp");
	system("mv -f md5sum.txt.tmp md5sum.txt");
	chdir $bdir;

	if (defined($ENV{'DISC_END_HOOK'})) {
		$hook = $ENV{'DISC_END_HOOK'};
		print "  Calling disc_end hook: $hook\n";
		$error = system("$hook $tdir $mirror $disknum $cddir \"$archlist\"");
		$error == 0 || die "DISC_END_HOOK failed with error $error\n";
	}

	$size = `$size_check $cddir`;
	chomp $size;
	$bytes = $size * $blocksize;
	print LOG "CD $disknum$not filled with $pkgs_this_cd packages, $size blocks, $bytes bytes\n";
	print "  CD $disknum$not filled with $pkgs_this_cd packages, $size blocks, $bytes bytes\n";
	system("date >> $log");
}

# start of add_packages

sub msg_ap {
    my $level = shift;
    if (!$log_opened) {
        open(AP_LOG, ">> $tdir/$codename/add_packages.log")
            || die "Can't write in $tdir/add_packages.log!\n";
    }
    print AP_LOG @_;
}

sub size_in_blocks {
    my $size_in_bytes = shift;
    return (1 + int(($size_in_bytes + $iso_blksize - 1) / $iso_blksize));
}

# From a package name and section, work out the directory where its
# corresponding Packages file should live
sub Packages_dir {
    my $dir = shift;
    my $file = shift;
    my $section = shift;

    my ($pdir, $dist);

    if ($file =~ /\/main\//) {
        $dist = "main";
    } elsif ($file =~ /\/contrib\//) {
        $dist = "contrib";
    } elsif ($file =~ /\/non-free\//) {
        $dist = "non-free";
    } else {
        $dist = "local";
    }
    $dist = "main";

    $pdir = "$dir/dists/$codename/$dist";
    if ($section and $section eq "debian-installer") {
        $pdir = "$dir/dists/$codename/$dist/debian-installer";
    }
    return $pdir;
}

# Dump the apt-cached data into a Packages file; make the parent dir
# for the Packages file if necesssary
sub add_Packages_entry {
    my $dir = shift;
    my $arch = shift;
    my $_ = shift;
    my ($p, $file, $section, $pdir, $pkgfile, $gz, $st1, $st2, $size1, $size2);
    my $blocks_added = 0;
    my $old_blocks = 0;
    my $new_blocks = 0;

    m/^Package: (\S+)/m and $p = $1;
    m/^Section: (\S+)/m and $section = $1;

    if ($arch eq "source") {
        m/^Directory: (\S+)/mi and $file = $1;
        if (!defined($file)) {
            die "Can't parse source file information out of $_\n";
        }
        $pdir = Packages_dir($dir, $file, $section) . "/source";
        $pkgfile = "$pdir/Sources";
    } else {
        m/^Filename: (\S+)/mi and $file = $1;
        if (!defined($file)) {
            die "Can't parse binary file information out of $_\n";
        }
        $pdir = Packages_dir($dir, $file, $section) . "/binary-$arch";
        $pkgfile = "$pdir/Packages";

        $file =~ s,.*(/(?:amd64|i386|all)/[^/]+),$1,;
        s/^Filename: (\S+)/Filename: $file/im;
    }

    msg_ap(0, "  Adding $p to $pkgfile(.gz)\n");
    
    if (! -d $pdir) {
        system("mkdir -p $pdir");
        $blocks_added++;
    }	

    if (-e $pkgfile) {
        $st1 = stat("$pkgfile");
        $old_blocks = size_in_blocks($st1->size);
    }

    if (-e "$pkgfile.gz") {
        $st1 = stat("$pkgfile.gz");
        $old_blocks += size_in_blocks($st1->size);
    }

    open(PFILE, ">>$pkgfile");
    print PFILE $_;
    close(PFILE);

    $gz = gzopen("$pkgfile.gz", "ab9") or die "Failed to open $pkgfile.gz: $gzerrno\n";
    $gz->gzwrite($_) or die "Failed to write $pkgfile.gz: $gzerrno\n";
    $gz->gzclose();
    $st1 = stat("$pkgfile");
    $st2 = stat("$pkgfile.gz");
    $size1 = $st1->size;
    $size2 = $st2->size;

    $new_blocks += size_in_blocks($st1->size);
    $new_blocks += size_in_blocks($st2->size);
    $blocks_added += ($new_blocks - $old_blocks);
    msg_ap(0, "    now $size1 / $size2 bytes, $blocks_added blocks added\n");
    return $blocks_added;
}

# Write out translated description(s) for a package
sub add_trans_desc_entry {
    my $dir = shift;
    my $arch = shift;
    my $_ = shift;
    my ($p, $file, $section, $idir, $pkgfile, $gz, $st);
    my $size = 0;
    my $blocks_added = 0;
    my $old_blocks = 0;
    my $new_blocks = 0;

    m/^Package: (\S+)/m and $p = $1;
    m/^Section: (\S+)/m and $section = $1;

    m/^Filename: (\S+)/mi and $file = $1;
    $idir = Packages_dir($dir, $file, $section) . "/i18n";

    if (! -d $idir) {
        system("mkdir -p $idir");
        $blocks_added++;
    }	

    foreach my $lang (keys %descriptions) {
        # Do we have a translation for this language?
        if (defined $descriptions{$lang}{$p}{"data"}) {
            my $trans_file = "$idir/Translation-$lang";

            msg_ap(0, "  Adding $p to $trans_file(.gz)\n");

            if ($descriptions{$lang}{$p}{"used"}) {
                msg_ap(0, "    - not, already included\n");
            } else {
                # Keeping files in .gz format is far too expensive in
                # terms of de-compressing and re-compressing all the
                # time. Store uncompressed and only compress when we're
                # finished. Analysis of typical text suggests that gzip
                # will give roughly a factor of 2 compresssion here, so
                # use that estimate. For accuracy, we may end up
                # compressing *anyway* just before doing a size check; if
                # so, we'll need to uncompress again on entry here.

                if (-f "$trans_file.gz") {
                    system("gunzip $trans_file.gz");
                }

                if (-f $trans_file) {
                    $st = stat("$trans_file") || die "unable to stat $trans_file\n";
                    $old_blocks += size_in_blocks($st->size / 2);
                }

                # Add the new description
                open(IFILE, ">> $trans_file");
                print IFILE $descriptions{$lang}{$p}{"data"};
                $descriptions{$lang}{$p}{"used"} = 1;
                close(IFILE);

                $st = stat("$trans_file") || die "unable to stat $trans_file\n";
                $size += int($st->size / 2);
                $new_blocks += size_in_blocks($st->size / 2);
            }
        }
    }
    $blocks_added += ($new_blocks - $old_blocks);
    msg_ap(0, "    now $size bytes, $blocks_added blocks added\n");
    return $blocks_added;
}

sub add_md5_entry {
    my $dir = shift;
    my $arch = shift;
    my $_ = shift;
    my ($pdir, $file, $md5, $st, $size, $p);
    my $md5file = "$dir/md5sum.txt";
    my $blocks_added = 0;
    my $old_blocks = 0;
    my $new_blocks = 0;

    m/^Package: (\S+)/mi and $p = $1;

    if (-e $md5file) {
        $st = stat("$md5file");
        $old_blocks = size_in_blocks($st->size);
    }

    open(MD5FILE, ">>$md5file");

    if ($arch eq "source") {
        m/^Directory: (\S+)/mi and $pdir = $1;
	# Explicitly use the md5 lines in the Sources stanza, hence the xdigit(32) here
	while (/^ ([[:xdigit:]]{32}) (\d+) (\S+)/msg) { print MD5FILE "$1  ./$pdir/$3\n"; }
    } else {
        m/^Filename: (\S+)/m and $file = $1;
        m/^MD5sum: (\S+)/m and print MD5FILE "$1  ./$file\n";
    }

    close(MD5FILE);
    msg_ap(0, "  Adding $p to $md5file\n");
    $st = stat("$md5file");
    $size = $st->size;
    $new_blocks = size_in_blocks($st->size);
    $blocks_added = $new_blocks - $old_blocks;
    msg_ap(0, "    now $size bytes, added $blocks_added blocks\n");

    return $blocks_added;
}

# Roll back the results of add_Packages_entry()
sub remove_Packages_entry {
    my $dir = shift;
    my $arch = shift;
    my $_ = shift;
    my ($p, $file, $section, $pdir, $pkgfile, $tmp_pkgfile, $match, $gz,
        $st1, $st2, $size1, $size2);
    my $blocks_removed = 0;
    my $old_blocks = 0;
    my $new_blocks = 0;

    m/^Package: (\S+)/m and $p = $1;
    m/^Section: (\S+)/m and $section = $1;

    if ($arch eq "source") {
        m/^Directory: (\S+)/mi and $file = $1;
        $pdir = Packages_dir($dir, $file, $section) . "/source";
        $pkgfile = "$pdir/Sources";
    } else {
        m/^Filename: (\S+)/mi and $file = $1;
        $pdir = Packages_dir($dir, $file, $section) . "/binary-$arch";
        $pkgfile = "$pdir/Packages";
    }

    if (-e $pkgfile) {
        $st1 = stat("$pkgfile");
        $old_blocks += size_in_blocks($st1->size);
    }

    if (-e "$pkgfile.gz") {
        $st2 = stat("$pkgfile.gz");
        $old_blocks += size_in_blocks($st2->size);
    }

    $tmp_pkgfile = "$pkgfile" . ".rollback";

    msg_ap(0, "  Removing $p from $pkgfile(.gz)\n");

    open(IFILE, "<$pkgfile");
    open(OFILE, ">>$tmp_pkgfile");

    $gz = gzopen("$pkgfile.gz", "wb9");

    $/ = ''; # Browse by paragraph
    while (defined($match = <IFILE>)) {
        if (! ($match =~ /^Package: \Q$p\E$/m)) {
            print OFILE $match;
            $gz->gzwrite($match) or die "Failed to write $pkgfile.gz: $gzerrno\n";
        }
    }
    $/ = $old_split; # Browse by line again

    $gz->gzclose();
    close(IFILE);
    close(OFILE);

    rename $tmp_pkgfile, $pkgfile;
    $st1 = stat("$pkgfile");
    $st2 = stat("$pkgfile.gz");
    $size1 = $st1->size;
    $size2 = $st2->size;
    $new_blocks += size_in_blocks($st1->size);
    $new_blocks += size_in_blocks($st2->size);
    $blocks_removed += ($old_blocks - $new_blocks);
    msg_ap(0, "    now $size1 / $size2 bytes, $blocks_removed blocks removed\n");
    return $blocks_removed;
}

# Roll back the result of add_trans_desc_entry()
sub remove_trans_desc_entry {
    my $dir = shift;
    my $arch = shift;
    my $_ = shift;
    my ($p, $file, $section, $idir, $gz, $match, $st);
    my $size = 0;
    my $blocks_added = 0;
    my $old_blocks = 0;
    my $new_blocks = 0;

    m/^Package: (\S+)/m and $p = $1;
    m/^Section: (\S+)/m and $section = $1;

    m/^Filename: (\S+)/mi and $file = $1;
    $idir = Packages_dir($dir, $file, $section) . "/i18n";

    $/ = ''; # Browse by paragraph
    foreach my $lang (keys %descriptions) {
        # Do we have a translation for this language?
        if (defined $descriptions{$lang}{$p}{"data"}) {
            my $trans_file = "$idir/Translation-$lang";
            my $tmp_tfile = "$trans_file" . ".rollback";
            my $entries_remaining = 0;

            msg_ap(0, "  Removing $p from $trans_file(.gz)\n");

            # Keeping files in .gz format is expensive - see comment
            # in add_trans_desc_entry() above.
            if (-f "$trans_file.gz") {
                system("gunzip $trans_file.gz");
            }
            $st = stat("$trans_file") || die "unable to stat $trans_file\n";
            $old_blocks += size_in_blocks($st->size / 2);

            # Remove the description
            open(IFILE, "< $trans_file") || die "unable to open $trans_file\n";
            open(OFILE, ">> $tmp_tfile");

            while (defined($match = <IFILE>)) {
                if (! ($match =~ /^Package: \Q$p\E$/m)) {
                    print OFILE $match;
                    $entries_remaining++;
                }
            }

            close(IFILE);
            close(OFILE);
            
            $descriptions{$lang}{$p}{"used"} = 0;

            # If we still have any entries in the new file,
            # keep it. Otherwise, just delete it
            if ($entries_remaining) {
                rename $tmp_tfile, $trans_file;
                $st = stat("$trans_file") || die "unable to stat $trans_file\n";
                $size += int($st->size / 3);
                $new_blocks += size_in_blocks($st->size / 3);
            } else {
                unlink($tmp_tfile);
                unlink($trans_file);
            }
        }
    }
    $/ = $old_split; # Browse by line again
    $blocks_added += ($new_blocks - $old_blocks);
    msg_ap(0, "    now $size bytes, $blocks_added blocks added\n");
    return $blocks_added;
}

sub remove_md5_entry {
    my $dir = shift;
    my $arch = shift;
    my $_ = shift;
    my $md5file = "$dir/md5sum.txt";
    my $tmp_md5file = "$dir/md5sum.txt.tmp";
    my @fileslist;
    my ($pdir, $file, $md5, $match, $present, $st, $size, $p);
    my $blocks_removed = 0;
    my $old_blocks = 0;
    my $new_blocks = 0;

    $/ = $old_split; # Browse by line again

    m/^Package: (\S+)/mi and $p = $1;
    if ($arch eq "source") {
        m/^Directory: (\S+)/mi and $pdir = $1;       
	# Explicitly use the md5 lines in the Sources stanza, hence the xdigit(32) here
	while (/^ ([[:xdigit:]]{32}) (\d+) (\S+)/msg) { push(@fileslist, "$1  ./$pdir/$3"); }
    } else {
        m/^Filename: (\S+)/m and $file = $1;
        m/^MD5Sum: (\S+)/mi and push(@fileslist, "$1  ./$file");
    }

    if (-e $md5file) {
        $st = stat("$md5file");
        $old_blocks = size_in_blocks($st->size);
    }

    open(IFILE, "<$md5file");
    open(OFILE, ">>$tmp_md5file");
    while (defined($match = <IFILE>)) {
        $present = 0;
        foreach my $entry (@fileslist) {
            if (($match =~ /\Q$entry\E$/m)) {
                $present++;
            }
        }
        if (!$present) {
            print OFILE $match;
        }
    }
    close(IFILE);
    close(OFILE);

    $/ = ''; # Browse by paragraph again
    rename $tmp_md5file, $md5file;
    msg_ap(0, "  Removing $p from md5sum.txt\n");
    $st = stat("$dir/md5sum.txt");
    $size = $st->size;
    $new_blocks = size_in_blocks($st->size);
    $blocks_removed = $old_blocks - $new_blocks;
    msg_ap(0, "    now $size bytes, $blocks_removed blocks removed\n");
    $/ = $old_split; # Browse by line again
    return $blocks_removed;
}

sub get_file_blocks {
    my $realfile = shift;
    my $st;
    $st = stat($realfile) or die "unable to stat file $realfile: $!\n";
    return size_in_blocks($st->size);
}

sub add_packages {
    my ($p, @files, $d, $realfile, $source, $section, $name, $pkgfile, $pdir);
    my $dir;

    my $total_blocks = 0;
    my $rollback = 0;
    my $option = shift;	
    if ($option =~ /--rollback/) {
        $rollback = 1;
        $dir = shift;
    } else {	
        $dir = $option;
    }

    if (! -d $dir) { 
        die "add_packages: $dir is not a directory ..."; 
    }

    my $pkg = shift;
    my ($arch, $component, $pkgname, $pkgsize) = split /:/, $pkg;

    if ("$arch" eq "" or "$pkgname" eq "" or "$pkgname" eq "") {
        die "inconsistent data passed to add_packages: $pkg\n";
    }

    msg_ap(0, "Looking at $pkg: arch $arch, package $pkgname, rollback $rollback\n");

    foreach my $package_info (@{$pkginfo{$arch}{$pkgname}}) {
        undef @files;
        $source = $mirror;
        if ($arch eq "source") {
            if ($package_info =~ m/^Directory: (\S+)/m) {
                $pdir = $1;
            }
            if ($pdir =~ m:updates/:) {
                $source = $security;
            }
            # Explicitly use the md5 lines in the Sources stanza, hence the xdigit(32) here
            while ($package_info =~ /^ ([[:xdigit:]]{32}) (\d+) (\S+)/msg) {
                push(@files, "$pdir/$3");
            }
        } else {
            if ($package_info =~ m/^Filename: (\S+)/mi) {
                push(@files, $1);
            }
            if ($1 =~ m:updates/:) {
                $source = $security;
            }
        }

        if ($rollback) {
            # Remove the Packages entry/entries for the specified package
            $total_blocks -= remove_Packages_entry($dir, $arch, $package_info);
            $total_blocks -= remove_md5_entry($dir, $arch, $package_info);
            if (!($arch eq "source")) {
                $total_blocks -= remove_trans_desc_entry($dir, $arch, $package_info);
            }
        
            foreach my $file (@files) {
                my $missing = 0;
                # Count how big the file is we're removing, for checking if the disc is full
                if (! -e "$source/$file") {
                    msg_ap(0, "Can't find $file in the main archive, trying local\n");
                    if (-e "$localdebs/$file") {
                        $source = $localdebs;
                    } else {
                        die "$file not found under either $source or $localdebs\n";
                    }                        
                }
                $realfile = real_file ("$source/$file");
                $total_blocks -= get_file_blocks($realfile);

                # Remove the link
                unlink ("$dir/$file") || msg_ap(0, "Couldn't delete file $dir/$file\n");
                msg_ap(0, "  Rollback: removed $dir/$file\n");
            }
        } else {
            $total_blocks += add_Packages_entry($dir, $arch, $package_info);
            $total_blocks += add_md5_entry($dir, $arch, $package_info);
            if (!($arch eq "source")) {
                $total_blocks += add_trans_desc_entry($dir, $arch, $package_info);
            }

            foreach my $file (@files) {

                # And put the file in the CD tree (with a (hard) link)
                if (! -e "$source/$file") {
                    msg_ap(0, "Can't find $file in the main archive, trying local\n");
                    if (-e "$localdebs/$file") {
                        $source = $localdebs;
                    } else {
                        die "$file not found under either $source or $localdebs\n";
                    }                        
                }
                $realfile = real_file ("$source/$file");
                my $dstfile = "$file";
                $dstfile =~ s,.*(/(?:amd64|i386|all)/[^/]+),$dir/$1,;

                if (! -e "$dstfile") {
                    # Count how big the file is, for checking if the
                    # disc is full. ONLY do this if the file is not
                    # already linked in - consider binary-all packages
                    # on a multi-arch disc
                    $total_blocks += get_file_blocks($realfile);
                    $total_blocks += good_link ($realfile, "$dstfile");
                    msg_ap(0, "  Linked $dir/$file\n");
                    if ($firmware_package{$pkgname}) {
                        msg_ap(0, "Symlink fw package $pkgname into /firmware\n");
                        if (! -d "$dir/firmware") {
                            mkdir "$dir/firmware" or die "symlink failed $!\n";
                        }
                        symlink("../$file", "$dir/firmware/" . basename($file));
                        msg_ap(0, "Symlink ../$file $dir/firmware/.\n");
                    }
                } else {
                    msg_ap(0, "  $dir/$file already linked in\n");
                }
            }
        }
    }
#    close LIST or die "Something went wrong with apt-cache : $@ ($!)\n";
    msg_ap(0, "  size $total_blocks\n");
    $/ = $old_split; # Return to line-orientation
    return $total_blocks;
}
