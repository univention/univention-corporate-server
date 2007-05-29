# This Makefile is for the Unidump extension to perl.
#
# It was generated automatically by MakeMaker version
# 6.03 (Revision: 1.63) from the contents of
# Makefile.PL. Don't edit this file, edit Makefile.PL instead.
#
#       ANY CHANGES MADE HERE WILL BE LOST!
#
#   MakeMaker ARGV: (q[INSTALLDIRS=vendor])
#
#   MakeMaker Parameters:

#     ABSTRACT => q[Unidump - Perl extension for scheduled backup]
#     AUTHOR => q[Joerg Ungethuem <joerg.ungethuem@enersim.de>]
#     EXE_FILES => [q[scripts/unidump], q[scripts/unilabel], q[scripts/unirest], q[scripts/unilib], q[scripts/uniresume], q[scripts/unitoc], q[scripts/uniflush], q[scripts/unilist], q[scripts/unisched], q[scripts/unihist], q[scripts/uniproper], q[scripts/unistat], q[scripts/unihrest]]
#     MAN3PODS => { Unidump/Strategy.pm=>q[$(INST_MAN3DIR)/Unidump::Strategy.$(MAN3EXT)], Unidump/Logger.pm=>q[$(INST_MAN3DIR)/Unidump::Logger.$(MAN3EXT)], Unidump/Config.pm=>q[$(INST_MAN3DIR)/Unidump::Config.$(MAN3EXT)], Unidump/Units.pm=>q[$(INST_MAN3DIR)/Unidump::Units.$(MAN3EXT)], Unidump.pm=>q[$(INST_MAN3DIR)/Unidump.$(MAN3EXT)], Unidump/History.pm=>q[$(INST_MAN3DIR)/Unidump::History.$(MAN3EXT)] }
#     NAME => q[Unidump]
#     PMLIBDIRS => [q[Unidump]]
#     PREREQ_PM => { File::Remove=>q[0], Unix::Syslog=>q[0.9], Data::ShowTable=>q[0], Class::Accessor=>q[0], AppConfig=>q[1.5], Date::Parse=>q[0] }
#     VERSION => q[0.5]

# --- MakeMaker post_initialize section:


# --- MakeMaker const_config section:

# These definitions are from config.sh (via /usr/lib/perl/5.8.0/Config.pm)

# They may have been overridden via Makefile.PL or on the command line
AR = ar
CC = cc
CCCDLFLAGS = -fPIC
CCDLFLAGS = -rdynamic
DLEXT = so
DLSRC = dl_dlopen.xs
LD = cc
LDDLFLAGS = -shared -L/usr/local/lib
LDFLAGS =  -L/usr/local/lib
LIBC = /lib/libc-2.3.2.so
LIB_EXT = .a
OBJ_EXT = .o
OSNAME = linux
OSVERS = 2.4.18-xfs
RANLIB = :
SO = so
EXE_EXT = 
FULL_AR = /usr/bin/ar


# --- MakeMaker constants section:
AR_STATIC_ARGS = cr
NAME = Unidump
DISTNAME = Unidump
NAME_SYM = Unidump
VERSION = 0.5
VERSION_SYM = 0_5
XS_VERSION = 0.5
INST_ARCHLIB = blib/arch
INST_SCRIPT = blib/script
INST_BIN = blib/bin
INST_LIB = blib/lib
INSTALLDIRS = vendor
PREFIX = /usr
SITEPREFIX = $(PREFIX)/local
VENDORPREFIX = $(PREFIX)
INSTALLPRIVLIB = $(PREFIX)/share/perl/5.8.0
INSTALLSITELIB = $(SITEPREFIX)/share/perl/5.8.0
INSTALLVENDORLIB = $(VENDORPREFIX)/share/perl5
INSTALLARCHLIB = $(PREFIX)/lib/perl/5.8.0
INSTALLSITEARCH = $(SITEPREFIX)/lib/perl/5.8.0
INSTALLVENDORARCH = $(VENDORPREFIX)/lib/perl5
INSTALLBIN = $(PREFIX)/bin
INSTALLSITEBIN = $(SITEPREFIX)/bin
INSTALLVENDORBIN = $(VENDORPREFIX)/bin
INSTALLSCRIPT = $(PREFIX)/bin
PERL_LIB = /usr/share/perl/5.8.0
PERL_ARCHLIB = /usr/lib/perl/5.8.0
SITELIBEXP = /usr/local/share/perl/5.8.0
SITEARCHEXP = /usr/local/lib/perl/5.8.0
LIBPERL_A = libperl.a
FIRST_MAKEFILE = Makefile
MAKE_APERL_FILE = Makefile.aperl
PERLMAINCC = $(CC)
PERL_INC = /usr/lib/perl/5.8.0/CORE
PERL = /usr/bin/perl
FULLPERL = /usr/bin/perl
PERLRUN = $(PERL)
FULLPERLRUN = $(FULLPERL)
PERLRUNINST = $(PERLRUN) "-I$(INST_ARCHLIB)" "-I$(INST_LIB)"
FULLPERLRUNINST = $(FULLPERLRUN) "-I$(INST_ARCHLIB)" "-I$(INST_LIB)"
ABSPERL = $(PERL)
ABSPERLRUN = $(ABSPERL)
ABSPERLRUNINST = $(ABSPERLRUN) "-I$(INST_ARCHLIB)" "-I$(INST_LIB)"
FULL_AR = /usr/bin/ar
PERL_CORE = 0
NOOP = $(SHELL) -c true
NOECHO = @

