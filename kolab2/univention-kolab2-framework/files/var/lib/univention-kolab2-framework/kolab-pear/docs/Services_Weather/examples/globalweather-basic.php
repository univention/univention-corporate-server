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
// $Id: globalweather-basic.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once "Services/Weather.php";

// Object initialization - error checking is important, because of
// handling exceptions such as missing PEAR modules or not being online
$globalweather = &Services_Weather::service("GlobalWeather", array("debug" => 2));
if (Services_Weather::isError($globalweather)) {
    die("Error: ".$globalweather->getMessage()."\n");
}

/* Erase comments to enable caching
$globalweather->setCache("file", array("cache_dir" => "/tmp/cache/"));
if (Services_Weather::isError($globalweather)) {
    echo "Error: ".$globalweather->getMessage()."\n";
}
*/

$globalweather->setUnitsFormat("metric");
$globalweather->setDateTimeFormat("d.m.Y", "H:i");

// First get code for location
$search = $globalweather->searchLocation("Koeln / Bonn");
if (Services_Weather::isError($search)) {
    die("Error: ".$search->getMessage()."\n");
}

// Now iterate through available functions for retrieving data
foreach (array("getLocation", "getWeather", "getForecast") as $function) {
    $data = $globalweather->$function($search);
    if (Services_Weather::isError($data)) {
        echo "Error: ".$data->getMessage()."\n";
        continue;
    }

    var_dump($data);
}
?>
