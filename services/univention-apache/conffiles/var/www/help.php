<?php
@%@BCWARNING=// @%@
/*
 * Univention Webui
 *  help.php
 *
 * Copyright 2009-2012 Univention GmbH
 *
 * http://www.univention.de/
 *
 * All rights reserved.
 *
 * The source code of this program is made available
 * under the terms of the GNU Affero General Public License version 3
 * (GNU AGPL V3) as published by the Free Software Foundation.
 *
 * Binary versions of this program provided by Univention to you as
 * well as other copyrighted, protected or trademarked materials like
 * Logos, graphics, fonts, specific documentations and configurations,
 * cryptographic keys etc. are subject to a license agreement between
 * you and Univention and not subject to the GNU AGPL V3.
 *
 * In the case you use this program under the terms of the GNU AGPL V3,
 * the program is provided in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License with the Debian GNU/Linux or Univention distribution in file
 * /usr/share/common-licenses/AGPL-3; if not, see
 * <http://www.gnu.org/licenses/>.
 */

// default application in case the given one does not exist
$DEFAULT_APP = 'udm';

// the inlcude file containing the online help layout is set for each module
// separately in the following UCR variables
$LAYOUT_INCLUDE = array (
	'udm' => '@%@directory/manager/web/onlinehelp/layout@%@',
	'umc' => '@%@umc/web/onlinehelp/layout@%@'
);

// include files for help text with different language versions are set in 
// the following UCR variables
$HELP_INCLUDE = array (
	'udm' => '@%@directory/manager/web/onlinehelp/include@%@',
	'umc' => '@%@umc/web/onlinehelp/include@%@'
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

// get the current active application and include layout as well as help text files
$app = get_sanitized_argument( "app" );
include($HELP_INCLUDE[array_key_exists($app, $HELP_INCLUDE) ? $app : $DEFAULT_APP]); // includes help texts for current module in different languages
include($LAYOUT_INCLUDE[array_key_exists($app, $LAYOUT_INCLUDE) ? $app : $DEFAULT_APP]); // includes the layout information with print_help() function

// get the current language option and print the help
$lang = get_sanitized_argument( "lang" );
print_help($lang);
?>