VERSION_MACRO = VERSION
DEFINE_VERSION = -D$(VERSION_MACRO)=\"$(VERSION)\"
XS_VERSION_MACRO = XS_VERSION
XS_DEFINE_VERSION = -D$(XS_VERSION_MACRO)=\"$(XS_VERSION)\"
PERL_MALLOC_DEF = -DPERL_EXTMALLOC_DEF -Dmalloc=Perl_malloc -Dfree=Perl_mfree -Drealloc=Perl_realloc -Dcalloc=Perl_calloc

MAKEMAKER = /usr/share/perl/5.8.0/ExtUtils/MakeMaker.pm
MM_VERSION = 6.03

# FULLEXT = Pathname for extension directory (eg Foo/Bar/Oracle).
# BASEEXT = Basename part of FULLEXT. May be just equal FULLEXT. (eg Oracle)
# PARENT_NAME = NAME without BASEEXT and no trailing :: (eg Foo::Bar)
# DLBASE  = Basename part of dynamic library. May be just equal BASEEXT.
FULLEXT = Unidump
BASEEXT = Unidump
PARENT_NAME = 
DLBASE = $(BASEEXT)
OBJECT = 
LDFROM = $(OBJECT)
LINKTYPE = dynamic

# Handy lists of source code files:
XS_FILES= 
C_FILES = 
O_FILES = 
H_FILES = 
MAN1PODS = scripts/unidump \
	scripts/uniflush \
	scripts/unihist \
	scripts/unilabel \
	scripts/unilib \
	scripts/unilist \
	scripts/uniproper \
	scripts/unirest \
	scripts/uniresume \
	scripts/unisched \
	scripts/unistat \
	scripts/unitoc
MAN3PODS = Unidump.pm \
	Unidump/Config.pm \
	Unidump/History.pm \
	Unidump/Logger.pm \
	Unidump/Strategy.pm \
	Unidump/Units.pm
INST_MAN1DIR = blib/man1
MAN1EXT = 1p
INSTALLMAN1DIR = $(PREFIX)/share/man/man1
INSTALLSITEMAN1DIR = $(SITEPREFIX)/man/man1
INSTALLVENDORMAN1DIR = $(VENDORPREFIX)/share/man/man1
INST_MAN3DIR = blib/man3
MAN3EXT = 3pm
INSTALLMAN3DIR = $(PREFIX)/share/man/man3
INSTALLSITEMAN3DIR = $(SITEPREFIX)/man/man3
INSTALLVENDORMAN3DIR = $(VENDORPREFIX)/share/man/man3
PERM_RW = 644
PERM_RWX = 755

# work around a famous dec-osf make(1) feature(?):
makemakerdflt: all

.SUFFIXES: .xs .c .C .cpp .i .s .cxx .cc $(OBJ_EXT)

# Nick wanted to get rid of .PRECIOUS. I don't remember why. I seem to recall, that
# some make implementations will delete the Makefile when we rebuild it. Because
# we call false(1) when we rebuild it. So make(1) is not completely wrong when it
# does so. Our milage may vary.
# .PRECIOUS: Makefile    # seems to be not necessary anymore

.PHONY: all config static dynamic test linkext manifest

# Where is the Config information that we are using/depend on
CONFIGDEP = $(PERL_ARCHLIB)/Config.pm $(PERL_INC)/config.h

# Where to put things:
INST_LIBDIR      = $(INST_LIB)
INST_ARCHLIBDIR  = $(INST_ARCHLIB)

INST_AUTODIR     = $(INST_LIB)/auto/$(FULLEXT)
INST_ARCHAUTODIR = $(INST_ARCHLIB)/auto/$(FULLEXT)

INST_STATIC  =
INST_DYNAMIC =
INST_BOOT    =

EXPORT_LIST = 

PERL_ARCHIVE = 

PERL_ARCHIVE_AFTER = 

TO_INST_PM = Unidump.pm \
	Unidump/Config.pm \
	Unidump/Dumper.pm \
	Unidump/Ext2Dumper.pm \
	Unidump/GenericDumper.pm \
	Unidump/GtarDumper.pm \
	Unidump/History.pm \
	Unidump/Logger.pm \
	Unidump/StarDumper.pm \
	Unidump/Strategy.pm \
	Unidump/Tape.pm \
	Unidump/Tapelib.pm \
	Unidump/Units.pm \
	Unidump/XfsDumper.pm

PM_TO_BLIB = Unidump/GtarDumper.pm \
	blib/lib/Unidump/GtarDumper.pm \
	Unidump/Dumper.pm \
	blib/lib/Unidump/Dumper.pm \
	Unidump/XfsDumper.pm \
	blib/lib/Unidump/XfsDumper.pm \
	Unidump/Tape.pm \
	blib/lib/Unidump/Tape.pm \
	Unidump/Config.pm \
	blib/lib/Unidump/Config.pm \
	Unidump/Units.pm \
	blib/lib/Unidump/Units.pm \
	Unidump/StarDumper.pm \
	blib/lib/Unidump/StarDumper.pm \
	Unidump/Strategy.pm \
	blib/lib/Unidump/Strategy.pm \
	Unidump/Logger.pm \
	blib/lib/Unidump/Logger.pm \
	Unidump/Tapelib.pm \
	blib/lib/Unidump/Tapelib.pm \
	Unidump.pm \
	blib/lib/Unidump.pm \
	Unidump/History.pm \
	blib/lib/Unidump/History.pm \
	Unidump/Ext2Dumper.pm \
	blib/lib/Unidump/Ext2Dumper.pm \
	Unidump/GenericDumper.pm \
	blib/lib/Unidump/GenericDumper.pm


