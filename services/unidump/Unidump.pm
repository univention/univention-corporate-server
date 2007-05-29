package Unidump;
# 	$Id: Unidump.pm,v 1.2 2003/09/08 07:14:36 thorsten Exp $	
use strict;
use vars qw($VERSION @ISA @EXPORT @EXPORT_OK %EXPORT_TAGS);

require Exporter;
@ISA = qw(Exporter);
$VERSION = do{my @r = split(" ",qq$Revision: 1.2 $ );$r[1];};

# Items to export into callers namespace by default. Note: do not export
# names by default without a very good reason. Use EXPORT_OK instead.
# Do not simply export all your public functions/methods/constants.

# This allows declaration	use Unidump ':all';
# If you do not need this, moving things directly into @EXPORT or @EXPORT_OK
# will save memory.
%EXPORT_TAGS = ( 'all' => [ qw() ] );
@EXPORT_OK = ( @{ $EXPORT_TAGS{'all'} } );
@EXPORT = qw();

1;
__END__

=head1 NAME

  Unidump - Perl extension for scheduled backup and restore

=head1 SYNOPSIS

  use Unidump::Dumper;
  use Unidump::Ext2Dumper;
  use Unidump::GenericDumper;
  use Unidump::GtarDumper;
  use Unidump::StarDumper;
  use Unidump::XfsDumper;
  use Unidump::History;
  use Unidump::Logger;
  use Unidump::Strategy;
  use Unidump::Tape;
  use Unidump::Tapelib;
  use Unidump::Units;

=head1 DESCRIPTION

  This is just a dummy module. See one of the Unidump::* modules instead.

=head1 AUTHOR

  Joerg Ungethuem <joerg.ungethuem@enersim.de>

=head1 SEE ALSO

perl(1).

