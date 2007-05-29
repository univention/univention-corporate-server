# 	$Id: Dumper.pm,v 1.2 2003/09/08 07:14:37 thorsten Exp $	
package Unidump::Dumper;
use strict;
use vars qw($VERSION);
use Unidump::GenericDumper;
use Unidump::Ext2Dumper;
use Unidump::XfsDumper;
use Unidump::GtarDumper;
use Unidump::StarDumper;

$VERSION = do{ qq$Revision: 1.2 $ =~ /\d+\.\d+/, $&; };

sub new {
  my $class = shift;
  my $self = shift;
 Unidump::Logger::logmessage_debug("creating new dumper object");
 SWITCH: for($self->{dumper}) {
   /^(ext2)?dump$/ and 
     $self = Unidump::Ext2Dumper->new($self), last SWITCH;
   /^xfsdump$/ and 
     $self = Unidump::XfsDumper->new($self), last SWITCH;
   /^star$/ and 
     $self = Unidump::StarDumper->new($self), last SWITCH;
   /^gtar$/ and 
     $self = Unidump::GtarDumper->new($self), last SWITCH;
   $self = Unidump::GenericDumper->new($self), last SWITCH;
 }
  return $self;
}

1;