# --- MakeMaker tool_autosplit section:
# Usage: $(AUTOSPLITFILE) FileToSplit AutoDirToSplitInto
AUTOSPLITFILE = $(PERLRUN) -e 'use AutoSplit;  autosplit($$ARGV[0], $$ARGV[1], 0, 1, 1) ;'



# --- MakeMaker tool_xsubpp section:


# --- MakeMaker tools_other section:

SHELL = /bin/sh
CHMOD = chmod
CP = cp
LD = cc
MV = mv
NOOP = $(SHELL) -c true
RM_F = rm -f
RM_RF = rm -rf
TEST_F = test -f
TOUCH = touch
UMASK_NULL = umask 0
DEV_NULL = > /dev/null 2>&1

# The following is a portable way to say mkdir -p
# To see which directories are created, change the if 0 to if 1
MKPATH = $(PERLRUN) "-MExtUtils::Command" -e mkpath

# This helps us to minimize the effect of the .exists files A yet
# better solution would be to have a stable file in the perl
# distribution with a timestamp of zero. But this solution doesn't
# need any changes to the core distribution and works with older perls
EQUALIZE_TIMESTAMP = $(PERLRUN) "-MExtUtils::Command" -e eqtime

# Here we warn users that an old packlist file was found somewhere,
# and that they should call some uninstall routine
WARN_IF_OLD_PACKLIST = $(PERL) -we 'exit unless -f $$ARGV[0];' \
-e 'print "WARNING: I have found an old package in\n";' \
-e 'print "\t$$ARGV[0].\n";' \
-e 'print "Please make sure the two installations are not conflicting\n";'

UNINST=0
VERBINST=0

MOD_INSTALL = $(PERL) "-I$(INST_LIB)" "-I$(PERL_LIB)" "-MExtUtils::Install" \
-e "install({@ARGV},'$(VERBINST)',0,'$(UNINST)');"

DOC_INSTALL = $(PERL) -e '$$\="\n\n";' \
-e 'print "=head2 ", scalar(localtime), ": C<", shift, ">", " L<", $$arg=shift, "|", $$arg, ">";' \
-e 'print "=over 4";' \
-e 'while (defined($$key = shift) and defined($$val = shift)){print "=item *";print "C<$$key: $$val>";}' \
-e 'print "=back";'

UNINSTALL =   $(PERLRUN) "-MExtUtils::Install" \
-e 'uninstall($$ARGV[0],1,1); print "\nUninstall is deprecated. Please check the";' \
-e 'print " packlist above carefully.\n  There may be errors. Remove the";' \
-e 'print " appropriate files manually.\n  Sorry for the inconveniences.\n"'


# --- MakeMaker dist section:
ZIPFLAGS = -r
TO_UNIX = @$(NOOP)
TAR = tar
POSTOP = @$(NOOP)
ZIP = zip
DIST_DEFAULT = tardist
CI = ci -u
SHAR = shar
COMPRESS = gzip --best
DIST_CP = best
PREOP = @$(NOOP)
TARFLAGS = cvf
DISTVNAME = $(DISTNAME)-$(VERSION)
SUFFIX = .gz
RCS_LABEL = rcs -Nv$(VERSION_SYM): -q


# --- MakeMaker macro section:


# --- MakeMaker depend section:


# --- MakeMaker cflags section:


# --- MakeMaker const_loadlibs section:


# --- MakeMaker const_cccmd section:


# --- MakeMaker post_constants section:


# --- MakeMaker pasthru section:

PASTHRU = LIB="$(LIB)"\
	LIBPERL_A="$(LIBPERL_A)"\
	LINKTYPE="$(LINKTYPE)"\
	PREFIX="$(PREFIX)"\
	OPTIMIZE="$(OPTIMIZE)"\
	PASTHRU_DEFINE="$(PASTHRU_DEFINE)"\
	PASTHRU_INC="$(PASTHRU_INC)"


# --- MakeMaker c_o section:


# --- MakeMaker xs_c section:


# --- MakeMaker xs_o section:


# --- MakeMaker top_targets section:

all :: pure_all manifypods
	@$(NOOP)

pure_all :: config pm_to_blib subdirs linkext
	@$(NOOP)

subdirs :: $(MYEXTLIB)
	@$(NOOP)

config :: Makefile $(INST_LIBDIR)/.exists
	@$(NOOP)

config :: $(INST_ARCHAUTODIR)/.exists
	@$(NOOP)

config :: $(INST_AUTODIR)/.exists
	@$(NOOP)

$(INST_AUTODIR)/.exists :: /usr/lib/perl/5.8.0/CORE/perl.h
	@$(MKPATH) $(INST_AUTODIR)
	@$(EQUALIZE_TIMESTAMP) /usr/lib/perl/5.8.0/CORE/perl.h $(INST_AUTODIR)/.exists

	-@$(CHMOD) $(PERM_RWX) $(INST_AUTODIR)

