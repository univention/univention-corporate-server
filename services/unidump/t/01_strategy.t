#!/usr/bin/perl
# 	$Id: 01_strategy.t,v 1.2 2003/09/08 07:14:37 thorsten Exp $	

use Test;
use English;
use Unidump::Strategy qw(:all);

BEGIN { plan tests => 81; }

$WARNING = 0;

# test 1..2
ok(nextdump(), 0);		# 0 argument(s) scalar context
@exp = (0, undef);
@get = nextdump();		# 0 argument(s) array context
ok("@get", "@exp");	    

# test 3..4
ok(nextdump('foo'), 0);		# 1 argument(s) scalar context
@exp = (0, 'foo');
@get = nextdump('foo');
ok("@get", "@exp");		# 1 argument(s) array context


$mo = 1014591600;		# monday, 2002-02-25
$tu = $mo + 24*3600;
$we = $mo + 2*24*3600;
$th = $mo + 3*24*3600;
$fr1= $mo + 4*24*3600;
$fr2= $mo + 11*24*3600;
$fr3= $mo + 18*24*3600;
$fr4= $mo + 25*24*3600;
$fr5= $mo + 32*24*3600;

# test 5..13
ok(nextdump('simple', "", $mo), 1); # simple strat. scalar context
ok(nextdump('simple', "", $tu), 1); # simple strat. scalar context
ok(nextdump('simple', "", $we), 1); # simple strat. scalar context
ok(nextdump('simple', "", $th), 1); # simple strat. scalar context
ok(nextdump('simple', "", $fr1), 0); # simple strat. scalar context
ok(nextdump('simple', "", $fr2), 0); # simple strat. scalar context
ok(nextdump('simple', "", $fr3), 0); # simple strat. scalar context
ok(nextdump('simple', "", $fr4), 0); # simple strat. scalar context
ok(nextdump('simple', "", $fr5), 0); # simple strat. scalar context


# test 14 .. 22
@exp = (1, 'Monday'); @get = nextdump('simple', "", $mo); ok("@get", "@exp");
@exp = (1, 'Tuesday'); @get = nextdump('simple', "", $tu); ok("@get", "@exp");
@exp = (1, 'Wednesday'); @get = nextdump('simple', "", $we); ok("@get", "@exp");
@exp = (1, 'Thursday'); @get = nextdump('simple', "", $th); ok("@get", "@exp");
@exp = (0, 'Friday_week1'); @get = nextdump('simple', "", $fr1); ok("@get", "@exp");
@exp = (0, 'Friday_week2'); @get = nextdump('simple', "", $fr2); ok("@get", "@exp");
@exp = (0, 'Friday_week3'); @get = nextdump('simple', "", $fr3); ok("@get", "@exp");
@exp = (0, 'Friday_week4'); @get = nextdump('simple', "", $fr4); ok("@get", "@exp");
@exp = (0, 'Friday_week5'); @get = nextdump('simple', "", $fr5); ok("@get", "@exp");



# test 23..27
ok(nextdump('simple_mo', "", $mo), 0); # simple_mo strat. scalar context
ok(nextdump('simple_mo', "", $tu), 1); # simple_mo strat. scalar context
ok(nextdump('simple_mo', "", $we), 1); # simple_mo strat. scalar context
ok(nextdump('simple_mo', "", $th), 1); # simple_mo strat. scalar context
ok(nextdump('simple_mo', "", $fr1), 1); # simple_mo strat. scalar context


# test 28..32
@exp = (0, 'Monday_week4'); @get = nextdump('simple_mo', "", $mo); ok("@get", "@exp");
@exp = (1, 'Tuesday'); @get = nextdump('simple_mo', "", $tu); ok("@get", "@exp");
@exp = (1, 'Wednesday'); @get = nextdump('simple_mo', "", $we); ok("@get", "@exp");
@exp = (1, 'Thursday'); @get = nextdump('simple_mo', "", $th); ok("@get", "@exp");
@exp = (1, 'Friday'); @get = nextdump('simple_mo', "", $fr1); ok("@get", "@exp");


# test 33..41
ok(nextdump('simple', "+3", $mo), 4); # simple strat. scalar context
ok(nextdump('simple', "+5", $tu), 6); # simple strat. scalar context
ok(nextdump('simple', "1", $fr1), 0); # simple strat. scalar context
ok(nextdump('simple', "2", $fr1), 1); # simple strat. scalar context
ok(nextdump('simple', "2", $fr2), 0); # simple strat. scalar context
ok(nextdump('simple', "2", $fr3), 1); # simple strat. scalar context
ok(nextdump('simple', "2+1", $fr1), 2); # simple strat. scalar context
ok(nextdump('simple', "2+1", $fr2), 1); # simple strat. scalar context
ok(nextdump('simple', "2+1", $fr3), 2); # simple strat. scalar context


