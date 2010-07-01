#!/usr/bin/php
<?php
/**
 * This script bounces a message back to the sender and can be used with IMP's
 * spam reporting feature to bounce spam.
 *
 * It takes the orginal message from standard input and requires the bounce
 * message in the file imp/config/bounce.txt. Important: the bounce message
 * must be a complete message including headers!
 *
 * $Horde: imp/scripts/bounce_spam.php,v 1.4.2.3 2009-01-06 15:24:32 jan Exp $
 *
 * Copyright 2005-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (GPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/gpl.html.
 *
 * @author Jan Schneider <jan@horde.org>
 */

define('IMP_CONFIG', dirname(__FILE__) . '/../config');
require_once 'Horde/CLI.php';

/* Make sure no one runs this from the web. */
if (!Horde_CLI::runningFromCLI()) {
    fwrite(STDERR, "Must be run from the command line\n");
    exit(1);
}

/* If there's no bounce template file then abort */
if (!file_exists(IMP_CONFIG . '/bounce.txt')) {
    exit(0);
}

/* Load the CLI environment - make sure there's no time limit, init some
 * variables, etc. */
Horde_CLI::init();

/* Read the message content. */
$data = Horde_CLI::readStdin();

/* Who's the spammer? */
preg_match('/return-path: <(.*?)>\r?\n/i', $data, $matches);
$return_path = $matches[1];

/* Who's the target? */
preg_match_all('/delivered-to: (.*?)\r?\n/is', $data, $matches);
$delivered_to = $matches[1][count($matches[1])-1];

/* Read the bounce template and construct the mail */
$bounce = file_get_contents(IMP_CONFIG . '/bounce.txt');
$bounce = str_replace(array('%TO%', '%TARGET%'),
                      array($return_path, $delivered_to),
                      $bounce);

/* Send the mail */
$sendmail = "/usr/sbin/sendmail -t -f ''";
$fd = popen($sendmail, 'w');
fputs($fd, preg_replace("/\n$/", "\r\n", $bounce . $data));
pclose($fd);