$(INST_LIBDIR)/.exists :: /usr/lib/perl/5.8.0/CORE/perl.h
	@$(MKPATH) $(INST_LIBDIR)
	@$(EQUALIZE_TIMESTAMP) /usr/lib/perl/5.8.0/CORE/perl.h $(INST_LIBDIR)/.exists

	-@$(CHMOD) $(PERM_RWX) $(INST_LIBDIR)

$(INST_ARCHAUTODIR)/.exists :: /usr/lib/perl/5.8.0/CORE/perl.h
	@$(MKPATH) $(INST_ARCHAUTODIR)
	@$(EQUALIZE_TIMESTAMP) /usr/lib/perl/5.8.0/CORE/perl.h $(INST_ARCHAUTODIR)/.exists

	-@$(CHMOD) $(PERM_RWX) $(INST_ARCHAUTODIR)

config :: $(INST_MAN1DIR)/.exists
	@$(NOOP)


$(INST_MAN1DIR)/.exists :: /usr/lib/perl/5.8.0/CORE/perl.h
	@$(MKPATH) $(INST_MAN1DIR)
	@$(EQUALIZE_TIMESTAMP) /usr/lib/perl/5.8.0/CORE/perl.h $(INST_MAN1DIR)/.exists

	-@$(CHMOD) $(PERM_RWX) $(INST_MAN1DIR)

config :: $(INST_MAN3DIR)/.exists
	@$(NOOP)


$(INST_MAN3DIR)/.exists :: /usr/lib/perl/5.8.0/CORE/perl.h
	@$(MKPATH) $(INST_MAN3DIR)
	@$(EQUALIZE_TIMESTAMP) /usr/lib/perl/5.8.0/CORE/perl.h $(INST_MAN3DIR)/.exists

	-@$(CHMOD) $(PERM_RWX) $(INST_MAN3DIR)

help:
	perldoc ExtUtils::MakeMaker


# --- MakeMaker linkext section:

linkext :: $(LINKTYPE)
	@$(NOOP)


# --- MakeMaker dlsyms section:


# --- MakeMaker dynamic section:

## $(INST_PM) has been moved to the all: target.
## It remains here for awhile to allow for old usage: "make dynamic"
#dynamic :: Makefile $(INST_DYNAMIC) $(INST_BOOT) $(INST_PM)
dynamic :: Makefile $(INST_DYNAMIC) $(INST_BOOT)
	@$(NOOP)


# --- MakeMaker dynamic_bs section:

BOOTSTRAP =


# --- MakeMaker dynamic_lib section:


# --- MakeMaker static section:

## $(INST_PM) has been moved to the all: target.
## It remains here for awhile to allow for old usage: "make static"
#static :: Makefile $(INST_STATIC) $(INST_PM)
static :: Makefile $(INST_STATIC)
	@$(NOOP)


# --- MakeMaker static_lib section:


# --- MakeMaker manifypods section:
POD2MAN_EXE = /usr/bin/pod2man
POD2MAN = $(PERL) -we '%m=@ARGV;for (keys %m){' \
-e 'next if -e $$m{$$_} && -M $$m{$$_} < -M $$_ && -M $$m{$$_} < -M "Makefile";' \
-e 'print "Manifying $$m{$$_}\n";' \
-e 'system(q[$(PERLRUN) $(POD2MAN_EXE) ].qq[$$_>$$m{$$_}])==0 or warn "Couldn\047t install $$m{$$_}\n";' \
-e 'chmod(oct($(PERM_RW)), $$m{$$_}) or warn "chmod $(PERM_RW) $$m{$$_}: $$!\n";}'

manifypods : pure_all scripts/uniproper \
	scripts/unisched \
	scripts/unitoc \
	scripts/uniresume \
	scripts/unihist \
	scripts/unilist \
	scripts/unidump \
	scripts/unistat \
	scripts/uniflush \
	scripts/unilib \
	scripts/unirest \
	scripts/unilabel \
	Unidump/Strategy.pm \
	Unidump/Logger.pm \
	Unidump/Config.pm \
	Unidump/Units.pm \
	Unidump.pm \
	Unidump/History.pm
	@$(POD2MAN) \
	scripts/uniproper \
	$(INST_MAN1DIR)/uniproper.$(MAN1EXT) \
	scripts/unisched \
	$(INST_MAN1DIR)/unisched.$(MAN1EXT) \
	scripts/unitoc \
	$(INST_MAN1DIR)/unitoc.$(MAN1EXT) \
	scripts/uniresume \
	$(INST_MAN1DIR)/uniresume.$(MAN1EXT) \
	scripts/unihist \
	$(INST_MAN1DIR)/unihist.$(MAN1EXT) \
	scripts/unilist \
	$(INST_MAN1DIR)/unilist.$(MAN1EXT) \
	scripts/unidump \
	$(INST_MAN1DIR)/unidump.$(MAN1EXT) \
	scripts/unistat \
	$(INST_MAN1DIR)/unistat.$(MAN1EXT) \
	scripts/uniflush \
	$(INST_MAN1DIR)/uniflush.$(MAN1EXT) \
	scripts/unilib \
	$(INST_MAN1DIR)/unilib.$(MAN1EXT) \
	scripts/unirest \
	$(INST_MAN1DIR)/unirest.$(MAN1EXT) \
	scripts/unilabel \
	$(INST_MAN1DIR)/unilabel.$(MAN1EXT) \
	Unidump/Strategy.pm \
	$(INST_MAN3DIR)/Unidump::Strategy.$(MAN3EXT) \
	Unidump/Logger.pm \
	$(INST_MAN3DIR)/Unidump::Logger.$(MAN3EXT) \
	Unidump/Config.pm \
	$(INST_MAN3DIR)/Unidump::Config.$(MAN3EXT) \
	Unidump/Units.pm \
	$(INST_MAN3DIR)/Unidump::Units.$(MAN3EXT) \
	Unidump.pm \
	$(INST_MAN3DIR)/Unidump.$(MAN3EXT) \
	Unidump/History.pm \
	$(INST_MAN3DIR)/Unidump::History.$(MAN3EXT)

