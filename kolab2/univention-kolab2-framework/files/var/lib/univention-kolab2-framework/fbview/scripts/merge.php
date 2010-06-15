#!/usr/local/bin/php -q
<?php
/**
$Horde: horde/scripts/merge.php,v 1.3 2002/11/10 20:52:19 chuck Exp $

A small script that takes lines of a commit message like:

  2.485     +26 -5     imp/compose.php
  1.503     +2 -0      imp/docs/CHANGES
  2.159     +25 -12    imp/templates/compose/compose.inc
  2.55      +28 -3     imp/templates/compose/javascript.inc

from the standard input and merges these commits into the
appropriate files of the current directory.
Mainly for merging changes in HEAD to the RELENG tree.
*/

@set_time_limit(0);
ob_implicit_flush(true);
ini_set('track_errors', true);
ini_set('implicit_flush', true);
ini_set('html_errors', false);
ini_set('magic_quotes_runtime', false);

$lines = file('php://stdin');
foreach ($lines as $line) {
    $tok = preg_split('/\s+/', $line, -1, PREG_SPLIT_NO_EMPTY);
    if (count($tok) != 4) {
        print "Unknown line format:\n" . $line . "\n";
        continue;
    }
    $new_version = explode('.', $tok[0]);
    $old_version = $new_version;
    $old_version[count($old_version) - 1]--;
    $cmd = sprintf('cvs up -kk -j %s -j %s %s' . "\n",
                   implode('.', $old_version), implode('.', $new_version), str_replace('horde/', '', $tok[3]));
    print $cmd;
    system($cmd . ' 2>&1');
    print "\n";
}
