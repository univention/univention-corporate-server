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
// $Id: Ejse.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once "Services/Weather/Common.php";

// {{{ class Services_Weather_Ejse
/**
* PEAR::Services_Weather_Ejse
*
* This class acts as an interface to the soap service of EJSE. It retrieves
* current weather data and forecasts based on postal codes (ZIP).
*
* Currently this service is only available for US territory.
*
* For a working example, please take a look at
*     docs/Services_Weather/examples/ejse-basic.php
*
* @author       Alexander Wirtz <alex@pc4p.net>
* @link         http://www.ejse.com/services/weather_xml_web_services.htm
* @example      docs/Services_Weather/examples/ejse-basic.php
* @package      Services_Weather
* @license      http://www.php.net/license/2_02.txt
* @version      1.2
*/
class Services_Weather_Ejse extends Services_Weather_Common {

    // {{{ properties
    /**
    * WSDL object, provided by EJSE
    *
    * @var      object                      $_wsdl
    * @access   private
    */
    var $_wsdl;

    /**
    * SOAP object to access weather data, provided by EJSE
    *
    * @var      object                      $_weaterSoap
    * @access   private
    */
    var $_weatherSoap;
    // }}}

    // {{{ constructor
    /**
    * Constructor
    *
    * Requires SOAP to be installed
    *
    * @param    array                       $options
    * @param    mixed                       $error
    * @throws   PEAR_Error
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA
    * @see      Science_Weather::Science_Weather
    * @access   private
    */
    function Services_Weather_Ejse($options, &$error)
    {
        $perror = null;
        $this->Services_Weather_Common($options, $perror);
        if (Services_Weather::isError($perror)) {
            $error = $perror;
            return;
        }

        include_once "SOAP/Client.php";
        $this->_wsdl = new SOAP_WSDL("http://www.ejse.com/WeatherService/Service.asmx?WSDL");
        if (isset($this->_wsdl->fault) && Services_Weather::isError($this->_wsdl->fault)) {
            $error = Services_Weather::raiseError(SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA);
            return;
        }

        eval($this->_wsdl->generateAllProxies());
        if (!class_exists("WebService_Service_ServiceSoap")) {
            $error = Services_Weather::raiseError(SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA);
            return;
        }

        $this->_weatherSoap = &new WebService_Service_ServiceSoap;
    }
    // }}}

    // {{{ _checkLocationID()
    /**
    * Checks the id for valid values and thus prevents silly requests to EJSE server
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
        } elseif (!ctype_digit($id) || (strlen($id) != 5)) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_INVALID_LOCATION);
        }

        return true;
    }
    // }}}

    // {{{ searchLocation()
    /**
    * EJSE offers no search function to date, so this function is disabled.
    * Maybe this is the place to interface to some online postcode service... 
    *
    * @param    string                      $location
    * @param    bool                        $useFirst
    * @return   bool
    * @access   public
    * @deprecated
    */
    function searchLocation($location = null, $useFirst = null)
    {
        return $false;
    }
    // }}}

    // {{{ searchLocationByCountry()
    /**
    * EJSE offers no search function to date, so this function is disabled.
    * Maybe this is the place to interface to some online postcode service... 
    *
    * @param    string                      $country
    * @return   bool
    * @access   public
    * @deprecated
    */
    function searchLocationByCountry($country = null)
    {
        return $false;
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

        if ($this->_cacheEnabled && ($weather = $this->_cache->get($id, "weather"))) {
            // Get data from cache
            $this->_weather = $weather;
            $locationReturn["cache"] = "HIT";
        } else {
            $weather = $this->_weatherSoap->getWeatherInfo($id);

            if (Services_Weather::isError($weather)) {
                return $weather;
            }

            $this->_weather = $weather;

            if ($this->_cacheEnabled) {
                // ...and cache it
                $expire = constant("SERVICES_WEATHER_EXPIRES_WEATHER");
                $this->_cache->extSave($id, $this->_weather, "", $expire, "weather");
            }
            $locationReturn["cache"] = "MISS";
        }
        $locationReturn["name"] = $this->_weather->Location;

        return $locationReturn;
    }
    // }}}