# --- MakeMaker processPL section:


# --- MakeMaker installbin section:

$(INST_SCRIPT)/.exists :: /usr/lib/perl/5.8.0/CORE/perl.h
	@$(MKPATH) $(INST_SCRIPT)
	@$(EQUALIZE_TIMESTAMP) /usr/lib/perl/5.8.0/CORE/perl.h $(INST_SCRIPT)/.exists

	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)

EXE_FILES = scripts/unidump scripts/unilabel scripts/unirest scripts/unilib scripts/uniresume scripts/unitoc scripts/uniflush scripts/unilist scripts/unisched scripts/unihist scripts/uniproper scripts/unistat scripts/unihrest

FIXIN = $(PERLRUN) "-MExtUtils::MY" \
    -e "MY->fixin(shift)"

pure_all :: $(INST_SCRIPT)/uniproper $(INST_SCRIPT)/unisched $(INST_SCRIPT)/unitoc $(INST_SCRIPT)/uniresume $(INST_SCRIPT)/unihist $(INST_SCRIPT)/unilist $(INST_SCRIPT)/unidump $(INST_SCRIPT)/unistat $(INST_SCRIPT)/uniflush $(INST_SCRIPT)/unilib $(INST_SCRIPT)/unihrest $(INST_SCRIPT)/unirest $(INST_SCRIPT)/unilabel
	@$(NOOP)

realclean ::
	rm -f $(INST_SCRIPT)/uniproper $(INST_SCRIPT)/unisched $(INST_SCRIPT)/unitoc $(INST_SCRIPT)/uniresume $(INST_SCRIPT)/unihist $(INST_SCRIPT)/unilist $(INST_SCRIPT)/unidump $(INST_SCRIPT)/unistat $(INST_SCRIPT)/uniflush $(INST_SCRIPT)/unilib $(INST_SCRIPT)/unihrest $(INST_SCRIPT)/unirest $(INST_SCRIPT)/unilabel

$(INST_SCRIPT)/uniproper: scripts/uniproper Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/uniproper
	cp scripts/uniproper $(INST_SCRIPT)/uniproper
	$(FIXIN) $(INST_SCRIPT)/uniproper
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/uniproper

$(INST_SCRIPT)/unisched: scripts/unisched Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/unisched
	cp scripts/unisched $(INST_SCRIPT)/unisched
	$(FIXIN) $(INST_SCRIPT)/unisched
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/unisched

$(INST_SCRIPT)/unitoc: scripts/unitoc Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/unitoc
	cp scripts/unitoc $(INST_SCRIPT)/unitoc
	$(FIXIN) $(INST_SCRIPT)/unitoc
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/unitoc

$(INST_SCRIPT)/uniresume: scripts/uniresume Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/uniresume
	cp scripts/uniresume $(INST_SCRIPT)/uniresume
	$(FIXIN) $(INST_SCRIPT)/uniresume
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/uniresume

$(INST_SCRIPT)/unihist: scripts/unihist Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/unihist
	cp scripts/unihist $(INST_SCRIPT)/unihist
	$(FIXIN) $(INST_SCRIPT)/unihist
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/unihist

$(INST_SCRIPT)/unilist: scripts/unilist Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/unilist
	cp scripts/unilist $(INST_SCRIPT)/unilist
	$(FIXIN) $(INST_SCRIPT)/unilist
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/unilist

$(INST_SCRIPT)/unidump: scripts/unidump Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/unidump
	cp scripts/unidump $(INST_SCRIPT)/unidump
	$(FIXIN) $(INST_SCRIPT)/unidump
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/unidump

$(INST_SCRIPT)/unistat: scripts/unistat Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/unistat
	cp scripts/unistat $(INST_SCRIPT)/unistat
	$(FIXIN) $(INST_SCRIPT)/unistat
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/unistat

$(INST_SCRIPT)/uniflush: scripts/uniflush Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/uniflush
	cp scripts/uniflush $(INST_SCRIPT)/uniflush
	$(FIXIN) $(INST_SCRIPT)/uniflush
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/uniflush

$(INST_SCRIPT)/unilib: scripts/unilib Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/unilib
	cp scripts/unilib $(INST_SCRIPT)/unilib
	$(FIXIN) $(INST_SCRIPT)/unilib
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/unilib

$(INST_SCRIPT)/unihrest: scripts/unihrest Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/unihrest
	cp scripts/unihrest $(INST_SCRIPT)/unihrest
	$(FIXIN) $(INST_SCRIPT)/unihrest
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/unihrest

