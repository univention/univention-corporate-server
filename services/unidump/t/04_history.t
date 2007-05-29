#!/usr/bin/perl
# 	$Id: 04_history.t,v 1.2 2003/09/08 07:14:37 thorsten Exp $	

use Test;
use English;
use POSIX;
use Unidump::History qw(:all);

BEGIN { 
  do {
    $dir = POSIX::tmpnam;
  } until(mkdir $dir, 0700);
  plan tests => 64;
}
END {
  unlink <$dir/*>;
  rmdir $dir;
}

$WARNING = 0;

$Unidump::History::historydir  = $dir;

# test 1..2
ok(Unidump::History::historyfile, "$dir/history.txt");
ok(-f "$dir/history.txt");

$d = [["3cad4689-7be", "/",3,"Tuesday",2,
       "f1dd83e8-ad26-49a8-b4d4-89245d038f5b",
       1017988909,'ext2dump,z,10k'],

      ["3cad476d-7c7", "/home", 3, "Monday", "-",
       "/var/lib/unidump/hd/3cad476d-7c7.dump",
       1017989051, 'xfsdump,gzip,64k']];

hist_insert({dumpid => $d->[0][0],
	     directory => $d->[0][1],
	     dumplevel => $d->[0][2],
	     tapelabel => $d->[0][3],
	     tapeidx => $d->[0][4],
	     tapeid => $d->[0][5],
	     starttime => $d->[0][6],
	     options => $d->[0][7],});
hist_insert(@{$d->[1]});

# test 3
eval {
  open(F, "$dir/history.txt");
  @h = sort <F>;
  chomp @h;
  close F;
};
ok(!$@);

# test 4..5
ok($h[0], join(" ", @{$d->[0]}));
ok($h[1], join(" ", @{$d->[1]}));

# test 6..7
ok(join(" ", $d->[0][0], hist_get($d->[0][0])), join(" ", @{$d->[0]}));
ok(join(" ", $d->[1][0], hist_get($d->[1][0])), join(" ", @{$d->[1]}));

# test 8
ok(join(" ", sort {$a cmp $b} hist_get), join(" ", $d->[0][0], $d->[1][0]));

# test 9..22
ok(hist_get_directory($d->[0][0]), $d->[0][1]);
ok(hist_get_dumplevel($d->[0][0]), $d->[0][2]);
ok(hist_get_tapelabel($d->[0][0]), $d->[0][3]);
ok(hist_get_tapeidx($d->[0][0]), $d->[0][4]);
ok(hist_get_tapeid($d->[0][0]), $d->[0][5]);
ok(hist_get_starttime($d->[0][0]), $d->[0][6]);
ok(hist_get_options($d->[0][0]), $d->[0][7]);

ok(hist_get_directory($d->[1][0]), $d->[1][1]);
ok(hist_get_dumplevel($d->[1][0]), $d->[1][2]);
ok(hist_get_tapelabel($d->[1][0]), $d->[1][3]);
ok(hist_get_tapeidx($d->[1][0]), $d->[1][4]);
ok(hist_get_tapeid($d->[1][0]), $d->[1][5]);
ok(hist_get_starttime($d->[1][0]), $d->[1][6]);
ok(hist_get_options($d->[1][0]), $d->[1][7]);

# test 23..25
ok(hist_get, 2); 
ok(hist_dump_is_obsolete($d->[0][0]), 0);
ok(hist_dump_is_obsolete($d->[1][0]), 0);

# test 26
# make dump 0 obsolete (by writing a new dump on this tape)
@d = ("3cad6189-edd", "/xyz", 0, "archiv", 1, 
      $d->[0][5], $d->[0][6]+1, 'xfsdump,z,10k');
hist_insert(@d);
ok(hist_dump_is_obsolete($d->[0][0]), 1);

# test 27
# make dump 1 obsolete (by writing a new dump on a similar-labeled tape)
@d = ("3cad6c7c-113c", "/bar", 9, $d->[1][3], 2,
      "263e8579-42be-409b-bb7d-909924c44802",
      $d->[1][6]+5, 'xfsdump,z,10k');
hist_insert(@d);
ok(hist_dump_is_obsolete($d->[1][0]), 1);

# test 28..30
hist_delete($d->[0][0]); ok(hist_get, 3);
hist_delete($d->[1][0]); ok(hist_get, 2); 
hist_delete("3cad6c7c-113c"); 
ok(hist_get, 2); # don't delete as it's not obsolete


# generate a bunch of history entries
@tl  = qw(Monday Tuesday Wednesday Thursday Friday_week1 
	  Friday_week2 Friday_week3 Friday_week4 Friday_week5);
@dl  = qw(1 1 1 1 0 0 0 0 0);
@tid = qw(eba26e5f-9c82-4300-b79c-7150243fda4d
	  43e99595-8a19-43a4-b0f2-549b55004a00
	  5a6776ca-9dd2-4908-844b-1c80fa4daca5
	  ab80e32e-2e86-4fd0-b764-e0922aeecbb1
	  bd7d2fac-7650-4584-bf96-711d9ff9c9bf
	  c59fec48-87eb-4cc0-b14b-395dc2d3bdc5
	  de396a71-da2e-45ce-9493-ab2d04b4b6eb
	  b2166d60-fa46-4953-ada4-fec4f04e74bd
	  3abcc345-d817-4202-a814-006fd3dd16c4);
$tic  = 1017991929;
$toc  = 1017993745;
for(my $i=0;$i<90;$i++) {
  my $idx = $i%9;
  hist_insert({dumpid => "dump-$i",
	     directory => "/foo",
	     dumplevel => $dl[$idx],
	     tapelabel => $tl[$idx],
	     tapeidx => int(10*rand)+1,
	     tapeid =>  $tid[$idx],
	     starttime => $i<45 ? $tic : $toc,
	     options => "ext2dump,z,64k"});
}

#test 31..37
%h = hist_lookup({directory => "/foo"}); 
ok(scalar keys %h, 90);
%h = hist_lookup({directory => "/foo", dumplevel => 0}); 
ok(scalar keys %h, 50);
%h = hist_lookup({directory => "/foo", dumplevel => 1}); 
ok(scalar keys %h, 40);
%h = hist_lookup({directory => "/foo", tapelabel => "Thursday"}); 
ok(scalar keys %h, 10);
%h = hist_lookup({directory => "/foo", tapelabel => "Friday.*"}); 
ok(scalar keys %h, 50);
%h = hist_lookup({directory => "/foo", tapelabel => "Friday"}); 
ok(scalar keys %h, 0);
%h = hist_lookup({directory => "/foo", 
		  tapeid => "b2166d60-fa46-4953-ada4-fec4f04e74bd"}); 
ok(scalar keys %h, 10);

# test 38..40
%h = hist_lookup({directory => "/foo", before => $toc}); 
ok(scalar keys %h, 45);
%h = hist_lookup({directory => "/foo", after => $tic}); 
ok(scalar keys %h, 45);
%h = hist_lookup({directory => "/foo", 
		  dumplevel => 0,
		  tapelabel => "Friday_week3",
		  after => $tic}); 
ok(scalar keys %h, 5);

hist_insert("dump-0",  "/a", 0, "archiv",       2, "tape-0",  1, 'gtar'); # 1
hist_insert("dump-1",  "/a", 1, "Friday_week1", 2, "tape-1",  2, 'gtar'); # 2
hist_insert("dump-2",  "/a", 2, "Monday",       2, "tape-2",  3, 'gtar'); # 3
hist_insert("dump-3",  "/a", 3, "Tuesday",      2, "tape-3",  4, 'gtar'); # 4
hist_insert("dump-4",  "/a", 3, "Wednesday",    2, "tape-4",  5, 'gtar'); # 5
hist_insert("dump-5",  "/a", 3, "Thursday",     2, "tape-5",  6, 'gtar'); # 6
hist_insert("dump-6",  "/a", 1, "Friday_week2", 2, "tape-6",  7, 'gtar'); # 7
hist_insert("dump-7",  "/a", 2, "Monday",       2, "tape-2",  8, 'gtar'); # 8
hist_insert("dump-8",  "/a", 3, "Tuesday",      2, "tape-3",  9, 'gtar'); # 9
hist_insert("dump-9",  "/a", 3, "Wednesday",    2, "tape-4", 10, 'gtar'); # 10
hist_insert("dump-10", "/a", 3, "Thursday",     2, "tape-5", 11, 'gtar'); # 11
hist_insert("dump-11", "/a", 1, "Friday_week3", 2, "tape-7", 12, 'gtar'); # 12
hist_insert("dump-12", "/a", 2, "Monday",       2, "tape-2", 13, 'gtar'); # 13
hist_insert("dump-13", "/a", 3, "Tuesday",      2, "tape-3", 14, 'gtar'); # 14
hist_insert("dump-14", "/a", 3, "Wednesday",    2, "tape-4", 15, 'gtar'); # 15
hist_insert("dump-15", "/a", 3, "Thursday",     2, "tape-5", 16, 'gtar'); # 16
hist_insert("dump-16", "/a", 1, "Friday_week4", 2, "tape-7", 17, 'gtar'); # 17
hist_insert("dump-17", "/a", 2, "Monday",       2, "tape-2", 18, 'gtar'); # 18
hist_insert("dump-18", "/a", 3, "Tuesday",      2, "tape-3", 19, 'gtar'); # 19
hist_insert("dump-19", "/a", 3, "Wednesday",    2, "tape-4", 20, 'gtar'); # 20
hist_insert("dump-20", "/a", 3, "Thursday",     2, "tape-5", 21, 'gtar'); # 21

# test 41..48
ok(hist_get_parent({directory => "/a", dumplevel => 1, 
		    starttime => 2}), "dump-0");
ok(hist_get_parent("/a", 2, 2), "dump-0");
ok(hist_get_parent("/a", 3, 4), "dump-2");
ok(hist_get_parent("/a", 2, 4), "dump-1");
ok(hist_get_parent("/a", 1, 9), "dump-0");
ok(hist_get_parent("/a", 2, 9), "dump-6");
ok(hist_get_parent("/a", 3, 9), "dump-7");
ok(hist_get_parent("/a", 4, 9), "dump-7");

# test 49..52
@get = hist_get_parent("/a", 1, 17);
@exp = ("dump-0", hist_get("dump-0"));
ok("@get", "@exp");
@get = hist_get_parent("/a", 2, 17);
@exp = ("dump-11", hist_get("dump-11"));
ok("@get", "@exp");
@get = hist_get_parent("/a", 3, 17);
@exp = ("dump-12", hist_get("dump-12"));
ok("@get", "@exp");
@get = hist_get_parent("/a", 4, 17);
@exp = ("dump-15", hist_get("dump-15"));
ok("@get", "@exp");


# test 53
@get = hist_get_restorelist("/a", 22);
@exp = qw( dump-0 dump-16 dump-17 dump-20 );
ok("@get", "@exp");


# test 54
@get = hist_get_restorelist("/a", 11);
@exp = qw(dump-0 dump-6);
ok("@get", "@exp");

# test 55
@get = hist_get_restorelist("/a", 4);
@exp = qw(dump-0 dump-1);
ok("@get", "@exp");

hist_insert("dump-100", "/a", 0, "archiv",       2, "tape-0", 101, 'gtar'); 
hist_insert("dump-101", "/a", 1, "Friday_week1", 2, "tape-1", 102, 'gtar'); 
hist_insert("dump-102", "/a", 2, "Monday",       2, "tape-2", 103, 'gtar'); 
hist_insert("dump-103", "/a", 3, "Tuesday",      2, "tape-3", 104, 'gtar'); 
hist_insert("dump-104", "/a", 3, "Wednesday",    2, "tape-4", 105, 'gtar'); 
hist_insert("dump-105", "/a", 3, "Thursday",     2, "tape-5", 106, 'gtar'); 
hist_insert("dump-106", "/a", 1, "Friday_week2", 2, "tape-6", 107, 'gtar'); 
hist_insert("dump-107", "/a", 2, "Monday",       2, "tape-2", 108, 'gtar'); 
hist_insert("dump-108", "/a", 3, "Tuesday",      2, "tape-3", 109, 'gtar'); 
hist_insert("dump-109", "/a", 3, "Wednesday",    2, "tape-4", 110, 'gtar'); 
hist_insert("dump-110", "/a", 3, "Thursday",     2, "tape-5", 111, 'gtar'); 
hist_insert("dump-111", "/a", 1, "Friday_week3", 2, "tape-7", 112, 'gtar'); 
hist_insert("dump-112", "/a", 2, "Monday",       2, "tape-2", 113, 'gtar'); 
hist_insert("dump-113", "/a", 3, "Tuesday",      2, "tape-3", 114, 'gtar'); 
hist_insert("dump-114", "/a", 3, "Wednesday",    2, "tape-4", 115, 'gtar'); 
hist_insert("dump-115", "/a", 3, "Thursday",     2, "tape-5", 116, 'gtar'); 
hist_insert("dump-116", "/a", 1, "Friday_week4", 2, "tape-7", 117, 'gtar'); 
hist_insert("dump-117", "/a", 2, "Monday",       2, "tape-2", 118, 'gtar'); 
hist_insert("dump-118", "/a", 3, "Tuesday",      2, "tape-3", 119, 'gtar'); 
hist_insert("dump-119", "/a", 3, "Wednesday",    2, "tape-4", 120, 'gtar'); 
hist_insert("dump-120", "/a", 3, "Thursday",     2, "tape-5", 121, 'gtar'); 

# test 56
@get = hist_get_restorelist("/a", 22);
@exp = ();
ok("@get", "@exp");

# test 57
@get = hist_get_restorelist("/a", 122);
@exp = qw( dump-100 dump-116 dump-117 dump-120 );
ok("@get", "@exp");

# test 58
@get = hist_get_ancestors("dump-12");
@exp = qw(dump-11 dump-0);
ok("@get", "@exp");


# test 59
@get = hist_get_ancestors("dump-120");
@exp = qw(dump-117 dump-116 dump-100);
ok("@get", "@exp");


# test 60
@get = sort {$a cmp $b} hist_get_descendants("dump-116");
@exp = sort qw(dump-117 dump-118 dump-119 dump-120);
ok("@get", "@exp");

#test 61
@get = sort {$a cmp $b} hist_get_descendants("dump-0");
@exp = sort grep {s/^/dump-/} (1..20);
ok("@get", "@exp");

# test 62
@get = sort {$a cmp $b} hist_get_descendants("dump-7");
@exp = sort qw(dump-8 dump-9 dump-10);
ok("@get", "@exp");

# test 63
ok(!hist_get_descendants("dump-8"));

# test 64
hist_history_save("tar", "$dir/hist.tar");
@get = sort {$a cmp $b} qx(tar -xOf $dir/hist.tar);
chomp @get;
%h = hist_lookup;
@exp = sort values %h;
chomp @exp;
ok(@get, @exp);

print qx(ls -dl $dir);
print qx(ls -l $dir);
