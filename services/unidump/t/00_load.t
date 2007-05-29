#!/usr/bin/perl
# 	$Id: 00_load.t,v 1.2 2003/09/08 07:14:37 thorsten Exp $	
use Test;

BEGIN {
  @modules = qw(Unidump Unidump::Config Unidump::Dumper 
	      Unidump::Ext2Dumper Unidump::GenericDumper
	      Unidump::GtarDumper Unidump::History
	      Unidump::Logger Unidump::StarDumper
	      Unidump::Strategy Unidump::Tapelib
	      Unidump::Tape Unidump::Units
	      Unidump::XfsDumper);

  plan tests => scalar @modules;
}


foreach (@modules) {

	eval "use $_";
	ok("$@", "");

}

exit 0;