$(INST_SCRIPT)/unirest: scripts/unirest Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/unirest
	cp scripts/unirest $(INST_SCRIPT)/unirest
	$(FIXIN) $(INST_SCRIPT)/unirest
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/unirest

$(INST_SCRIPT)/unilabel: scripts/unilabel Makefile $(INST_SCRIPT)/.exists
	@rm -f $(INST_SCRIPT)/unilabel
	cp scripts/unilabel $(INST_SCRIPT)/unilabel
	$(FIXIN) $(INST_SCRIPT)/unilabel
	-@$(CHMOD) $(PERM_RWX) $(INST_SCRIPT)/unilabel


# --- MakeMaker subdirs section:

# none

# --- MakeMaker clean section:

# Delete temporary files but do not touch installed files. We don't delete
# the Makefile here so a later make realclean still has a makefile to use.

clean ::
	-rm -rf ./blib $(MAKE_APERL_FILE) $(INST_ARCHAUTODIR)/extralibs.all perlmain.c tmon.out mon.out so_locations pm_to_blib *$(OBJ_EXT) *$(LIB_EXT) perl.exe perl perl$(EXE_EXT) $(BOOTSTRAP) $(BASEEXT).bso $(BASEEXT).def lib$(BASEEXT).def $(BASEEXT).exp $(BASEEXT).x core core.*perl.*.? *perl.core
	-mv Makefile Makefile.old $(DEV_NULL)


# --- MakeMaker realclean section:

# Delete temporary files (via clean) and also delete installed files
realclean purge ::  clean
	rm -rf $(INST_AUTODIR) $(INST_ARCHAUTODIR)
	rm -rf $(DISTVNAME)
	rm -f  blib/lib/Unidump/GtarDumper.pm blib/lib/Unidump/Dumper.pm
	rm -f blib/lib/Unidump/XfsDumper.pm blib/lib/Unidump/Tape.pm blib/lib/Unidump/Config.pm
	rm -f blib/lib/Unidump/Units.pm blib/lib/Unidump/StarDumper.pm
	rm -f blib/lib/Unidump/Strategy.pm blib/lib/Unidump/Logger.pm
	rm -f blib/lib/Unidump/Tapelib.pm blib/lib/Unidump.pm blib/lib/Unidump/History.pm
	rm -f blib/lib/Unidump/Ext2Dumper.pm blib/lib/Unidump/GenericDumper.pm
	rm -rf Makefile Makefile.old


# --- MakeMaker dist_basics section:
distclean :: realclean distcheck
	$(NOECHO) $(NOOP)

distcheck :
	$(PERLRUN) "-MExtUtils::Manifest=fullcheck" -e fullcheck

skipcheck :
	$(PERLRUN) "-MExtUtils::Manifest=skipcheck" -e skipcheck

manifest :
	$(PERLRUN) "-MExtUtils::Manifest=mkmanifest" -e mkmanifest

veryclean : realclean
	$(RM_F) *~ *.orig */*~ */*.orig



# --- MakeMaker dist_core section:

dist : $(DIST_DEFAULT)
	@$(PERL) -le 'print "Warning: Makefile possibly out of date with $$vf" if ' \
	    -e '-e ($$vf="$(VERSION_FROM)") and -M $$vf < -M "Makefile";'

tardist : $(DISTVNAME).tar$(SUFFIX)

zipdist : $(DISTVNAME).zip

$(DISTVNAME).tar$(SUFFIX) : distdir
	$(PREOP)
	$(TO_UNIX)
	$(TAR) $(TARFLAGS) $(DISTVNAME).tar $(DISTVNAME)
	$(RM_RF) $(DISTVNAME)
	$(COMPRESS) $(DISTVNAME).tar
	$(POSTOP)

$(DISTVNAME).zip : distdir
	$(PREOP)
	$(ZIP) $(ZIPFLAGS) $(DISTVNAME).zip $(DISTVNAME)
	$(RM_RF) $(DISTVNAME)
	$(POSTOP)

uutardist : $(DISTVNAME).tar$(SUFFIX)
	uuencode $(DISTVNAME).tar$(SUFFIX) \
		$(DISTVNAME).tar$(SUFFIX) > \
		$(DISTVNAME).tar$(SUFFIX)_uu

shdist : distdir
	$(PREOP)
	$(SHAR) $(DISTVNAME) > $(DISTVNAME).shar
	$(RM_RF) $(DISTVNAME)
	$(POSTOP)


# --- MakeMaker dist_dir section:
distdir :
	$(RM_RF) $(DISTVNAME)
	$(PERLRUN) "-MExtUtils::Manifest=manicopy,maniread" \
		-e "manicopy(maniread(),'$(DISTVNAME)', '$(DIST_CP)');"



# --- MakeMaker dist_test section:

disttest : distdir
	cd $(DISTVNAME) && $(ABSPERLRUN) Makefile.PL
	cd $(DISTVNAME) && $(MAKE) $(PASTHRU)
	cd $(DISTVNAME) && $(MAKE) test $(PASTHRU)


# --- MakeMaker dist_ci section:

ci :
	$(PERLRUN) "-MExtUtils::Manifest=maniread" \
		-e "@all = keys %{ maniread() };" \
		-e 'print("Executing $(CI) @all\n"); system("$(CI) @all");' \
		-e 'print("Executing $(RCS_LABEL) ...\n"); system("$(RCS_LABEL) @all");'


