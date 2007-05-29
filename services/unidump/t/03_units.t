#!/usr/bin/perl
# 	$Id: 03_units.t,v 1.2 2003/09/08 07:14:37 thorsten Exp $	

use Test;
use English;
use POSIX;
use Unidump::Units qw(:all);

BEGIN { plan tests => 7; }

$WARNING = 0;

# test 1..4
$n = int(100*rand())+1; ok(convert("${n}k"), $n*1024);
$n = int(100*rand())+1; ok(convert("${n}M"), $n*1024**2);
$n = int(100*rand())+1; ok(convert("${n}G"), $n*1024**3);
$n = int(100*rand())+1; ok(convert("${n}T"), $n*1024**4);


# test 5..7
$n = int(100*rand())+1; ok(convert("${n}M", "k"), $n*1024 . "k");
$n = int(100*rand())+1; ok(convert("${n}G", "M"), $n*1024 . "M");
$n = int(100*rand())+1; ok(convert("${n}T", "G"), $n*1024 . "G");

