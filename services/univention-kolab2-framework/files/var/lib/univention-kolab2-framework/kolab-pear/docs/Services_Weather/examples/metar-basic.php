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
// $Id: metar-basic.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once "Services/Weather.php";

// Object initialization - error checking is important, because of
// handling exceptions such as missing PEAR modules
$metar = &Services_Weather::service("METAR", array("debug" => 0));
if (Services_Weather::isError($metar)) {
    die("Error: ".$metar->getMessage()."\n");
}

// Set parameters for DB access, needed for location searches
$metar->setMetarDB("sqlite://localhost//usr/local/lib/php/data/Services_Weather/servicesWeatherDB");
if (Services_Weather::isError($metar)) {
    echo "Error: ".$metar->getMessage()."\n";
}

/* Erase comments to enable caching
$metar->setCache("file", array("cache_dir" => "/tmp/cache/"));
if (Services_Weather::isError($metar)) {
    echo "Error: ".$metar->getMessage()."\n";
}
*/

$metar->setUnitsFormat("custom", array(
    "wind" => "kt",
    "vis" => "km",
    "temp" => "c",
    "pres" => "hpa",
    "rain" => "in"));
$metar->setDateTimeFormat("d.m.Y", "H:i");

// First get code for location
$search = $metar->searchLocation("Bonn, Germany");
if (Services_Weather::isError($search)) {
    die("Error: ".$search->getMessage()."\n");
}

// Now iterate through available functions for retrieving data
foreach (array("getLocation", "getWeather", "getForecast") as $function) {
    $data = $metar->$function($search);
    if (Services_Weather::isError($data)) {
        echo "Error: ".$data->getMessage()."\n";
        continue;
    }

    var_dump($data);
}
?>