# --- MakeMaker install section:

install :: all pure_install doc_install

install_perl :: all pure_perl_install doc_perl_install

install_site :: all pure_site_install doc_site_install

install_vendor :: all pure_vendor_install doc_vendor_install

pure_install :: pure_$(INSTALLDIRS)_install

doc_install :: doc_$(INSTALLDIRS)_install

pure__install : pure_site_install
	@echo INSTALLDIRS not defined, defaulting to INSTALLDIRS=site

doc__install : doc_site_install
	@echo INSTALLDIRS not defined, defaulting to INSTALLDIRS=site

pure_perl_install ::
	@umask 022; $(MOD_INSTALL) \
		read $(PERL_ARCHLIB)/auto/$(FULLEXT)/.packlist \
		write $(INSTALLARCHLIB)/auto/$(FULLEXT)/.packlist \
		$(INST_LIB) $(INSTALLPRIVLIB) \
		$(INST_ARCHLIB) $(INSTALLARCHLIB) \
		$(INST_BIN) $(INSTALLBIN) \
		$(INST_SCRIPT) $(INSTALLSCRIPT) \
		$(INST_MAN1DIR) $(INSTALLMAN1DIR) \
		$(INST_MAN3DIR) $(INSTALLMAN3DIR)
	@$(WARN_IF_OLD_PACKLIST) \
		$(SITEARCHEXP)/auto/$(FULLEXT)


pure_site_install ::
	@umask 02; $(MOD_INSTALL) \
		read $(SITEARCHEXP)/auto/$(FULLEXT)/.packlist \
		write $(INSTALLSITEARCH)/auto/$(FULLEXT)/.packlist \
		$(INST_LIB) $(INSTALLSITELIB) \
		$(INST_ARCHLIB) $(INSTALLSITEARCH) \
		$(INST_BIN) $(INSTALLSITEBIN) \
		$(INST_SCRIPT) $(INSTALLSCRIPT) \
		$(INST_MAN1DIR) $(INSTALLSITEMAN1DIR) \
		$(INST_MAN3DIR) $(INSTALLSITEMAN3DIR)
	@$(WARN_IF_OLD_PACKLIST) \
		$(PERL_ARCHLIB)/auto/$(FULLEXT)

pure_vendor_install ::
	@umask 022; $(MOD_INSTALL) \
		$(INST_LIB) $(INSTALLVENDORLIB) \
		$(INST_ARCHLIB) $(INSTALLVENDORARCH) \
		$(INST_BIN) $(INSTALLVENDORBIN) \
		$(INST_SCRIPT) $(INSTALLSCRIPT) \
		$(INST_MAN1DIR) $(INSTALLVENDORMAN1DIR) \
		$(INST_MAN3DIR) $(INSTALLVENDORMAN3DIR)

doc_perl_install ::
	@echo Appending installation info to $(INSTALLARCHLIB)/perllocal.pod
	-@umask 022; $(MKPATH) $(INSTALLARCHLIB)
	-@umask 022; $(DOC_INSTALL) \
		"Module" "$(NAME)" \
		"installed into" "$(INSTALLPRIVLIB)" \
		LINKTYPE "$(LINKTYPE)" \
		VERSION "$(VERSION)" \
		EXE_FILES "$(EXE_FILES)" \
		>> $(INSTALLARCHLIB)/perllocal.pod

doc_site_install ::
	@echo Appending installation info to $(INSTALLSITEARCH)/perllocal.pod
	-@umask 02; $(MKPATH) $(INSTALLSITEARCH)
	-@umask 02; $(DOC_INSTALL) \
		"Module" "$(NAME)" \
		"installed into" "$(INSTALLSITELIB)" \
		LINKTYPE "$(LINKTYPE)" \
		VERSION "$(VERSION)" \
		EXE_FILES "$(EXE_FILES)" \
		>> $(INSTALLSITEARCH)/perllocal.pod

doc_vendor_install ::


uninstall :: uninstall_from_$(INSTALLDIRS)dirs

uninstall_from_perldirs ::
	@$(UNINSTALL) $(PERL_ARCHLIB)/auto/$(FULLEXT)/.packlist

uninstall_from_sitedirs ::
	@$(UNINSTALL) $(SITEARCHEXP)/auto/$(FULLEXT)/.packlist


# --- MakeMaker force section:
# Phony target to force checking subdirectories.
FORCE:
	@$(NOOP)


# --- MakeMaker perldepend section:


# --- MakeMaker makefile section:

# We take a very conservative approach here, but it\'s worth it.
# We move Makefile to Makefile.old here to avoid gnu make looping.
Makefile : Makefile.PL $(CONFIGDEP)
	@echo "Makefile out-of-date with respect to $?"
	@echo "Cleaning current config before rebuilding Makefile..."
	-@$(RM_F) Makefile.old
	-@$(MV) Makefile Makefile.old
	-$(MAKE) -f Makefile.old clean $(DEV_NULL) || $(NOOP)
	$(PERLRUN) Makefile.PL "INSTALLDIRS=vendor"
	@echo "==> Your Makefile has been rebuilt. <=="
	@echo "==> Please rerun the make command.  <=="
	false



# --- MakeMaker staticmake section:

# --- MakeMaker makeaperl section ---
MAP_TARGET    = perl
FULLPERL      = /usr/bin/perl

