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
// $Id: Common.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once "Services/Weather.php";

// {{{ constants
// {{{ natural constants and measures
define("SERVICES_WEATHER_RADIUS_EARTH", 6378.15);
// }}}
// }}}

// {{{ class Services_Weather_Common
/**
* PEAR::Services_Weather_Common
*
* Parent class for weather-services. Defines common functions for unit
* conversions, checks for astronomy-class, cache enabling and does other
* miscellaneous things. 
*
* @author       Alexander Wirtz <alex@pc4p.net>
* @package      Services_Weather
* @license      http://www.php.net/license/2_02.txt
* @version      1.2
*/
class Services_Weather_Common {

    // {{{ properties
    /**
    * Format of the units provided (standard/metric/custom)
    *
    * @var      string                      $_unitsFormat
    * @access   private
    */
    var $_unitsFormat = "s";

    /**
    * Custom format of the units
    *
    * @var      array                       $_customUnitsFormat
    * @access   private
    */
    var $_customUnitsFormat = array(
        "temp"  => "f",
        "vis"   => "sm",
        "wind"  => "mph",
        "pres"  => "in",
        "rain"  => "in"
    );

    /**
    * Format of the used dates
    *
    * @var      string                      $_dateFormat
    * @access   private
    */
    var $_dateFormat = "m/d/y";

    /**
    * Format of the used times
    *
    * @var      string                      $_timeFormat
    * @access   private
    */
    var $_timeFormat = "G:i A";

    /**
    * Object containing the location-data
    *
    * @var      object stdClass             $_location
    * @access   private
    */
    var $_location;

    /**
    * Object containing the weather-data
    *
    * @var      object stdClass             $_weather
    * @access   private
    */
    var $_weather;

    /**
    * Object containing the forecast-data
    *
    * @var      object stdClass             $_forecast
    * @access   private
    */
    var $_forecast;

    /**
    * Cache, containing the data-objects
    *
    * @var      object Cache                $_cache
    * @access   private
    */
    var $_cache;

    /**
    * Provides check for Cache
    *
    * @var      bool                        $_cacheEnabled
    * @access   private
    */
    var $_cacheEnabled = false;
    // }}}

    // {{{ constructor
    /**
    * Constructor
    *
    * @param    array                       $options
    * @param    mixed                       $error
    * @throws   PEAR_Error
    * @see      Science_Weather::Science_Weather
    * @access   private
    */
    function Services_Weather_Common($options, &$error)
    {
        // Set options accordingly        
        if (isset($options["cacheType"])) {
            if (isset($options["cacheOptions"])) {
                $status = $this->setCache($options["cacheType"], $options["cacheOptions"]);
            } else {
                $status = $this->setCache($options["cacheType"]);
            }
        }
        if (Services_Weather::isError($status)) {
            $error = $status;
            return;
        }

        if (isset($options["unitsFormat"])) {
            if (isset($options["customUnitsFormat"])) {
                $this->setUnitsFormat($options["unitsFormat"], $options["customUnitsFormat"]);
            } else {
                $this->setUnitsFormat($options["unitsFormat"]);
            }
        }
        
        if (isset($options["dateFormat"])) {
            $this->setDateTimeFormat($options["dateFormat"], "");
        }
        if (isset($options["timeFormat"])) {
            $this->setDateTimeFormat("", $options["timeFormat"]);
        }
    }
    // }}}

    // {{{ setCache()
    /**
    * Enables caching the data, usage strongly recommended
    *
    * Requires Cache to be installed
    *
    * @param    string                      $cacheType
    * @param    array                       $cacheOptions
    * @return   PEAR_Error|bool
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_CACHE_INIT_FAILED
    * @access   public
    */
    function setCache($cacheType = "file", $cacheOptions = array())
    {
        // The error handling in Cache is a bit crummy (read: not existent)
        // so we have to do that on our own...
        @include_once "Cache.php";
        @$cache = new Cache($cacheType, $cacheOptions);
        if (is_object($cache) && (get_class($cache) == "cache" || is_subclass_of($cache, "cache"))) {
            $this->_cache        = $cache;
            $this->_cacheEnabled = true;
        } else {
            $this->_cache        = null;
            $this->_cacheEnabled = false;
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_CACHE_INIT_FAILED);
        }

