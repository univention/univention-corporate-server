my $symlink_farm = read_env('SYMLINK', 0);
my $link_verbose = read_env('VERBOSE', 0);
my $link_copy = read_env('COPYLINK', 0);

sub read_env {
    my $env_var = shift;
    my $default = shift;

    if (exists($ENV{$env_var})) {
        return $ENV{$env_var};
    }
    # else
    return $default;
}

sub good_link ($$) {
	my ($src, $dest) = @_;
	return 0 if (-e $dest);

	my $dir_added = 0;

	# Check if the destination directory does exist
	my $ddir = $dest;
	$ddir =~ s#/?[^/]+$##g;
	if ($ddir eq "")
	{
		$ddir = ".";
	}
	if (! -d $ddir) # Create it if not
	{
		system("mkdir -p $ddir");
		$dir_added++;
	}

	# Link the files
	if ($symlink_farm) {
		print "Symlink: $dest => $src\n" if ($link_verbose >= 3);
		if (not symlink ($src, $dest)) {
			print STDERR "Symlink from $src to $dest failed: $!\n";
		}
		return $dir_added;
	}
	if (! $link_copy) {
		print "Hardlink: $dest => $src\n" if ($link_verbose >= 3);
		if (link ($src, $dest)) {
			return $dir_added;
		}
		print STDERR "Link from $src to $dest failed: $!\n";
	}
	print "Copy: $dest => $src\n" if ($link_verbose >= 3);
	if (system("cp -ap $src $dest")) {
		my $err_num = $? >> 8;
		my $sig_num = $? & 127;
		print STDERR "Copy from $src to $dest failed: cp exited with error code $err_num, signal $sig_num\n";
	}
	return $dir_added;
}

sub real_file ($) {
	my $link = shift;
	my ($dir, $to);
	
	while (-l $link) {
		$dir = $link;
		$dir =~ s#[^/]+/?$##;
		if ($to = readlink($link)) {
			$link = $dir . $to;
		} else {
			print STDERR "Can't readlink $link: $!\n";
		}
	}

	return $link;
}


1;
