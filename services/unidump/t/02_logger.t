#!/usr/bin/perl
# 	$Id: 02_logger.t,v 1.2 2003/09/08 07:14:37 thorsten Exp $	

use Test;
use English;
use POSIX;
use Unidump::Logger qw(:all);

BEGIN { plan tests => 2; }

$WARNING = 0;

do { 
  $f = POSIX::tmpnam; 
} until sysopen(F, $f, O_RDWR | O_CREAT | O_EXCL);
close(F);

$Unidump::Logger::unilogfile = $f;
$Unidump::Logger::debug = 0;
$Unidump::Logger::useunilog = 0;
$Unidump::Logger::usestderr = 0;
$Unidump::Logger::usesyslog = 0;

# test 1
$day = strftime("%Y/%m/%d", localtime());
eval {
  local($Unidump::Logger::useunilog);
  $Unidump::Logger::useunilog = 0;
  logmessage("I'm not seen");
  $Unidump::Logger::useunilog = 1;
  logmessage("test-me");
  open(F, "$f");
  undef($RS);
  $get = <F>;
  close(F);
  unlink($f);
};
ok($get, '/^\[' . $day . ' \d\d:\d\d:\d\d\] test-me$/');

# test 2
eval {
  local($Unidump::Logger::debug);
  $Unidump::Logger::debug = 0;
  logmessage_debug("I'm not seen");
  $Unidump::Logger::debug = 1;
  open(STDERR, ">$f");
  logmessage_debug("test-me-debug");
  close(STDERR);
  open(F, "$f");
  undef($RS);
  $get = <F>;
  close(F);
  unlink($f);
};
ok($get, '/^DEBUG: test-me-debug at /');