    // {{{ getWeather()
    /**
    * Returns the weather-data for the supplied location
    *
    * @param    string                      $id
    * @param    string                      $unitsFormat
    * @return   PEAR_Error|array
    * @throws   PEAR_Error
    * @access   public
    */
    function getWeather($id = "", $unitsFormat = "")
    {
        $status = $this->_checkLocationID($id);

        if (Services_Weather::isError($status)) {
            return $status;
        }

        // Get other data
        $units    = $this->getUnitsFormat($unitsFormat);

        $weatherReturn = array();
        if ($this->_cacheEnabled && ($weather = $this->_cache->get($id, "weather"))) {
            // Same procedure...
            $this->_weather = $weather;
            $weatherReturn["cache"] = "HIT";
        } else {
            // ...as last function
            $weather = $this->_weatherSoap->getWeatherInfo($id);

            if (Services_Weather::isError($weather)) {
                return $weather;
            }

            $this->_weather = $weather;

            if ($this->_cacheEnabled) {
                // ...and cache it
                $expire = constant("SERVICES_WEATHER_EXPIRES_WEATHER");
                $this->_cache->extSave($id, $this->_weather, "", $expire, "weather");
            }
            $weatherReturn["cache"] = "MISS";
        }

        if (!isset($compass)) {
            // Yes, NNE and the likes are multiples of 22.5, but as the other
            // services return integers for this value, these directions are
            // rounded up
            $compass = array(
                "north"             => array("N",     0),
                "north northeast"   => array("NNE",  23),
                "northeast"         => array("NE",   45),
                "east northeast"    => array("ENE",  68),
                "east"              => array("E",    90),
                "east southeast"    => array("ESE", 113),
                "southeast"         => array("SE",  135),
                "south southeast"   => array("SSE", 158),
                "south"             => array("S",   180),
                "south southwest"   => array("SSW", 203),
                "southwest"         => array("SW",  225),
                "west southwest"    => array("WSW", 248),
                "west"              => array("W",   270),
                "west northwest"    => array("WNW", 293),
                "northwest"         => array("NW",  315),
                "north northwest"   => array("NNW", 338)
            );
        }

        preg_match("/(\w+) (\d+), (\d+), at (\d+:\d+ \wM) [^\(]+(\(([^\)]+)\))?/", $this->_weather->LastUpdated, $update);
        if (isset($update[5])) {
            $timestring = $update[6];
        } else {
            $timestring = $update[2]." ".$update[1]." ".$update[3]." ".$update[4]." EST";
        }
        $weatherReturn["update"]            = gmdate(trim($this->_dateFormat." ".$this->_timeFormat), strtotime($timestring));
        $weatherReturn["station"]           = $this->_weather->ReportedAt;
        $weatherReturn["conditionIcon"]     = $this->_weather->IconIndex;
        preg_match("/(-?\d+)\D+/", $this->_weather->Temprature, $temperature);        
        $weatherReturn["temperature"]       = $this->convertTemperature($temperature[1], "f", $units["temp"]);
        preg_match("/(-?\d+)\D+/", $this->_weather->FeelsLike, $feltTemperature);        
        $weatherReturn["feltTemperature"]   = $this->convertTemperature($feltTemperature[1], "f", $units["temp"]);
        $weatherReturn["condition"]         = $this->_weather->Forecast;
        if (preg_match("/([\d\.]+)\D+/", $this->_weather->Visibility, $visibility)) { 
            $weatherReturn["visibility"]    = $this->convertDistance($visibility[1], "sm", $units["vis"]);
        } else {
            $weatherReturn["visibility"]    = trim($this->_weather->Visibility);
        } 
        preg_match("/([\d\.]+) inches and (\w+)/", $this->_weather->Pressure, $pressure);
        $weatherReturn["pressure"]          = $this->convertPressure($pressure[1], "in", $units["pres"]);        
        $weatherReturn["pressureTrend"]     = $pressure[2];
        preg_match("/(-?\d+)\D+/", $this->_weather->DewPoint, $dewPoint);      
        $weatherReturn["dewPoint"]          = $this->convertTemperature($dewPoint[1], "f", $units["temp"]);
        preg_match("/(\d+) (\w+)/", $this->_weather->UVIndex, $uvIndex);
        $weatherReturn["uvIndex"]           = $uvIndex[1];
        $weatherReturn["uvText"]            = $uvIndex[2];
        $weatherReturn["humidity"]          = str_replace("%", "", $this->_weather->Humidity);
        if (preg_match("/From the ([\w\ ]+) at ([\d\.]+) (gusting to ([\d\.]+) )?mph/", $this->_weather->Wind, $wind)) {
            $weatherReturn["wind"]              = $this->convertSpeed($wind[2], "mph", $units["wind"]);
            if (isset($wind[4])) {
                $weatherReturn["windGust"]      = $this->convertSpeed($wind[4], "mph", $units["wind"]);
            }
            $weatherReturn["windDegrees"]       = $compass[strtolower($wind[1])][1];
            $weatherReturn["windDirection"]     = $compass[strtolower($wind[1])][0];
        } elseif (strtolower($this->_weather->Wind) == "calm") {
            $weatherReturn["wind"]          = 0;
            $weatherReturn["windDegrees"]   = 0;
            $weatherReturn["windDirection"] = "CALM";
        }

        return $weatherReturn;
    }
    // }}}

