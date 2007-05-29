# 	$Id: Units.pm,v 1.2 2003/09/08 07:14:37 thorsten Exp $	
package Unidump::Units;
use POSIX;
use strict;
use Unidump::Logger qw(logmessage logmessage_debug);
use vars qw(@ISA @EXPORT @EXPORT_OK %EXPORT_TAGS $VERSION);
use Exporter;
$VERSION = do{my @r = split(" ",qq$Revision: 1.2 $ );$r[1];};
@ISA = qw(Exporter);
#use Data::Dumper;

@EXPORT = qw();
@EXPORT_OK = qw(convert);
%EXPORT_TAGS = (all => [@EXPORT_OK]);

sub convert {
  logmessage_debug("Units::convert: ", @_);
  my($val, $new_unit) = @_;
#  my $old_unit;
#  $val =~ s/\s*([kMGT])\s*$// and $old_unit = $1;
#  $val *= evalunit($old_unit);
  $val =~ s/\s*([kMGT])\s*$//;
  $val *= evalunit($1);
  $val /= evalunit($new_unit);
  $val .= $new_unit if defined $new_unit;
  return $val;
}

sub evalunit {
  logmessage_debug("Units::evalunit: ", grep {$_ ? $_ : ''} @_);
  for(shift) {
    defined or return 1;
    /^T$/ and return 1024**4;
    /^G$/ and return 1024**3;
    /^M$/ and return 1024**2;
    /^k$/ and return 1024;
    die "unknown unit: $_";
  }
}

1;

__END__

=head1 NAME
  
  Units -- a simple tool to convert base2 units

=head1 SYNOPSIS

  $int    = convert($value);
  $newval = convert($value, $newunit);

=head1 DESCRIPTION

  B<convert> evaluates an unit based value into a new unit or into a
  bare integer. Known units are: k (1024), M (1024k), G (1024M), T
  (1024G). 
  
