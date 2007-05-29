# 	$Id: Config.pm,v 1.2 2003/09/08 07:14:37 thorsten Exp $	
package Unidump::Config;
use strict;
use AppConfig qw(:expand :argcount);
use Exporter;
use vars qw($VERSION @ISA);
$VERSION = do{my @r = split(" ",qq$Revision: 1.2 $ );$r[1];};
@ISA = qw(AppConfig);
use Data::Dumper;

my @global_options = qw(config unidir holdingdisk holdingdisksize magicfile
			diskmode usesyslog useunilog usestderr debug logfile
			logfiledir tocfiledir ntapedevice strategy 
			hwcompression restoredir);

my @disk_options = qw(group writeflags readflags useqfa softcompression
		      regulardump blocksize dumper ext2dump ext2restore 
		      xfsdump xfsrestore zip gtar star mt dd precommand
		      postcommand eotcommand verify starttime directory exclude);

my $options_re = 
  join("", "^(" ,
       join("|", @global_options, @disk_options),
       join("|[a-z]+_", @disk_options),
       ")\$");

my $create_re = 
  join("", "^(" , join("|", grep { s/^/[a-z]+_/ } @disk_options), ")\$");

sub generic_validate {
  my $option = shift;
  my $value  = shift if @_;
 SWITCH: for($option) {
   /([a-z]+_)?group/           and return 1;
   /([a-z]+_)?writeflags/      and return 1;
   /([a-z]+_)?readflags/       and return 1;
   /([a-z]+_)?useqfa/          and return($value =~ /^[01]$/);
   /([a-z]+_)?softcompression/ and return($value =~ /^[01]$/);
   /([a-z]+_)?regulardump/     and return($value =~ /^[01]$/);
   /([a-z]+_)?blocksize/       and return($value =~ /^\d+[kM]?$/);
   /([a-z]+_)?dumper/          and 
     return($value =~ /^(gtar|star|xfsdump|(ext2)?dump)$/);
   /([a-z]+_)?ext2dump/        and return($value =~ /^.+$/);
   /([a-z]+_)?ext2restore/     and return($value =~ /^.+$/);
   /([a-z]+_)?xfsdump/         and return($value =~ /^.+$/);
   /([a-z]+_)?xfsrestore/      and return($value =~ /^.+$/);
   /([a-z]+_)?zip/             and return($value =~ /^.+$/);
   /([a-z]+_)?gtar/            and return($value =~ /^.+$/);
   /([a-z]+_)?star/            and return($value =~ /^.+$/);
   /([a-z]+_)?mt/              and return($value =~ /^.+$/);
   /([a-z]+_)?dd/              and return($value =~ /^.+$/);
   /([a-z]+_)?precommand/      and return 1;
   /([a-z]+_)?postcommand/     and return 1;
   /([a-z]+_)?eotcommand/      and return 1;
   /([a-z]+_)?verify/          and return($value =~ /^[01]$/);
   /([a-z]+_)?starttime/       and return 1;
   /([a-z]+_)?directory/       and return($value =~ /^\//);
 }
  return 1;
}



sub new {
  my $class = shift;
  my $self = $class->SUPER::new({ CREATE => $create_re,
				  PEDANTIC => 1,
				  ERROR => sub { 
				    my $fmt=shift; 
				    $!=1;
				    warn(sprintf("$fmt\n", @_));
				  },
				  GLOBAL => {
				    DEFAULT  => undef,
				    EXPAND => 1,
				    ARGCOUNT => ARGCOUNT_ONE,
				    # default validation does not work yet!
				    #VALIDATE => \&generic_validate
				  }});
  bless $self, $class;
  return $self;
}

sub default {
  my $self = shift;

  $self->define("config" => { ALIAS => "file|f",
			      DEFAULT => "/etc/unidump.conf",
			      ARGCOUNT => ARGCOUNT_ONE,
			      VALIDATE => '^/'});
  
  $self->define("unidir" => { DEFAULT => "/var/lib/unidump",
			      ARGCOUNT => ARGCOUNT_ONE,
			      VALIDATE => '^/' });

  $self->define("holdingdisk" => { DEFAULT => $self->unidir . "/hd",
				   ARGCOUNT => ARGCOUNT_ONE,
				   VALIDATE => '^/' });

  $self->define("holdingdisksize" => { DEFAULT => 0,
				       ARGCOUNT => ARGCOUNT_ONE,
				       VALIDATE => q(^[-+]?\d+[kMGT]?$) });
  # holdingdisksize: 0       -> do not use holdingdisk
  #                  int > 0 -> write to hd unless du > int
  #                  int < 0 -> write to hd unless free space < hd

  $self->define("magicfile" => { DEFAULT => $self->unidir . "/magic",
				 ARGCOUNT => ARGCOUNT_ONE,
				 VALIDATE => '^/' });

  $self->define("diskmode" => { DEFAULT => 0,
				ARGCOUNT => ARGCOUNT_NONE });

  $self->define("usesyslog" => { DEFAULT => 0,
				 ARGCOUNT => ARGCOUNT_NONE });

  $self->define("useunilog" => { DEFAULT => 0,
				 ARGCOUNT => ARGCOUNT_NONE });

  $self->define("usestderr" => { DEFAULT => 0,
				 ARGCOUNT => ARGCOUNT_NONE });

  $self->define("debug" => { DEFAULT => 0,
			     ARGCOUNT => ARGCOUNT_NONE });

  $self->define("logfile" => { DEFAULT => $self->unidir . "/unidump.log",
			       ARGCOUNT => ARGCOUNT_ONE,
			       VALIDATE => '^/' });
  
  $self->define("logfiledir" => { DEFAULT => $self->unidir . "/log",
				  ARGCOUNT => ARGCOUNT_ONE,
				  VALIDATE => '^/'  });
  
  $self->define("tocfiledir" => { DEFAULT => $self->unidir . "/toc",
				  ARGCOUNT => ARGCOUNT_ONE,
				  VALIDATE => '^/'  });
  
  $self->define("ntapedevice" => { DEFAULT => "/dev/nst0",
				   ARGCOUNT => ARGCOUNT_ONE,
				   VALIDATE => '(^/)|(@/)'  });

  $self->define("strategy" => { DEFAULT => "simple",
				ARGCOUNT => ARGCOUNT_ONE });

  $self->define("group" => { DEFAULT => "",
			     ARGCOUNT => ARGCOUNT_ONE });

  $self->define("writeflags" => { ARGCOUNT => ARGCOUNT_ONE });

  $self->define("readflags" => { ARGCOUNT => ARGCOUNT_ONE });

  $self->define("useqfa" => { DEFAULT => 0,
			      ARGCOUNT => ARGCOUNT_NONE });

  $self->define("softcompression" => { DEFAULT => 0,
				       ARGCOUNT => ARGCOUNT_NONE });

  $self->define("hwcompression" => { DEFAULT => 0,
				     ARGCOUNT => ARGCOUNT_NONE });

  $self->define("regulardump" => { DEFAULT => 0,
				   ARGCOUNT => ARGCOUNT_NONE });
  
  $self->define("blocksize" => { DEFAULT => 65536,
				 ARGCOUNT => ARGCOUNT_ONE,
				 VALIDATE => q(^-?\d+[kM]?$)  });

  $self->define("dumper" => { DEFAULT => "gtar",
			      ARGCOUNT => ARGCOUNT_ONE,
			      VALIDATE => 
				'^(gtar|star|xfsdump|(ext2)?dump)'});
  
  $self->define("ext2dump" => { DEFAULT => 
				  $self->unidir . "/scripts/dump_wrapper",
				  ARGCOUNT => ARGCOUNT_ONE });

  $self->define("ext2restore" => { 
    DEFAULT =>  $self->unidir . "/scripts/restore_wrapper",
    ARGCOUNT => ARGCOUNT_ONE });
  
  $self->define("xfsdump" => { DEFAULT => "xfsdump",
			       ARGCOUNT => ARGCOUNT_ONE });

  $self->define("xfsrestore" => { DEFAULT => "xfsrestore",
				  ARGCOUNT => ARGCOUNT_ONE });

  $self->define("zip" => { DEFAULT => "zip",
			   ARGCOUNT => ARGCOUNT_ONE });

  $self->define("gtar" => { DEFAULT => "tar",
			    ARGCOUNT => ARGCOUNT_ONE });

  $self->define("star" => { DEFAULT => "star",
			    ARGCOUNT => ARGCOUNT_ONE });

  $self->define("mt" => { DEFAULT => "mt",
			  ARGCOUNT => ARGCOUNT_ONE });

  $self->define("dd" => { DEFAULT => "dd",
			  ARGCOUNT => ARGCOUNT_ONE });

  $self->define("precommand" => { ARGCOUNT => ARGCOUNT_ONE });

  $self->define("postcommand" => { ARGCOUNT => ARGCOUNT_ONE });

  $self->define("eotcommand" => { DEFAULT => 
				    $self->unidir . "/scripts/exit2",
				  ARGCOUNT => ARGCOUNT_ONE });
  
  $self->define("verify" => { ARGCOUNT => ARGCOUNT_NONE });

  $self->define("starttime" => { DEFAULT => time(),
				 ARGCOUNT => ARGCOUNT_ONE });

  
  $self->define("restoredir" => { DEFAULT => "/tmp/unirestore",
				  ARGCOUNT => ARGCOUNT_ONE,
				  VALIDATE => '^/' });
		
  $self->define("level" => { ARGCOUNT => ARGCOUNT_ONE });

  $self->define("exclude" => { ARGCOUNT => ARGCOUNT_ONE });

  return $self;
}

sub dumphash {
  my $self = shift;
  my %dump = $self->varlist(q/_directory$/, 1);
  my %global = $self->varlist(q/^[^_]+$/);
  foreach(keys %dump) {
    my %tmp = %global;
    my %local = $self->varlist("^$_" . "_", 1);
    while(my($k, $v) = each %local) {
      $tmp{$k} = $v;
    }
    $dump{$_} = { %tmp };
  }
  return %dump;
}

1;

__END__


=head1 NAME

Unidump::Config - configuration and commandline arguments

=head1 SYNOPSIS

  use Unidump::Config;
  $conf = Unidump::Config->new();
  %h = $conf->dumphash;

=head1 DESCRIPTION

B<Config> inherits from AppConfig, see L<AppConfig> for details. 

All options are build of alphanumeric characters. Options that
contain an underscore `_' are disk-specific, others are global.
e.g. `softcompression' is a global value while `home_directory' is a
disk-specific value. Some options make sense as common settings only
(e.g. unidir, strategy,...). These options are called global
options. For others you might (or sometimes should) specify
different values for your disks. These options are calles
disk-specific. Note, that it is valid to specify a common default
for these options. 

=head2 Methods
  
=over

=item %h = $conf->dumphash
  
return a hash of hashrefs. Keys are the names of the disks, values
are all options of the disk. Global options are merged into the
hashes unless they are overwritten by a disk-specific option.

Example:

  This is the config file:

  # global section
  ntapedevice = /dev/nzqft0
  blocksize = 10k
  dumper = dump

  # define a disk "home"
  [home]
  directory = /home
  dumper = xfsdump

  [system]
  directory = /


This will lead to a dumphash like this:
  
  $VAR1 = {
          'home' => {
                      'ntapedevice' => '/dev/nzqft0',
                      'blocksize' => '10k',
                      'dumper' => 'xfsdump',
                      'directory' => '/home'
                    },
          'system' => {
                        'ntapedevice' => '/dev/nzqft0',
                        'blocksize' => '10k',
                        'dumper' => 'dump',
                        'directory' => '/'
                      }
        };



=back


=head2 supported global options 

All global options might be given as commandline options. 
Commandline options overrides config file options. Options with argument 
are given with blank(s) between option and argument:
 -config /etc/unidump.conf
Flags might be switched on or off:
 -debug
 -nodebug


=over 2

=item config (/etc/unidump.conf)

UNIDUMP configfile


=item debug (0)

flag: print debug messages to stderr


=item diskmode (0) 

flag: dump to holdingdisk do not use tape 


=item holdingdisk ($unidir/hd)

path to  holdingdisk


=item holdingdisksize (0) 

if set to a positive value means the max. size of  holdingdisk
if set to a negative value, means leave that much free space on holdingdisk
if set to zero, do not use holdingdisk at all. Valid units are <none>,k,M,G,T. 
Default is <none> (= Bytes).


=item hwcompression (0) 

flag: enable hardware-compression
this works only for some scsi2-tapes. In all other cases you have to
enable the hardware-compression by yourself. This might be done by
choosing the appropriate device (e.g. /dev/nzqft0 for the first floppy-device)
or in some rare cases by setting the denity code using `mt'.


=item level (<undef>)

sets the dumplevel regardless of strategy


=item logfile ($unidir/unidump.log) 

path to  logfile


=item logfiledir ($unidir/log) 

directory for logfiles of  dump-processes


=item ntapedevice (/dev/nst0) 

tape-device (non-rewinding)


=item restoredir (/tmp/unirestore)

directory used to restore data


=item strategy (simple)

backup strategy (see Unidump::Strategy for details)


=item tocfiledir ($unidir/toc)

directory for listings of  dumps


=item unidir (/var/lib/unidump)

UNIDUMP directory


=item usestderr (0) 

flag: log to stderr


=item usesyslog (0) 

flag: use syslog for logging


=item useunilog (0) 

flag: log to extra logfile

=back



=head2 supported disk-specific options 

=over 2

=item blocksize (64k)

blocksize used fore reading and writing from/to tape. Some tapes 
need a fixed blocksize (e.g. floppy tapes 10k by default). You cannot use softwarecompression 
on such a tape. Valid units are <none>,k,M. Default unit is <none> (= bytes).


=item dd (dd)

command to start GNU dd


=item directory (undef)

full path to the directory to dump. This is the only option that must
be specified for every disk.


=item dumper (gtar) 

dumper to use (currently supported are: ext2dump, xfsdump)


=item eotcommand "sh -c 'exit 2'" 

this command will be executed if the end-of-tape mark is reached.
The default will abort the whole dump.


=item ext2dump ($unidir/scripts/dump_wrapper)

command to start ext2dump


=item exclude (undef)

a colon-separated list of files/directories to exclude from dump. 
Note that xfsdump does not support exclusion in this way. If you use 
xfsdump for backup, set exclude files/directories by setting the 
extended attribute "SGI_XFSDUMP_SKIP_FILE".


=item ext2restore ($unidir/scripts/restore_wrapper)

command to start ext2restore


=item group (undef)

backup strategy group (see Unidump::Strategy)


=item gtar (tar)

command to start GNU tar



=item mt (mt)

command to start mt (GNU mt or mt-st)



=item postcommand (undef)

this command will be executed after the dump was done



=item precommand (undef)

this command will be executed before the dump is started


=item readflags (undef)

additional options passed to the restorer



=item regulardump (0) 

flag: this permits further dumps to base on this dump. This option should be enabled for
all scheduled dumps. On-demand dumps might be performed without this flag. 
This flag sets the `-u' option in B<dump> and unsets the `-I' option in B<xfsdump>.




=item softcompression (0) 

flag: enable software-compression (libz or gzip)


=item star (star)

command to start Schily-tar



=item starttime (time())

timestamp used to evaluate the strategy. This can be used to force a dump
on a specific tape.


=item useqfa (0) 

flag: use quick-file-access (ext2dump only)


=item verify (undef)

flag: compare data on tape and data on disk after write


=item writeflags (undef)

additional options passed to the dumper


=item xfsdump (xfsdump)

command to start xfsdump


=item xfsrestore (xfsrestore)

command to start xfsrestore


=item zip (zip)

command to start INFO-zip


=back



=head2 Configfile example
  
	#unidir		=	/var/lib/unidump
	#ntapedevice	=	/dev/nst0
	#holdingdisk	=	/var/lib/unidump/hd
	#holdingdisksize=	0
	#magicfile	=	/var/lib/unidump/magic
	#logfile	=	/var/lib/unidump/unidump.log
	#logfiledir	=	/var/lib/unidump/log
	#restoredir	=	/tmp/unirestore
	#strategy	=	simple
	#blocksize	=	64k
	#mt		=	mt
	#dd		=	dd
	#ext2dump	=	/var/lib/unidump/scripts/dump_wrapper
	#ext2restore	=	/var/lib/unidump/scripts/restore_wrapper
	#xfsdump	=	xfsdump
	#xfsrestore	=	xfsrestore
	#zip		=	zip
	#gtar		=	gtar
	#star		=	star
	#precommand	=
	#postcommand	=
	#eotcommand	=	"sh -c 'exit 2'"
	
	#writeflags	=
	#readflags	=
	
	#diskmode	= 0
	#regulardump	= 0
	#softcompression= 0
	#hwcompression	= 0
	#useqfa		= 0
	#useunilog	= 0
	#usesyslog	= 0
	#usestderr	= 0
	#debug		= 0
	
	[system]
	dumper		=	ext2dump
	directory	=	/
	
	[home]
	dumper		=	xfsdump
	directory	=	/home
	
	[vmware]
	dumper		=	ext2dump
	directory	=	/vmware
	