    // {{{ getForecast()
    /**
    * Get the forecast for the next days
    *
    * @param    string                      $int
    * @param    int                         $days           Values between 1 and 9
    * @param    string                      $unitsFormat
    * @return   PEAR_Error|array
    * @throws   PEAR_Error
    * @access   public
    */
    function getForecast($id = "", $days = 2, $unitsFormat = "")
    {
        $status = $this->_checkLocationID($id);

        if (Services_Weather::isError($status)) {
            return $status;
        }
        if (!in_array($days, range(1, 9))) {
            $days = 2;
        }

        // Get other data
        $units    = $this->getUnitsFormat($unitsFormat);

        $forecastReturn = array();
        if ($this->_cacheEnabled && ($forecast = $this->_cache->get($id, "forecast"))) {
            // Same procedure...
            $this->_forecast = $forecast;
            $forecastReturn["cache"] = "HIT";
        } else {
            // ...as last function
            $forecast = $this->_weatherSoap->GetNineDayForecastInfo($id);

            if (Services_Weather::isError($forecast)) {
                return $forecast;
            }

            $this->_forecast = $forecast;

            if ($this->_cacheEnabled) {
                // ...and cache it
                $expire = constant("SERVICES_WEATHER_EXPIRES_FORECAST");
                $this->_cache->extSave($id, $this->_forecast, "", $expire, "forecast");
            }
            $forecastReturn["cache"] = "MISS";
        }

        $forecastReturn["days"]   = array();

        for ($i = 1; $i <= $days; $i++) {
            preg_match("/(-?\d+)\D+/", $this->_forecast->{"Day".$i}->High, $temperatureHigh);        
            preg_match("/(-?\d+)\D+/", $this->_forecast->{"Day".$i}->Low, $temperatureLow);        
            $day = array(
                "tempertureHigh" => $this->convertTemperature($temperatureHigh[1], "f", $units["temp"]),
                "temperatureLow" => $this->convertTemperature($temperatureLow[1], "f", $units["temp"]),
                "day" => array(
                    "condition"     => $this->_forecast->{"Day".$i}->Forecast,
                    "conditionIcon" => $this->_forecast->{"Day".$i}->IconIndex,
                    "precipitation" => trim(str_replace("%", "", $this->_forecast->{"Day".$i}->PrecipChance))
                )
            );

            $forecastReturn["days"][] = $day;
        }

        return $forecastReturn;        
    }
    // }}}
}
// }}}
?>
