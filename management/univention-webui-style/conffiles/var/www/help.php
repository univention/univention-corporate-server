<?php
/*
 * Univention Webui
 *  help.php
 *
 * Copyright (C) 2009 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License version 2 as
 * published by the Free Software Foundation.
 *
 * Binary versions of this file provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
 */

$DEFAULT_LANG = 'en';
$DEFAULT_APP = 'udm';
// add new help index pages here!
$PATH_HELPFILE = array (
	'udm' => '@%@directory/manager/web/onlinehelp/index@%@',
	'umc' => '@%@umc/web/onlinehelp/index@%@'
  );

function get_sanitized_argument($name) {
  // get GET/POST argument "$name"
  $var = $_GET[$name];
  if ( empty($var) ) {
    $var = $_POST[$name];
  }
  // sanitize input
  $var = preg_replace('/[^a-z]/', '', $var);
  return $var;
}

$lang = get_sanitized_argument( "lang" );
if ( empty($lang) || (strlen($lang) != 2)) {  // use fallback if lang is unset or contains wrong number of characters
  $lang = $DEFAULT;
}

$app = get_sanitized_argument( "app" );
if ( empty($app) ) {  // use fallback if lang is unset or contains wrong number of characters
  $lang = $DEFAULT_APP;
}

// select application specific online help index
if (isset($PATH_HELPFILE[$app])) {
  $prefilename = $PATH_HELPFILE[$app];
} else {
  $prefilename = $PATH_HELPFILE[$DEFAULT_APP];
}

// return selected file in specified language
$filename = str_replace("%s", $lang, $prefilename);
if (is_file($filename)) {
  readfile($filename);
} else {
  $filename = str_replace("%s", $DEFAULT_LANG, $prefilename);
  if (is_file($filename)) {
	readfile($filename);
  } else {
	echo "cannot find $filename";
  }
}
?>