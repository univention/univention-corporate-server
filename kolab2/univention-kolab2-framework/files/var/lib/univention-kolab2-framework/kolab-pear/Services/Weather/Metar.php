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
// $Id: Metar.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once "Services/Weather/Common.php";

require_once "DB.php";

// {{{ class Services_Weather_Metar
/**
* PEAR::Services_Weather_Metar
*
* This class acts as an interface to the metar service of weather.noaa.gov. It searches for
* locations given in ICAO notation and retrieves the current weather data.
*
* Of course the parsing of the METAR-data has its limitations, as it follows the
* Federal Meteorological Handbook No.1 with modifications to accomodate for non-US reports,
* so if the report deviates from these standards, you won't get it parsed correctly.
* Anything that is not parsed, is saved in the "noparse" array-entry, returned by
* getWeather(), so you can do your own parsing afterwards. This limitation is specifically
* given for remarks, as the class is not processing everything mentioned there, but you will
* get the most common fields like precipitation and temperature-changes. Again, everything
* not parsed, goes into "noparse".
*
* If you think, some important field is missing or not correctly parsed, please file a feature-
* request/bugreport at http://pear.php.net/ and be sure to provide the METAR report with a
* _detailed_ explanation!
*
* For a working example, please take a look at
*     docs/Services_Weather/examples/metar-basic.php
*
* @author       Alexander Wirtz <alex@pc4p.net>
* @link         http://weather.noaa.gov/weather/metar.shtml
* @example      docs/Services_Weather/examples/metar-basic.php
* @package      Services_Weather
* @license      http://www.php.net/license/2_02.txt
* @version      1.2
*/
class Services_Weather_Metar extends Services_Weather_Common
{
    // {{{ properties
    /**
    * Information to access the location DB
    *
    * @var      object  DB                  $_db
    * @access   private
    */
    var $_db;
    
    /**
    * The source METAR uses
    *
    * @var      string                      $_source
    * @access   private
    */
    var $_source;

    /**
    * This path is used to find the METAR data
    *
    * @var      string                      $_sourcePath
    * @access   private
    */
    var $_sourcePath;
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
    function Services_Weather_Metar($options, &$error)
    {
        $perror = null;
        $this->Services_Weather_Common($options, $perror);
        if (Services_Weather::isError($perror)) {
            $error = $perror;
            return;
        }
        
        // Set options accordingly        
        if (isset($options["dsn"])) {
            if (isset($options["dbOptions"])) {
                $status = $this->setMetarDB($options["dsn"], $options["dbOptions"]);
            } else {
                $status = $this->setMetarDB($options["dsn"]);
            }
        }
        if (Services_Weather::isError($status)) {
            $error = $status;
            return;
        }
        
        if (isset($options["source"])) {
            if (isset($options["sourcePath"])) {
                $this->setMetarSource($options["source"], $options["sourcePath"]);
            } else {
                $this->setMetarSource($options["source"]);
            }
        } else {
            $this->setMetarSource("http");
        }
    }
    // }}}

    // {{{ setMetarDB()
    /**
    * Sets the parameters needed for connecting to the DB, where the location-
    * search is fetching its data from. You need to build a DB with the external
    * tool buildMetarDB first, it fetches the locations and airports from a
    * NOAA-website.
    *
    * @param    string                      $dsn
    * @param    array                       $dbOptions
    * @return   DB_Error|bool
    * @throws   DB_Error
    * @see      DB::parseDSN
    * @access   public
    */
    function setMetarDB($dsn, $dbOptions = array())
    {
        $dsninfo = DB::parseDSN($dsn);
        if (is_array($dsninfo) && !isset($dsninfo["mode"])) {
            $dsninfo["mode"]= 0644;
        }
        
        // Initialize connection to DB and store in object if successful
        $db =  DB::connect($dsninfo, $dbOptions);
        if (DB::isError($db)) {
            return $db;
        }
        $this->_db = $db;

        return true;
    }
    // }}}

    // {{{ setMetarSource()
    /**
    * Sets the source, where the class tries to locate the METAR data
    *
    * Source can be http, ftp or file.
    * An alternate sourcepath can be provided.
    *
    * @param    string                      $source
    * @param    string                      $sourcePath
    * @access   public
    */
    function setMetarSource($source, $sourcePath = "")
    {
        if (in_array($source, array("http", "ftp", "file"))) {
            $this->_source = $source;
        }
        if (strlen($sourcePath)) {
            $this->_sourcePath = $sourcePath;
        } else {
            switch ($source) {
                case "http":
                    $this->_sourcePath = "http://weather.noaa.gov/pub/data/observations/metar/stations/";
                    break;
                case "ftp":
                    $this->_sourcePath = "ftp://weather.noaa.gov/data/observations/metar/stations/";
                    break;
                case "file":
                    $this->_sourcePath = "./";
                    break;
            }
        }
    }
    // }}}

