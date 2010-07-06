<?php
/**
 * $Horde: imp/config/header.php.dist,v 1.1.2.3 2007-12-20 13:59:20 jan Exp $
 *
 * This file will allow you to set headers to append to outgoing mail messages.
 *
 * To add a new header item, simply add a new entry to the $_header array.
 * The "key" should be the header name.
 * The "value" should be the header data.
 *
 * Example entries:
 *
 *  // Add the IP of the remote browser
 *  $_header['X-Originating-IP'] = $_SERVER['REMOTE_ADDR'];
 *
 *  // Add the Browser information of the remote browser
 *  $_header['X-Remote-Browser'] = $_SERVER['HTTP_USER_AGENT'];
 */

$_header = array();

/* Add your custom entries below this line. */
