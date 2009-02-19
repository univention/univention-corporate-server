<?php
/*
 * Univention Webui
 *  index.php
 *
 * Copyright (C) 2004-2009 Univention GmbH
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

if (!get_cfg_var(register_globals))
{
# For register_globals=off in php.ini (PHP Version > 4.2.3)
  foreach($_GET as $key => $value)
    $$key = $_GET[$key];
  foreach($_POST as $key => $value)
    $$key = $_POST[$key];
}

/* uncomment the following to debug POST message */
/*
function printPostValue($pvalue, $message) {
        if (is_array($pvalue))
                foreach($pvalue as $key => $value)
                        printPostValue($value, $message.$key.": ");
        else
                echo $message.$pvalue." <br> \n";

}

printPostValue($_POST, "POST: ");
*/

include ("includes/config.inc");	# Konfigurations-Klasse
$config = new webui_config($_SERVER["HTTP_USER_AGENT"], $session_id);
$config->set_js($is_js);
include ("includes/language.inc");	# i18n-Klasse
include ("includes/container.inc");	# Container-Klasse
include ("includes/parser.inc");	# Parser-Klasse
include ("includes/translator.inc");	# Übersetzungs-Klasse

$usedtextdomain = textdomain ( 'univention-webui' );

function escape_delimiter($instring) {
  $delimiter = "|";
  $outstring = "";
  $len = strlen( $instring );
  for ($i = 0; $i < $len; $i++) {
    if ($instring[$i] == $delimiter) {
	  $outstring = $outstring . $delimiter;
	}
	$outstring = $outstring . $instring[$i];
  }
  return $outstring;
}

if(is_array($_FILES['userfile'])){
	$tmp_name = escape_delimiter( $_FILES['userfile']['tmp_name'] );
	$fname = escape_delimiter( $_FILES['userfile']['name'] );
	$fsize = escape_delimiter( $_FILES['userfile']['size'] );
	$ftype = escape_delimiter( $_FILES['userfile']['type'] );
	$ferror = escape_delimiter( $_FILES['userfile']['error'] );
	$usrinput[$file] = $tmp_name . "@|@" . $fname . "@|@" . $fsize . "@|@" . $ftype . "@|@" . $ferror;
	# additional infos:
	# $userfile[name] - original filename
	# $userfile[type] - mime-type of uploaded file
	# $userfile[error] - error code if upload failed
	# $userfile[size] - filesize in bytes
}


if(!isset($logout))
{
  if(!isset($session_id))
    {

#################### For orig. Python Backend   ############
  // spawn off daemon
	$fp = popen($config->run." -s -", 'w');
	fwrite($fp, $config->socket_filename);
	fclose($fp);

	$pipe=fsockopen("unix://".$config->socket_filename, 0);
        if(isset($module)){
		fwrite($pipe, "jumpurl: ".$module."\n");
	}
	if(isset($opts)){
		fwrite($pipe, "opts: ".$opts."\n");
	}
	# send a notification when the session was caught by the timeout
	if ($sessioninvalid == '1') {
		fwrite($pipe, "Sessioninvalid: 1\n");
	}
	fwrite($pipe, "SessionId: ".$config->session_id."\n");
	fwrite($pipe, "Number: -1\n\n\0");

	$fp=fopen($config->session_dir.$config->number, "w");
	while (($buf = fread($pipe, 1024))) {
		fwrite($fp, $buf);
		if (strpos($buf, '\0'))
			break;
	}
	fclose($fp);
	fclose($pipe);
############################################################
    }
  if(@current($long_table))
    {
      switch ($long_table[key($long_table)])
	{
	case "<<":
	  $long_table[key($long_table)] = $visible*($previous-2);
	  break;
	case ">>":
	  $long_table[key($long_table)] = $visible*($next);
	  break;
	case "<":
	  $long_table[key($long_table)] = $visible*($current - 2);
	  break;
	case ">":
	  $long_table[key($long_table)] = $visible*($current);
	  break;
	default:
	  $long_table[key($long_table)] = ($long_table[key($long_table)]-1)*$visible;
	}
      if ($usrinput)
	{
	  $usrinput[key($long_table)] = $long_table[key($long_table)];
	  $output = new webui_out($config, $usrinput, $session_data);
	}
      else
	{
	  $output = new webui_out($config, $long_table, $session_data);
	}

    }
  elseif ($usrinput)
    {
      if (isset($current_position))
	$config->set_position($current_position);
      $output = new webui_out($config, $usrinput, $session_data);
    }
  $glob_tabindex=1;
  $container = new webui_container($config, $glob_tabindex);
  $trans = new webui_translator($container, $config);
  $parser = new webui_in($config, $trans);
  $config->del_old();
  $container->show();
}
else
{
  $container = new webui_container($config, $glob_tabindex);
  #$this->config = $config;
  $container->config = $config;
  $container->logout($logout, $session_id);
}

?>