    // {{{ _checkLocationID()
    /**
    * Checks the id for valid values and thus prevents silly requests to METAR server
    *
    * @param    string                      $id
    * @return   PEAR_Error|bool
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_NO_LOCATION
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_INVALID_LOCATION
    * @access   private
    */
    function _checkLocationID($id)
    {
        if (!strlen($id)) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_NO_LOCATION);
        } elseif (!ctype_alpha($id) || (strlen($id) > 4)) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_INVALID_LOCATION);
        }

        return true;
    }
    // }}}

    // {{{ _parseWeatherData()
    /**
    * Parses the data returned by the provided source and caches it
    *    
    * METAR KPIT 091955Z COR 22015G25KT 3/4SM R28L/2600FT TSRA OVC010CB 18/16 A2992 RMK SLP045 T01820159
    *
    * @param    string                      $source
    * @return   PEAR_Error|array
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION
    * @access   private
    */
    function _parseWeatherData($source)
    {
        static $compass;
        static $clouds;
        static $conditions;
        static $sensors;
        if (!isset($compass)) {
            $compass = array(
                "N", "NNE", "NE", "ENE",
                "E", "ESE", "SE", "SSE",
                "S", "SSW", "SW", "WSW",
                "W", "WNW", "NW", "NNW"
            );
            $clouds    = array(
                "skc"         => "sky clear",
                "few"         => "few",
                "sct"         => "scattered",
                "bkn"         => "broken",
                "ovc"         => "overcast",
                "vv"          => "vertical visibility",
                "tcu"         => "Towering Cumulus",
                "cb"          => "Cumulonimbus",
                "clr"         => "clear below 12,000 ft"
            );
            $conditions = array(
                "+"           => "heavy",        "-"           => "light",

                "vc"          => "vicinity",

                "mi"          => "shallow",      "bc"          => "patches",
                "pr"          => "partial",      "ts"          => "thunderstorm",
                "bl"          => "blowing",      "sh"          => "showers",
                "dr"          => "low drifting", "fz"          => "freezing",

                "dz"          => "drizzle",      "ra"          => "rain",
                "sn"          => "snow",         "sg"          => "snow grains",
                "ic"          => "ice crystals", "pe"          => "ice pellets",
                "gr"          => "hail",         "gs"          => "small hail/snow pellets",
                "up"          => "unknown precipitation",

                "br"          => "mist",         "fg"          => "fog",
                "fu"          => "smoke",        "va"          => "volcanic ash",
                "sa"          => "sand",         "hz"          => "haze",
                "py"          => "spray",        "du"          => "widespread dust",

                "sq"          => "squall",       "ss"          => "sandstorm",
                "ds"          => "duststorm",    "po"          => "well developed dust/sand whirls",
                "fc"          => "funnel cloud",

                "+fc"         => "tornado/waterspout"
            );
            $sensors = array(
                "rvrno"     => "Runway Visual Range Detector offline",
                "pwino"     => "Present Weather Identifier offline",
                "pno"       => "Tipping Bucket Rain Gauge offline",
                "fzrano"    => "Freezing Rain Sensor offline",
                "tsno"      => "Lightning Detection System offline",
                "visno_loc" => "2nd Visibility Sensor offline",
                "chino_loc" => "2nd Ceiling Height Indicator offline"
            );
        }
 
        $metarCode = array(
            "report"      => "METAR|SPECI",
            "station"     => "\w{4}",
            "update"      => "(\d{2})?(\d{4})Z",
            "type"        => "AUTO|COR",
            "wind"        => "(\d{3}|VAR|VRB)(\d{2,3})(G(\d{2}))?(\w{2,3})",
            "windVar"     => "(\d{3})V(\d{3})",
            "visibility1" => "\d",
            "visibility2" => "M?(\d{4})|((\d{1,2}|(\d)\/(\d))(SM|KM))|(CAVOK)",
            "runway"      => "R(\d{2})(\w)?\/(P|M)?(\d{4})(FT)?(V(P|M)?(\d{4})(FT)?)?(\w)?",
            "condition"   => "(-|\+|VC)?(MI|BC|PR|TS|BL|SH|DR|FZ)?(DZ|RA|SN|SG|IC|PL|GR|GS|UP)?(BR|FG|FU|VA|DU|SA|HZ|PY)?(PO|SQ|FC|SS|DS)?",
            "clouds"      => "(SKC|CLR|((FEW|SCT|BKN|OVC|VV)(\d{3})(TCU|CB)?))",
            "temperature" => "(M)?(\d{2})\/((M)?(\d{2})|XX|\/\/)?",
            "pressure"    => "(A)(\d{4})|(Q)(\d{4})",
            "nosig"       => "NOSIG",
            "remark"      => "RMK"
        );
        
        $remarks = array(
            "nospeci"     => "NOSPECI",
            "autostation" => "AO(1|2)",
            "presschg"    => "PRESS(R|F)R",
            "seapressure" => "SLP(\d{3}|NO)",
            "1hprecip"    => "P(\d{4})",
            "6hprecip"    => "6(\d{4}|\/{4})",
            "24hprecip"   => "7(\d{4}|\/{4})",
            "snowdepth"   => "4\/(\d{3})",
            "snowequiv"   => "933(\d{3})",
            "cloudtypes"  => "8\/(\d|\/)(\d|\/)(\d|\/)",
            "sunduration" => "98(\d{3})",
            "1htempdew"   => "T(0|1)(\d{3})((0|1)(\d{3}))?",
            "6hmaxtemp"   => "1(0|1)(\d{3})",
            "6hmintemp"   => "2(0|1)(\d{3})",
            "24htemp"     => "4(0|1)(\d{3})(0|1)(\d{3})",
            "3hpresstend" => "5([0-8])(\d{3})",
            "sensors"     => "RVRNO|PWINO|PNO|FZRANO|TSNO|VISNO_LOC|CHINO_LOC",
            "maintain"    => "[\$]"
        );        

        $data = @file($source);

        // Check for correct data, 2 lines in size
        if (!$data || !is_array($data) || sizeof($data) < 2) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA);
        } elseif (sizeof($data) > 2) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION);
        } else {
            if (SERVICES_WEATHER_DEBUG) {
                echo $data[0].$data[1];
            }
            // Ok, we have correct data, start with parsing the first line for the last update
            $weatherData = array();
            $weatherData["station"] = "";
            $weatherData["update"]  = strtotime(trim($data[0])." GMT");
            // and prepare the second line for stepping through
            $metar = explode(" ", trim($data[1]));

            for ($i = 0; $i < sizeof($metar); $i++) {
                // Check for whitespace and step loop, if nothing's there
                $metar[$i] = trim($metar[$i]);
                if (!strlen($metar[$i])) {
                    continue;
                }

                if (SERVICES_WEATHER_DEBUG) {
                    $tab = str_repeat("\t", 2 - floor((strlen($metar[$i]) + 2) / 8));
                    echo "\"".$metar[$i]."\"".$tab."-> ";
                }

                $found = false;
                foreach ($metarCode as $key => $regexp) {
                    // Check if current code matches current metar snippet
                    if (($found = preg_match("/^".$regexp."$/i", $metar[$i], $result)) == true) {
                        switch ($key) {
                            case "station":
                                $weatherData["station"] = $result[0];
                                unset($metarCode["station"]);
                                break;
                            case "wind":
                                // Parse wind data, first the speed, convert from kt to chosen unit
                                $weatherData["wind"] = $this->convertSpeed($result[2], strtolower($result[5]), "mph");
                                if ($result[1] == "VAR" || $result[1] == "VRB") {
                                    // Variable winds
                                    $weatherData["windDegrees"]   = "Variable";
                                    $weatherData["windDirection"] = "Variable";
                                } else {
                                    // Save wind degree and calc direction
                                    $weatherData["windDegrees"]   = $result[1];
                                    $weatherData["windDirection"] = $compass[round($result[1] / 22.5) % 16];
                                }
                                if (is_numeric($result[4])) {
                                    // Wind with gusts...
                                    $weatherData["windGust"] = $this->convertSpeed($result[4], strtolower($result[5]), "mph");
                                }
                                // We got that, unset
                                unset($metarCode["wind"]);
                                break;
                            case "windVar":
                                // Once more wind, now variability around the current wind-direction
                                $weatherData["windVariability"] = array("from" => $result[1], "to" => $result[2]);
                                unset($metarCode["windVar"]);
                                break;
                            case "visibility1":
                                // Visibility will come as x y/z, first the single digit part
                                $weatherData["visibility"] = $result[0];
                                unset($metarCode["visibility1"]);
                                break;
                            case "visibility2":
                                if (is_numeric($result[1]) && ($result[1] == 9999)) {
                                    // Upper limit of visibility range
                                    $visibility = $this->convertDistance(10, "km", "sm");
                                    $weatherData["visQualifier"] = "BEYOND";
                                } elseif (is_numeric($result[1])) {
                                    // 4-digit visibility in m
                                    $visibility = $this->convertDistance(($result[1]/1000), "km", "sm");
                                    $weatherData["visQualifier"] = "AT";
                                } elseif (!isset($result[7]) || $result[7] != "CAVOK") {
                                    if (is_numeric($result[3])) {
                                        // visibility as one/two-digit number
                                        $visibility = $this->convertDistance($result[3], $result[6], "sm");
                                        $weatherData["visQualifier"] = "AT";
                                    } else {
                                        // the y/z part, add if we had a x part (see visibility1)
                                        $visibility = $this->convertDistance($result[4] / $result[5], $result[6], "sm");
                                        if (isset($weatherData["visibility"])) {
                                            $visibility += $weatherData["visibility"];
                                        }
                                        if ($result[0]{0} == "M") {
                                            $weatherData["visQualifier"] = "BELOW";
                                        } else {
                                            $weatherData["visQualifier"] = "AT";
                                        } 
                                    }
                                } else {
                                    $weatherData["visQualifier"] = "BEYOND";
                                    $visibility               = $this->convertDistance(10, "km", "sm");
                                    $weatherData["clouds"]    = array("amount" => "none", "height" => "below 5000ft");
                                    $weatherData["condition"] = "no significant weather";
                                }
                                $weatherData["visibility"] = $visibility;
                                unset($metarCode["visibility2"]);
                                break;
                            case "condition":
                                // First some basic setups
                                if (!isset($weatherData["condition"])) {
                                    $weatherData["condition"] = "";
                                } elseif (strlen($weatherData["condition"]) > 0) {
                                    $weatherData["condition"] .= ",";
                                }

                                if (in_array(strtolower($result[0]), $conditions)) {
                                    // First try matching the complete string
                                    $weatherData["condition"] .= " ".$conditions[strtolower($result[0])];
                                } else {
                                    // No luck, match part by part
                                    for ($c = 1; $c < sizeof($result); $c++) {
                                        if (strlen($result[$c]) > 0) {
                                            $weatherData["condition"] .= " ".$conditions[strtolower($result[$c])];
                                        }
                                    }
                                }
                                $weatherData["condition"] = trim($weatherData["condition"]);
                                break;
                            case "clouds":
                                if (!isset($weatherData["clouds"])) {
                                    $weatherData["clouds"] = array();
                                }

                                if (sizeof($result) == 5) {
                                    // Only amount and height
                                    $cloud = array("amount" => $clouds[strtolower($result[3])], "height" => ($result[4]*100));
                                }
                                elseif (sizeof($result) == 6) {
                                    // Amount, height and type
                                    $cloud = array("amount" => $clouds[strtolower($result[3])], "height" => ($result[4]*100), "type" => $clouds[strtolower($result[5])]);
                                }
                                else {
                                    // SKC or CLR
                                    $cloud = array("amount" => $clouds[strtolower($result[0])]);
                                }
                                $weatherData["clouds"][] = $cloud;
                                break;
                            case "temperature":
                                // normal temperature in first part
                                // negative value
                                if ($result[1] == "M") {
                                    $result[2] *= -1;
                                }
                                $weatherData["temperature"] = $this->convertTemperature($result[2], "c", "f");
                                if (sizeof($result) > 4) {
                                    // same for dewpoint
                                    if ($result[4] == "M") {
                                        $result[5] *= -1;
                                    }
                                    $weatherData["dewPoint"] = $this->convertTemperature($result[5], "c", "f");
                                    $weatherData["humidity"] = $this->calculateHumidity($result[2], $result[5]);
                                }
                                if (isset($weatherData["wind"])) {
                                    // Now calculate windchill from temperature and windspeed
                                    $weatherData["feltTemperature"] = $this->calculateWindChill($weatherData["temperature"], $weatherData["wind"]);
                                }
                                unset($metarCode["temperature"]);
                                break;
                            case "pressure":
                                if ($result[1] == "A") {
                                    // Pressure provided in inches
                                    $weatherData["pressure"] = $result[2] / 100;
                                } elseif ($result[3] == "Q") {
                                    // ... in hectopascal
                                    $weatherData["pressure"] = $this->convertPressure($result[4], "hpa", "in");
                                }
                                unset($metarCode["pressure"]);
                                break;
                            case "nosig":
                            case "nospeci":
                                // No change during the last hour
                                if (!isset($weatherData["remark"])) {
                                    $weatherData["remark"] = array();
                                }
                                $weatherData["remark"]["nosig"] = "No changes in weather conditions";
                                unset($metarCode[$key]);
                                break;
                            case "remark":
                                // Remark part begins
                                $metarCode = $remarks;
                                if (!isset($weatherData["remark"])) {
                                    $weatherData["remark"] = array();
                                }
                                break;
                            case "autostation":
                                // Which autostation do we have here?
                                if ($result[1] == 0) {
                                    $weatherData["remark"]["autostation"] = "Automatic weatherstation w/o precipitation discriminator";
                                } else {
                                    $weatherData["remark"]["autostation"] = "Automatic weatherstation w/ precipitation discriminator";
                                }
                                unset($metarCode["autostation"]);
                                break;
                            case "presschg":
                                // Decoding for rapid pressure changes
                                if (strtolower($result[1]) == "r") {
                                    $weatherData["remark"]["presschg"] = "Pressure rising rapidly";
                                } else {
                                    $weatherData["remark"]["presschg"] = "Pressure falling rapidly";
                                }
                                unset($metarCode["presschg"]);
                                break;
                            case "seapressure":
                                // Pressure at sea level (delivered in hpa)
                                // Decoding is a bit obscure as 982 gets 998.2
                                // whereas 113 becomes 1113 -> no real rule here
                                if (strtolower($result[1]) != "no") {
                                    if ($result[1] > 500) {
                                        $press = 900 + round($result[1] / 100, 1);
                                    } else {
                                        $press = 1000 + $result[1];
                                    }
                                    $weatherData["remark"]["seapressure"] = $this->convertPressure($press, "hpa", "in");
                                }
                                unset($metarCode["seapressure"]);
                                break;
                            case "1hprecip":
                                // Precipitation for the last hour in inches
                                if (!isset($weatherData["precipitation"])) {
                                    $weatherData["precipitation"] = array();
                                }
                                if (!is_numeric($result[1])) {
                                    $precip = "indeterminable";
                                } elseif ($result[1] == "0000") {
                                    $precip = "traceable";
                                }else {
                                    $precip = $result[1] / 100;
                                }
                                $weatherData["precipitation"][] = array(
                                    "amount" => $precip,
                                    "hours"  => "1" 
                                );
                                unset($metarCode["1hprecip"]);
                                break;
                            case "6hprecip":
                                // Same for last 3 resp. 6 hours... no way to determine
                                // which report this is, so keeping the text general
                                if (!isset($weatherData["precipitation"])) {
                                    $weatherData["precipitation"] = array();
                                }
                                if (!is_numeric($result[1])) {
                                    $precip = "indeterminable";
                                } elseif ($result[1] == "0000") {
                                    $precip = "traceable";
                                }else {
                                    $precip = $result[1] / 100;
                                }
                                $weatherData["precipitation"][] = array(
                                    "amount" => $precip,
                                    "hours"  => "3/6" 
                                );
                                unset($metarCode["6hprecip"]);
                                break;
                            case "24hprecip":
                                // And the same for the last 24 hours
                                if (!isset($weatherData["precipitation"])) {
                                    $weatherData["precipitation"] = array();
                                }
                                if (!is_numeric($result[1])) {
                                    $precip = "indeterminable";
                                } elseif ($result[1] == "0000") {
                                    $precip = "traceable";
                                }else {
                                    $precip = $result[1] / 100;
                                }
                                $weatherData["precipitation"][] = array(
                                    "amount" => $precip,
                                    "hours"  => "24" 
                                );
                                unset($metarCode["24hprecip"]);
                                break;
                            case "snowdepth":
                                // Snow depth in inches
                                $weatherData["remark"]["snowdepth"] = $result[1];
                                unset($metarCode["snowdepth"]);
                                break;
                            case "snowequiv":
                                // Same for equivalent in Water... (inches)
                                $weatherData["remark"]["snowequiv"] = $result[1] / 10;
                                unset($metarCode["snowequiv"]);
                                break;
                            case "cloudtypes":
                                // Cloud types, haven't found a way for decent decoding (yet)
                                unset($metarCode["cloudtypes"]);
                                break;
                            case "sunduration":
                                // Duration of sunshine (in minutes)
                                $weatherData["remark"]["sunduration"] = "Total minutes of sunshine: ".$result[1];
                                unset($metarCode["sunduration"]);
                                break;
                            case "1htempdew":
                                // Temperatures in the last hour in C
                                if ($result[1] == "1") {
                                    $result[2] *= -1;
                                }
                                $weatherData["remark"]["1htemp"] = $this->convertTemperature($result[2] / 10, "c", "f");
                                
                                if (sizeof($result) > 3) {
                                    // same for dewpoint
                                    if ($result[4] == "1") {
                                        $result[5] *= -1;
                                    }
                                    $weatherData["remark"]["1hdew"] = $this->convertTemperature($result[5] / 10, "c", "f");
                                }
                                unset($metarCode["1htempdew"]);
                                break;
                            case "6hmaxtemp":
                                // Max temperature in the last 6 hours in C
                                if ($result[1] == "1") {
                                    $result[2] *= -1;
                                }
                                $weatherData["remark"]["6hmaxtemp"] = $this->convertTemperature($result[2] / 10, "c", "f");
                                unset($metarCode["6hmaxtemp"]);
                                break;
                            case "6hmintemp":
                                // Min temperature in the last 6 hours in C
                                if ($result[1] == "1") {
                                    $result[2] *= -1;
                                }
                                $weatherData["remark"]["6hmintemp"] = $this->convertTemperature($result[2] / 10, "c", "f");
                                unset($metarCode["6hmintemp"]);
                                break;
                            case "24htemp":
                                // Max/Min temperatures in the last 24 hours in C
                                if ($result[1] == "1") {
                                    $result[2] *= -1;
                                }
                                $weatherData["remark"]["24hmaxtemp"] = $this->convertTemperature($result[2] / 10, "c", "f");

                                if ($result[3] == "1") {
                                    $result[4] *= -1;
                                }
                                $weatherData["remark"]["24hmintemp"] = $this->convertTemperature($result[4] / 10, "c", "f");
                                unset($metarCode["24htemp"]);
                                break;
                            case "3hpresstend":
                                // We don't save the pressure during the day, so no decoding
                                // possible, sorry
                                unset($metarCode["3hpresstend"]);
                                break;
                            case "sensors":
                                // We may have multiple broken sensors, so do not unset
                                if (!isset($weatherData["remark"]["sensors"])) {
                                    $weatherData["remark"]["sensors"] = array();
                                }
                                $weatherData["remark"]["sensors"][strtolower($result[0])] = $sensors[strtolower($result[0])];
                                break;
                            case "maintain":
                                $weatherData["remark"]["maintain"] = "Maintainance needed";
                                unset($metarCode["maintain"]);
                                break;
                            default:
                                // Do nothing, just prevent further matching
                                unset($metarCode[$key]);
                                break;
                        }
                        if (SERVICES_WEATHER_DEBUG) {
                            echo $key."\n";
                        }
                        break;
                    }
                }
                if (!$found) {
                    if (SERVICES_WEATHER_DEBUG) {
                        echo "n/a\n";
                    }
                    if (!isset($weatherData["noparse"])) {
                        $weatherData["noparse"] = array();
                    }
                    $weatherData["noparse"][] = $metar[$i];
                }
            }
        }
        if (isset($weatherData["noparse"])) {
            $weatherData["noparse"] = implode(" ",  $weatherData["noparse"]);
        }

        return $weatherData;
    }
    // }}}

    // {{{ searchLocation()
    /**
    * Searches IDs for given location, returns array of possible locations or single ID
    *
    * @param    string|array                $location
    * @param    bool                        $useFirst       If set, first ID of result-array is returned
    * @return   PEAR_Error|array|string
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_DB_NOT_CONNECTED
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_INVALID_LOCATION
    * @access   public
    */
    function searchLocation($location, $useFirst = false)
    {
        if (!isset($this->_db) || !DB::isConnection($this->_db)) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_DB_NOT_CONNECTED);
        }
        
        if (is_string($location)) {
            // Try to part search string in name, state and country part
            // and build where clause from it for the select
            $location = explode(",", $location);
            if (sizeof($location) >= 1) {
                $where  = "LOWER(name) LIKE '%".strtolower(trim($location[0]))."%'";
            }
            if (sizeof($location) == 2) {
                $where .= " AND LOWER(country) LIKE '%".strtolower(trim($location[1]))."%'";
            } elseif (sizeof($location) == 3) {
                $where .= " AND LOWER(state) LIKE '%".strtolower(trim($location[1]))."%'";
                $where .= " AND LOWER(country) LIKE '%".strtolower(trim($location[2]))."%'";
            }
                
            // Create select, locations with ICAO first
            $select = "SELECT icao, name, state, country, latitude, longitude ".
                      "FROM metarLocations ".
                      "WHERE ".$where." ".
                      "ORDER BY icao DESC";
            $result = $this->_db->query($select);
            // Check result for validity
            if (DB::isError($result)) {
                return $result;
            } elseif (get_class($result) != "db_result" || $result->numRows() == 0) {
                return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION);
            }
            
            // Result is valid, start preparing the return
            $icao = array();
            while (($row = $result->fetchRow(DB_FETCHMODE_ASSOC)) != null) {
                $locicao = $row["icao"];
                // First the name of the location
                if (!strlen($row["state"])) {
                    $locname = $row["name"].", ".$row["country"];
                } else {
                    $locname = $row["name"].", ".$row["state"].", ".$row["country"];
                }
                if ($locicao != "----") {
                    // We have a location with ICAO
                    $icao[$locicao] = $locname;
                } else {
                    // No ICAO, try finding the nearest airport
                    $locicao = $this->searchAirport($row["latitude"], $row["longitude"]);
                    if (!isset($icao[$locicao])) {
                        $icao[$locicao] = $locname;
                    }
                }
            }
            // Only one result? Return as string
            if (sizeof($icao) == 1) {
                $icao = key($icao);
            }
        } elseif (is_array($location)) {
            // Location was provided as coordinates, search nearest airport
            $icao = $this->searchAirport($location[0], $location[1]);
        } else {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_INVALID_LOCATION);
        }

        return $icao;
    }
    // }}}

    // {{{ searchLocationByCountry()
    /**
    * Returns IDs with location-name for a given country or all available countries, if no value was given 
    *
    * @param    string                      $country
    * @return   PEAR_Error|array
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_DB_NOT_CONNECTED
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA
    * @access   public
    */
    function searchLocationByCountry($country = "")
    {
        if (!isset($this->_db) || !DB::isConnection($this->_db)) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_DB_NOT_CONNECTED);
        }

        // Return the available countries as no country was given
        if (!strlen($country)) {
            $select = "SELECT DISTINCT(country) ".
                      "FROM metarAirports ".
                      "ORDER BY country ASC";
            $countries = $this->_db->getCol($select);

            // As $countries is either an error or the true result,
            // we can just return it
            return $countries;
        }

        // Now for the real search
        $select = "SELECT icao, name, state, country ".
                  "FROM metarAirports ".
                  "WHERE LOWER(country) LIKE '%".strtolower(trim($country))."%' ".
                  "ORDER BY name ASC";
        $result = $this->_db->query($select);
        // Check result for validity
        if (DB::isError($result)) {
            return $result;
        } elseif (get_class($result) != "db_result" || $result->numRows() == 0) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION);
        }

        // Construct the result
        $locations = array();
        while (($row = $result->fetchRow(DB_FETCHMODE_ASSOC)) != null) {
            $locicao = $row["icao"];
            // First the name of the location
            if (!strlen($row["state"])) {
                $locname = $row["name"].", ".$row["country"];
            } else {
                $locname = $row["name"].", ".$row["state"].", ".$row["country"];
            }
            $locations[$locicao] = $locname;
        }

        return $locations;
    }
    // }}}

    // {{{ searchAirport()
    /**
    * Searches the nearest airport(s) for given coordinates, returns array of IDs or single ID
    *
    * @param    float                       $latitude
    * @param    float                       $longitude
    * @param    int                         $numResults
    * @return   PEAR_Error|array|string
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_DB_NOT_CONNECTED
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_INVALID_LOCATION
    * @access   public
    */
    function searchAirport($latitude, $longitude, $numResults = 1)
    {
        if (!isset($this->_db) || !DB::isConnection($this->_db)) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_DB_NOT_CONNECTED);
        }
        if (!is_numeric($latitude) || !is_numeric($longitude)) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_INVALID_LOCATION);
        }           
        
        // Get all airports
        $select = "SELECT icao, x, y, z FROM metarAirports";
        $result = $this->_db->query($select);
        if (DB::isError($result)) {
            return $result;
        } elseif (get_class($result) != "db_result" || $result->numRows() == 0) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION);
        }

        // Result is valid, start search
        // Initialize values
        $min_dist = null;
        $query    = $this->polar2cartesian($latitude, $longitude);
        $search   = array("dist" => array(), "icao" => array());
        while (($row = $result->fetchRow(DB_FETCHMODE_ASSOC)) != null) {
            $icao = $row["icao"];
            $air  = array($row["x"], $row["y"], $row["z"]);

            $dist = 0;
            $d = 0;
            // Calculate distance of query and current airport
            // break off, if distance is larger than current $min_dist
            for($d; $d < sizeof($air); $d++) {
                $t = $air[$d] - $query[$d];
                $dist += pow($t, 2);
                if ($min_dist != null && $dist > $min_dist) {
                    break;
                }
            }

            if ($d >= sizeof($air)) {
                // Ok, current airport is one of the nearer locations
                // add to result-array
                $search["dist"][] = $dist;
                $search["icao"][] = $icao;
                // Sort array for distance
                array_multisort($search["dist"], SORT_NUMERIC, SORT_ASC, $search["icao"], SORT_STRING, SORT_ASC);
                // If array is larger then desired results, chop off last one
                if (sizeof($search["dist"]) > $numResults) {
                    array_pop($search["dist"]);
                    array_pop($search["icao"]);
                }
                $min_dist = max($search["dist"]);
            }
        }
        if ($numResults == 1) {
            // Only one result wanted, return as string
            return $search["icao"][0];
        } elseif ($numResults > 1) {
            // Return found locations
            return $search["icao"];
        } else {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION);
        }
    }
    // }}}

    // {{{ getUnits()
    /**
    * Returns the units for the current query
    *
    * @param    string                      $id
    * @param    string                      $unitsFormat
    * @return   array
    * @deprecated
    * @access   public
    */
    function getUnits($id = null, $unitsFormat = "")
    {
        return $this->getUnitsFormat($unitsFormat);
    }
    // }}}

    // {{{ getLocation()
    /**
    * Returns the data for the location belonging to the ID
    *
    * @param    string                      $id
    * @return   PEAR_Error|array
    * @throws   PEAR_Error
    * @access   public
    */
    function getLocation($id = "")
    {
        $status = $this->_checkLocationID($id);

        if (Services_Weather::isError($status)) {
            return $status;
        }

        $locationReturn = array();

        if ($this->_cacheEnabled && ($location = $this->_cache->get("METAR-".$id, "location"))) {
            // Grab stuff from cache
            $this->_location = $location;
            $locationReturn["cache"] = "HIT";
        } elseif (isset($this->_db) && DB::isConnection($this->_db)) {
            // Get data from DB
            $select = "SELECT icao, name, state, country, latitude, longitude, elevation ".
                      "FROM metarAirports WHERE icao='".$id."'";
            $result = $this->_db->query($select);

            if (DB::isError($result)) {
                return $result;
            } elseif (get_class($result) != "db_result" || $result->numRows() == 0) {
                return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION);
            }
            // Result is ok, put things into object
            $this->_location = $result->fetchRow(DB_FETCHMODE_ASSOC);

            if ($this->_cacheEnabled) {
                // ...and cache it
                $expire = constant("SERVICES_WEATHER_EXPIRES_LOCATION");
                $this->_cache->extSave("METAR-".$id, $this->_location, "", $expire, "location");
            }

            $locationReturn["cache"] = "MISS";
        } else {
            $this->_location = array(
                "name"      => $id,
                "state"     => "",
                "country"   => "",
                "latitude"  => "",
                "longitude" => "",
                "elevation" => ""
            );
        }
        // Stuff name-string together
        if (strlen($this->_location["state"]) && strlen($this->_location["country"])) {
            $locname = $this->_location["name"].", ".$this->_location["state"].", ".$this->_location["country"];
        } elseif (strlen($this->_location["country"])) {
            $locname = $this->_location["name"].", ".$this->_location["country"];
        } else {
            $locname = $this->_location["name"];
        }
        $locationReturn["name"]      = $locname;
        $locationReturn["latitude"]  = $this->_location["latitude"];
        $locationReturn["longitude"] = $this->_location["longitude"];
        $locationReturn["elevation"] = $this->_location["elevation"];

        return $locationReturn;
    }
    // }}}

    // {{{ getWeather()
    /**
    * Returns the weather-data for the supplied location
    *
    * @param    string                      $id
    * @param    string                      $unitsFormat
    * @return   PHP_Error|array
    * @throws   PHP_Error
    * @access   public
    */
    function getWeather($id = "", $unitsFormat = "")
    {
        $id     = strtoupper($id);
        $status = $this->_checkLocationID($id);

        if (Services_Weather::isError($status)) {
            return $status;
        }

        // Get other data
        $units    = $this->getUnitsFormat($unitsFormat);
        $location = $this->getLocation($id);

        if ($this->_cacheEnabled && ($weather = $this->_cache->get("METAR-".$id, "weather"))) {
            // Wee... it was cached, let's have it...
            $weatherReturn  = $weather;
            $this->_weather = $weatherReturn;
            $weatherReturn["cache"] = "HIT";
        } else {
            // Set the source
            if ($this->_source == "file") {
                $source = realpath($this->_sourcePath.$id.".TXT");
            } else {
                $source = $this->_sourcePath.$id.".TXT";
            }

            // Download and parse weather
            $weatherReturn  = $this->_parseWeatherData($source, $units);

            if (Services_Weather::isError($weatherReturn)) {
                return $weatherReturn;
            }
            if ($this->_cacheEnabled) {
                // Cache weather
                $expire = constant("SERVICES_WEATHER_EXPIRES_WEATHER");
                $this->_cache->extSave("METAR-".$id, $weatherReturn, $unitsFormat, $expire, "weather");
            }
            $this->_weather = $weatherReturn;
            $weatherReturn["cache"] = "MISS";
        }

        if (isset($weatherReturn["remark"])) {
            foreach ($weatherReturn["remark"] as $key => $val) {
                switch ($key) {
                    case "seapressure":
                        $newVal = $this->convertPressure($val, "in", $units["pres"]);
                        break;
                    case "snowdepth":
                    case "snowequiv":
                        $newVal = $this->convertPressure($val, "in", $units["rain"]);
                        break;
                    case "1htemp":
                    case "1hdew":
                    case "6hmaxtemp":
                    case "6hmintemp":
                    case "24hmaxtemp":
                    case "24hmintemp":
                        $newVal = $this->convertTemperature($val, "f", $units["temp"]);
                        break;
                    default:
                        continue 2;
                        break;
                }
                $weatherReturn["remark"][$key] = $newVal;
            }
        }

        foreach ($weatherReturn as $key => $val) {
            switch ($key) {
                case "station":
                    $newVal = $location["name"];
                    break;
                case "update":
                    $newVal = gmdate(trim($this->_dateFormat." ".$this->_timeFormat), $val);
                    break;
                case "wind":
                case "windGust":
                    $newVal = $this->convertSpeed($val, "mph", $units["wind"]);
                    break;
                case "visibility":
                    $newVal = $this->convertDistance($val, "sm", $units["vis"]);
                    break;
                case "temperature":
                case "dewPoint":
                case "feltTemperature":
                    $newVal = $this->convertTemperature($val, "f", $units["temp"]);
                    break;
                case "pressure":
                    $newVal = $this->convertPressure($val, "in", $units["pres"]);
                    break;
                case "precipitation":
                    $newVal = array();
                    for ($p = 0; $p < sizeof($val); $p++) {
                        $newVal[$p] = array();
                        if (is_numeric($val[$p]["amount"])) {
                            $newVal[$p]["amount"] = $this->convertPressure($val[$p]["amount"], "in", $units["rain"]);
                        } else {
                            $newVal[$p]["amount"] = $val[$p]["amount"];
                        }
                        $newVal[$p]["hours"]  = $val[$p]["hours"];
                    }
                    break;
/*
                case "remark":
                    $newVal = implode(", ", $val);
                    break;
*/
                default:
                    continue 2;
                    break;
            }
            $weatherReturn[$key] = $newVal;
        }

        return $weatherReturn;
    }
    // }}}
    
    // {{{ getForecast()
    /**
    * METAR has no forecast per se, so this function is just for
    * compatibility purposes.
    *
    * @param    string                      $int
    * @param    int                         $days
    * @param    string                      $unitsFormat
    * @return   bool
    * @access   public
    * @deprecated
    */
    function getForecast($id = null, $days = null, $unitsFormat = null)
    {
        return false;
    }
    // }}}
}
// }}}
?>