        return true;
    }
    // }}}

    // {{{ setUnitsFormat()
    /**
    * Changes the representation of the units (standard/metric)
    *
    * @param    string                      $unitsFormat
    * @param    array                       $customUnitsFormat
    * @access   public
    */
    function setUnitsFormat($unitsFormat, $customUnitsFormat = array())
    {
        static $acceptedFormats;
        if (!isset($acceptedFormats)) {
            $acceptedFormats = array(
                "temp"  => array("c", "f"),
                "vis"   => array("km", "ft", "sm"),
                "wind"  => array("mph", "kmh", "kt", "mps", "fps"),
                "pres"  => array("in", "hpa", "mb", "mm", "atm"),
                "rain"  => array("in", "mm")
            );
        }
        
        if (strlen($unitsFormat) && in_array(strtolower($unitsFormat{0}), array("c", "m", "s"))) {
            $this->_unitsFormat = strtolower($unitsFormat{0});
            if ($this->_unitsFormat == "c" && is_array($customUnitsFormat)) {
                foreach ($customUnitsFormat as $key => $value) {
                    if (array_key_exists($key, $acceptedFormats) && in_array($value, $acceptedFormats[$key])) {
                        $this->_customUnitsFormat[$key] = $value;
                    }
                }
            } elseif ($this->_unitsFormat == "c") {
                $this->_unitsFormat = "s";
            }
        }
    }
    // }}}

    // {{{ getUnitsFormat()
    /**
    * Returns the selected units format
    *
    * @param    string                      $unitsFormat
    * @return   array
    * @access   public
    */
    function getUnitsFormat($unitsFormat = "")
    {
        // This is cheap'o stuff
        if (strlen($unitsFormat) && in_array(strtolower($unitsFormat{0}), array("c", "m", "s"))) {
            $unitsFormat = strtolower($unitsFormat{0});
        } else {
            $unitsFormat = $this->_unitsFormat;
        }

        $c = $this->_customUnitsFormat;
        $m = array(
            "temp"  => "c",
            "vis"   => "km",
            "wind"  => "kmh",
            "pres"  => "mb",
            "rain"  => "mm"
        );
        $s = array(
            "temp"  => "f",
            "vis"   => "sm",
            "wind"  => "mph",
            "pres"  => "in",
            "rain"  => "in"
        );

        return ${$unitsFormat};
    }
    // }}}

    // {{{ setDateTimeFormat()
    /**
    * Changes the representation of time and dates (see http://www.php.net/date)
    *
    * @param    string                      $dateFormat
    * @param    string                      $timeFormat
    * @access   public
    */
    function setDateTimeFormat($dateFormat = "", $timeFormat = "")
    {
        if (strlen($dateFormat)) {
            $this->_dateFormat = $dateFormat;
        }
        if (strlen($timeFormat)) {
            $this->_timeFormat = $timeFormat;
        }
    }
    // }}}

    // {{{ convertTemperature()
    /**
    * Convert temperature between f and c
    *
    * @param    float                       $temperature
    * @param    string                      $from
    * @param    string                      $to
    * @return   float
    * @access   public
    */
    function convertTemperature($temperature, $from, $to)
    {
        $from = strtolower($from{0});
        $to   = strtolower($to{0});

        $result = array(
            "f" => array(
                "f" => $temperature,            "c" => ($temperature - 32) / 1.8
            ),
            "c" => array(
                "f" => 1.8 * $temperature + 32, "c" => $temperature
            )
        );

        return round($result[$from][$to], 2);
    }
    // }}}

    // {{{ convertSpeed()
    /**
    * Convert speed between mph, kmh, kt, mps and fps
    *
    * @param    float                       $speed
    * @param    string                      $from
    * @param    string                      $to
    * @return   float
    * @access   public
    */
    function convertSpeed($speed, $from, $to)
    {
        $from = strtolower($from);
        $to   = strtolower($to);

        static $factor;
        if (!isset($factor)) {
            $factor = array(
                "mph" => array(
                    "mph" => 1,         "kmh" => 1.609344, "kt" => 0.8689762, "mps" => 0.44704,   "fps" => 1.4666667
                ),
                "kmh" => array(
                    "mph" => 0.6213712, "kmh" => 1,        "kt" => 0.5399568, "mps" => 0.2777778, "fps" => 0.9113444
                ),
                "kt"  => array(
                    "mph" => 1.1507794, "kmh" => 1.852,    "kt" => 1,         "mps" => 0.5144444, "fps" => 1.6878099
                ),
                "mps" => array(
                    "mph" => 2.2369363, "kmh" => 3.6,      "kt" => 1.9438445, "mps" => 1,         "fps" => 3.2808399
                ),
                "fps" => array(
                    "mph" => 0.6818182, "kmh" => 1.09728,  "kt" => 0.5924838, "mps" => 0.3048,    "fps" => 1
                )
            );
        }

        return round($speed * $factor[$from][$to], 2);
    }
    // }}}

    // {{{ convertPressure()
    /**
    * Convert pressure between in, hpa, mb, mm and atm
    *
    * @param    float                       $pressure
    * @param    string                      $from
    * @param    string                      $to
    * @return   float
    * @access   public
    */
    function convertPressure($pressure, $from, $to)
    {
        $from = strtolower($from);
        $to   = strtolower($to);

        static $factor;
        if (!isset($factor)) {
            $factor = array(
                "in"   => array(
                    "in" => 1,         "hpa" => 33.863887, "mb" => 33.863887, "mm" => 25.4,      "atm" => 0.0334213
                ),
                "hpa"  => array(
                    "in" => 0.02953,   "hpa" => 1,         "mb" => 1,         "mm" => 0.7500616, "atm" => 0.0009869
                ),
                "mb"   => array(
                    "in" => 0.02953,   "hpa" => 1,         "mb" => 1,         "mm" => 0.7500616, "atm" => 0.0009869
                ),
                "mm"   => array(
                    "in" => 0.0393701, "hpa" => 1.3332239, "mb" => 1.3332239, "mm" => 1,         "atm" => 0.0013158
                ),
                "atm"  => array(
                    "in" => 29,921258, "hpa" => 1013.2501, "mb" => 1013.2501, "mm" => 759.999952, "atm" => 1
                )
            );
        }

        return round($pressure * $factor[$from][$to], 2);
    }
    // }}}

    // {{{ convertDistance()
    /**
    * Convert distance between km, ft and sm
    *
    * @param    float                       $distance
    * @param    string                      $from
    * @param    string                      $to
    * @return   float
    * @access   public
    */
    function convertDistance($distance, $from, $to)
    {
        $to   = strtolower($to);
        $from = strtolower($from);

        static $factor;
        if (!isset($factor)) {
            $factor = array(
                "km" => array(
                    "km" => 1,         "ft" => 3280.839895, "sm" => 0.6213699
                ),
                "ft" => array(
                    "km" => 0.0003048, "ft" => 1,           "sm" => 0.0001894
                ),
                "sm" => array(
                    "km" => 1.6093472, "ft" => 5280.0106,   "sm" => 1
                )
            );
        }

        return round($distance * $factor[$from][$to], 2);
    }
    // }}}

    // {{{ calculateWindChill()
    /**
    * Calculate windchill from temperature and windspeed (enhanced formula)
    *
    * Temperature has to be entered in deg F, speed in mph!
    *
    * @param    float                       $temperature
    * @param    float                       $speed
    * @return   float
    * @access   public
    * @link     http://www.nws.noaa.gov/om/windchill/      
    */
    function calculateWindChill($temperature, $speed)
    {
        return round(35.74 + 0.6215 * $temperature - 35.75 * pow($speed, 0.16) + 0.4275 * $temperature * pow($speed, 0.16));
    }
    // }}}

    // {{{ calculateHumidity()
    /**
    * Calculate humidity from temperature and dewpoint
    * This is only an approximation, there is no exact formula, this
    * one here is called Magnus-Formula
    *
    * Temperature and dewpoint have to be entered in deg C!
    *
    * @param    float                       $temperature
    * @param    float                       $dewPoint
    * @return   float
    * @access   public
    * @link     http://www.faqs.org/faqs/meteorology/temp-dewpoint/
    */
    function calculateHumidity($temperature, $dewPoint)
    {   
        // First calculate saturation steam pressure for both temperatures
        if ($temperature >= 0) {
            $a = 7.5;
            $b = 237.3;
        } else {
            $a = 7.6;
            $b = 240.7;
        }
        $tempSSP = 6.1078 * pow(10, ($a * $temperature) / ($b + $temperature));

        if ($dewPoint >= 0) {
            $a = 7.5;
            $b = 237.3;
        } else {
            $a = 7.6;
            $b = 240.7;
        }
        $dewSSP  = 6.1078 * pow(10, ($a * $dewPoint) / ($b + $dewPoint));
        
        return round(100 * $dewSSP / $tempSSP, 1);
    }
    // }}}

    // {{{ calculateDewPoint()
    /**
    * Calculate dewpoint from temperature and humidity
    * This is only an approximation, there is no exact formula, this
    * one here is called Magnus-Formula
    *
    * Temperature has to be entered in deg C!
    *
    * @param    float                       $temperature
    * @param    float                       $humidity
    * @return   float
    * @access   public
    * @link     http://www.faqs.org/faqs/meteorology/temp-dewpoint/
    */
    function calculateDewPoint($temperature, $humidity)
    {   
        if ($temperature >= 0) {
            $a = 7.5;
            $b = 237.3;
        } else {
            $a = 7.6;
            $b = 240.7;
        }

        // First calculate saturation steam pressure for temperature
        $SSP = 6.1078 * pow(10, ($a * $temperature) / ($b + $temperature));

        // Steam pressure
        $SP  = $humidity / 100 * $SSP;

        $v   = log($SP / 6.1078, 10);

        return round($b * $v / ($a - $v), 1);
    }
    // }}}

    // {{{ polar2cartesian()
    /**
    * Convert polar coordinates to cartesian coordinates
    *
    * @param    float                       $latitude
    * @param    float                       $longitude
    * @return   array
    * @access   public
    */
    function polar2cartesian($latitude, $longitude)
    {
        $theta = deg2rad($latitude);
        $phi   = deg2rad($longitude);

        $x = SERVICES_WEATHER_RADIUS_EARTH * cos($phi) * cos($theta);
        $y = SERVICES_WEATHER_RADIUS_EARTH * sin($phi) * cos($theta);
        $z = SERVICES_WEATHER_RADIUS_EARTH             * sin($theta);

        return array($x, $y, $z);
    }
    // }}}
}
// }}}
?>