# test 42..50
ok(nextdump('distrib', "", $mo), 1); # distrib strat. scalar context
ok(nextdump('distrib', "", $tu), 1); # distrib strat. scalar context
ok(nextdump('distrib', "", $we), 1); # distrib strat. scalar context
ok(nextdump('distrib', "", $th), 1); # distrib strat. scalar context
ok(nextdump('distrib', "", $fr1), 0); # distrib strat. scalar context
ok(nextdump('distrib', "", $fr2), 0); # distrib strat. scalar context
ok(nextdump('distrib', "", $fr3), 0); # distrib strat. scalar context
ok(nextdump('distrib', "", $fr4), 0); # distrib strat. scalar context
ok(nextdump('distrib', "", $fr5), 0); # distrib strat. scalar context

# test 51..59
@exp = (1, 'Monday_week4'); @get = nextdump('distrib', "", $mo); ok("@get", "@exp");
@exp = (1, 'Tuesday_week4'); @get = nextdump('distrib', "", $tu); ok("@get", "@exp");
@exp = (1, 'Wednesday_week4'); @get = nextdump('distrib', "", $we); ok("@get", "@exp");
@exp = (1, 'Thursday_week4'); @get = nextdump('distrib', "", $th); ok("@get", "@exp");
@exp = (0, 'Friday_week1'); @get = nextdump('distrib', "", $fr1); ok("@get", "@exp");
@exp = (0, 'Friday_week2'); @get = nextdump('distrib', "", $fr2); ok("@get", "@exp");
@exp = (0, 'Friday_week3'); @get = nextdump('distrib', "", $fr3); ok("@get", "@exp");
@exp = (0, 'Friday_week4'); @get = nextdump('distrib', "", $fr4); ok("@get", "@exp");
@exp = (0, 'Friday_week5'); @get = nextdump('distrib', "", $fr5); ok("@get", "@exp");


# test 60..68
@exp = (1, 'Monday_week4'); @get = nextdump('distrib', "Tuesday", $mo); ok("@get", "@exp");
@exp = (0, 'Tuesday_week4'); @get = nextdump('distrib', "Tuesday", $tu); ok("@get", "@exp");
@exp = (1, 'Wednesday_week4'); @get = nextdump('distrib', "Tuesday", $we); ok("@get", "@exp");
@exp = (1, 'Thursday_week4'); @get = nextdump('distrib', "Tuesday", $th); ok("@get", "@exp");
@exp = (1, 'Friday_week1'); @get = nextdump('distrib', "Tuesday", $fr1); ok("@get", "@exp");
@exp = (1, 'Friday_week2'); @get = nextdump('distrib', "Tuesday", $fr2); ok("@get", "@exp");
@exp = (1, 'Friday_week3'); @get = nextdump('distrib', "Tuesday", $fr3); ok("@get", "@exp");
@exp = (1, 'Friday_week4'); @get = nextdump('distrib', "Tuesday", $fr4); ok("@get", "@exp");
@exp = (1, 'Friday_week5'); @get = nextdump('distrib', "Tuesday", $fr5); ok("@get", "@exp");


# test 69..76
@exp = (3, 'Monday_week4'); @get = nextdump('distrib', "Tuesday+2", $mo); ok("@get", "@exp");
@exp = (2, 'Tuesday_week4'); @get = nextdump('distrib', "Tuesday+2", $tu); ok("@get", "@exp");
@exp = (3, 'Wednesday_week4'); @get = nextdump('distrib', "Tuesday+2", $we); ok("@get", "@exp");
@exp = (4, 'Friday_week1'); @get = nextdump('distrib', "Friday2+3", $fr1); ok("@get", "@exp");
@exp = (3, 'Friday_week2'); @get = nextdump('distrib', "Friday2+3", $fr2); ok("@get", "@exp");
@exp = (4, 'Friday_week3'); @get = nextdump('distrib', "Friday2+3", $fr3); ok("@get", "@exp");
@exp = (4, 'Friday_week4'); @get = nextdump('distrib', "Friday2+3", $fr4); ok("@get", "@exp");
@exp = (4, 'Friday_week5'); @get = nextdump('distrib', "Friday2+3", $fr5); ok("@get", "@exp");


# test 77..81
@exp = (0, 'archiv_foo'); @get = nextdump('archiv_foo'); ok("@get", "@exp");
@exp = (0, 'archiv_foo2'); @get = nextdump('archiv_foo2'); ok("@get", "@exp");
@exp = (0, 'archiv_foo_2'); @get = nextdump('archiv_foo_2'); ok("@get", "@exp");
@exp = (2, 'archiv_foo'); @get = nextdump('archiv_foo', "+2"); ok("@get", "@exp");
@exp = (2, 'archiv_foo_7'); @get = nextdump('archiv_foo_7', "+2"); ok("@get", "@exp");