$(MAP_TARGET) :: static $(MAKE_APERL_FILE)
	$(MAKE) -f $(MAKE_APERL_FILE) $@

$(MAKE_APERL_FILE) : $(FIRST_MAKEFILE)
	@echo Writing \"$(MAKE_APERL_FILE)\" for this $(MAP_TARGET)
	@$(PERLRUNINST) \
		Makefile.PL DIR= \
		MAKEFILE=$(MAKE_APERL_FILE) LINKTYPE=static \
		MAKEAPERL=1 NORECURS=1 CCCDLFLAGS= \
		INSTALLDIRS=vendor


# --- MakeMaker test section:

TEST_VERBOSE=0
TEST_TYPE=test_$(LINKTYPE)
TEST_FILE = test.pl
TEST_FILES = t/*.t
TESTDB_SW = -d

testdb :: testdb_$(LINKTYPE)

test :: $(TEST_TYPE)

test_dynamic :: pure_all
	PERL_DL_NONLAZY=1 $(FULLPERLRUN) "-MExtUtils::Command::MM" "-e" "test_harness($(TEST_VERBOSE), '$(INST_LIB)', '$(INST_ARCHLIB)')" $(TEST_FILES)

testdb_dynamic :: pure_all
	PERL_DL_NONLAZY=1 $(FULLPERLRUN) $(TESTDB_SW) "-I$(INST_LIB)" "-I$(INST_ARCHLIB)" $(TEST_FILE)

test_ : test_dynamic

test_static :: test_dynamic
testdb_static :: testdb_dynamic


# --- MakeMaker ppd section:
# Creates a PPD (Perl Package Description) for a binary distribution.
ppd:
	@$(PERL) -e "print qq{<SOFTPKG NAME=\"$(DISTNAME)\" VERSION=\"0,5,0,0\">\n\t<TITLE>$(DISTNAME)</TITLE>\n\t<ABSTRACT>Unidump - Perl extension for scheduled backup</ABSTRACT>\n\t<AUTHOR>Joerg Ungethuem &lt;joerg.ungethuem\@enersim.de&gt;</AUTHOR>\n}" > $(DISTNAME).ppd
	@$(PERL) -e "print qq{\t<IMPLEMENTATION>\n\t\t<DEPENDENCY NAME=\"AppConfig\" VERSION=\"1,5,0,0\" />\n\t\t<DEPENDENCY NAME=\"Class-Accessor\" VERSION=\"0,0,0,0\" />\n\t\t<DEPENDENCY NAME=\"Data-ShowTable\" VERSION=\"0,0,0,0\" />\n\t\t<DEPENDENCY NAME=\"Date-Parse\" VERSION=\"0,0,0,0\" />\n\t\t<DEPENDENCY NAME=\"File-Remove\" VERSION=\"0,0,0,0\" />\n\t\t<DEPENDENCY NAME=\"Unix-Syslog\" VERSION=\"0,9,0,0\" />\n}" >> $(DISTNAME).ppd
	@$(PERL) -e "print qq{\t\t<OS NAME=\"$(OSNAME)\" />\n\t\t<ARCHITECTURE NAME=\"i386-linux-thread-multi\" />\n\t\t<CODEBASE HREF=\"\" />\n\t</IMPLEMENTATION>\n</SOFTPKG>\n}" >> $(DISTNAME).ppd

# --- MakeMaker pm_to_blib section:

pm_to_blib: $(TO_INST_PM)
	@$(PERLRUNINST) "-MExtUtils::Install" \
	-e "pm_to_blib({qw{Unidump/Dumper.pm blib/lib/Unidump/Dumper.pm Unidump/GtarDumper.pm blib/lib/Unidump/GtarDumper.pm Unidump/Tape.pm blib/lib/Unidump/Tape.pm Unidump/XfsDumper.pm blib/lib/Unidump/XfsDumper.pm}},'$(INST_LIB)/auto','$(PM_FILTER)')"
	@$(PERLRUNINST) "-MExtUtils::Install" \
	-e "pm_to_blib({qw{Unidump/Config.pm blib/lib/Unidump/Config.pm Unidump/Units.pm blib/lib/Unidump/Units.pm Unidump/StarDumper.pm blib/lib/Unidump/StarDumper.pm Unidump/Strategy.pm blib/lib/Unidump/Strategy.pm}},'$(INST_LIB)/auto','$(PM_FILTER)')"
	@$(PERLRUNINST) "-MExtUtils::Install" \
	-e "pm_to_blib({qw{Unidump/Logger.pm blib/lib/Unidump/Logger.pm Unidump/Tapelib.pm blib/lib/Unidump/Tapelib.pm Unidump.pm blib/lib/Unidump.pm Unidump/Ext2Dumper.pm blib/lib/Unidump/Ext2Dumper.pm}},'$(INST_LIB)/auto','$(PM_FILTER)')"
	@$(PERLRUNINST) "-MExtUtils::Install" \
	-e "pm_to_blib({qw{Unidump/History.pm blib/lib/Unidump/History.pm Unidump/GenericDumper.pm blib/lib/Unidump/GenericDumper.pm}},'$(INST_LIB)/auto','$(PM_FILTER)')"
	@$(TOUCH) $@

# --- MakeMaker selfdocument section:


# --- MakeMaker postamble section:


# End.
