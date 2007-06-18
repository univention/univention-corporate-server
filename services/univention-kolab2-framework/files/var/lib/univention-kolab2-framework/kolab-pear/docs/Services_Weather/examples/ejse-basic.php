<?php
/* vim: set expandtab tabstop=4 shiftwidth=4: */
// +----------------------------------------------------------------------+
// | PHP version 4                                                        |
// +----------------------------------------------------------------------+
// | Copyright (c) 1997-2004 The PHP Group                                |
// +----------------------------------------------------------------------+
// | This source file is subject to version 2.0 of the PHP license,       |
// | that is bundled with this package in the file LICENSE, and is        |
// | available through the world-wide-web at                              |
// | http://www.php.net/license/2_02.txt.                                 |
// | If you did not receive a copy of the PHP license and are unable to   |
// | obtain it through the world-wide-web, please send a note to          |
// | license@php.net so we can mail you a copy immediately.               |
// +----------------------------------------------------------------------+
// | Authors: Alexander Wirtz <alex@pc4p.net>                             |
// +----------------------------------------------------------------------+
//
// $Id: ejse-basic.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once "Services/Weather.php";

// Object initialization - error checking is important, because of
// handling exceptions such as missing PEAR modules or not being online
$ejse = &Services_Weather::service("Ejse", array("debug" => 2));
if (Services_Weather::isError($ejse)) {
    die("Error: ".$ejse->getMessage()."\n");
}

/* Erase comments to enable caching
$ejse->setCache("file", array("cache_dir" => "/tmp/cache/"));
if (Services_Weather::isError($ejse)) {
    echo "Error: ".$ejse->getMessage()."\n";
}
*/

$ejse->setUnitsFormat("metric");
$ejse->setDateTimeFormat("d.m.Y", "H:i");

$location = "81611"; // Aspen, CO
//$location = "02115"; // Boston, MA
//$location = "96799"; // Pago Pago, AS
//$location = "09009"; // Armed Forces Europe -> Error

// Now iterate through available functions for retrieving data
foreach (array("getLocation", "getWeather", "getForecast") as $function) {
    $data = $ejse->$function($location);
    if (Services_Weather::isError($data)) {
        echo "Error: ".$data->getMessage()."\n";
        continue;
    }

    var_dump($data);
}
?>
