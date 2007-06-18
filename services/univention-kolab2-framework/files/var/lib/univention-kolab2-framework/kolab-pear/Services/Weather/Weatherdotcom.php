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
// $Id: Weatherdotcom.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

require_once "Services/Weather/Common.php";

// {{{ class Services_Weather_Weatherdotcom
/**
* PEAR::Services_Weather_Weatherdotcom
*
* This class acts as an interface to the xml service of weather.com. It searches for given
* locations and retrieves current weather data as well as forecast for up to 10 days.
*
* For using the weather.com xml-service please visit
*     http://www.weather.com/services/xmloap.html
* and follow the link to sign up, it's free! You will receive an email where to download
* the SDK with the needed images and guidelines how to publish live data from weather.com.
* Unfortunately the guidelines are a bit harsh, that's why there's no actual data-representation
* in this class, just the raw data.
* Also weather.com demands active caching, so I'd strongly recommend enabling the caching
* implemented in this class. It obeys to the times as written down in the guidelines.
*
* For a working example, please take a look at
*     docs/Services_Weather/examples/weather.com-basic.php
*
* @author       Alexander Wirtz <alex@pc4p.net>
* @link         http://www.weather.com/services/xmloap.html
* @example      docs/Services_Weather/examples/weather.com-basic.php
* @package      Services_Weather
* @license      http://www.php.net/license/2_02.txt
* @version      1.2
*/
class Services_Weather_Weatherdotcom extends Services_Weather_Common {

    // {{{ properties
    /**
    * Partner-ID at weather.com
    *
    * @var      string                      $_partnerID
    * @access   private
    */
    var $_partnerID = "";

    /**
    * License key at weather.com
    *
    * @var      string                      $_licenseKey
    * @access   private
    */
    var $_licenseKey = "";

    /**
    * XML_Unserializer, used for processing the xml
    *
    * @var      object XML_Unserializer     $_unserializer
    * @access   private
    */
    var $_unserializer;
    // }}}

    // {{{ constructor
    /**
    * Constructor
    *
    * Requires XML_Serializer to be installed
    *
    * @param    array                       $options
    * @param    mixed                       $error
    * @throws   PEAR_Error
    * @see      Science_Weather::Science_Weather
    * @access   private
    */
    function Services_Weather_Weatherdotcom($options, &$error)
    {
        $perror = null;
        $this->Services_Weather_Common($options, $perror);
        if (Services_Weather::isError($perror)) {
            $error = $perror;
            return;
        }

        // Set options accordingly
        if (isset($options["partnerID"])) {
            $this->setAccountData($options["partnerID"]);
        }
        if (isset($options["licenseKey"])) {
            $this->setAccountData("", $options["licenseKey"]);
        }
        
        include_once "XML/Unserializer.php";
        $unserializer = &new XML_Unserializer(array("complexType" => "object", "keyAttribute" => "type"));
        if (Services_Weather::isError($unserializer)) {
            $error = $unserializer;
            return;
        } else {
            $this->_unserializer = $unserializer;
        }
    }
    // }}}

    // {{{ setAccountData()
    /**
    * Sets the neccessary account-information for weather.com, you'll receive them after registering for the XML-stream
    *
    * @param    string                      $partnerID
    * @param    string                      $licenseKey
    * @access   public
    */
    function setAccountData($partnerID, $licenseKey)
    {
        if (strlen($partnerID) && ctype_digit($partnerID)) {
            $this->_partnerID  = $partnerID;
        }
        if (strlen($licenseKey) && ctype_alnum($licenseKey)) {
            $this->_licenseKey = $licenseKey;
        }
    }
    // }}}

    // {{{ _checkLocationID()
    /**
    * Checks the id for valid values and thus prevents silly requests to weather.com server
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
        } elseif (!ctype_alnum($id) || (strlen($id) > 8)) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_INVALID_LOCATION);
        }

        return true;
    }
    // }}}

    // {{{ _parseWeatherData()
    /**
    * Parses the data returned by the provided URL and caches it
    *
    * @param    string                      $id
    * @param    string                      $url
    * @return   PEAR_Error|bool
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA
    * @throws   PEAR_Error
    * @access   private
    */
    function _parseWeatherData($id, $url)
    {
        // Get data from URL and unserialize
        $status = $this->_unserializer->unserialize($url, true);

        if (Services_Weather::isError($status)) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA);
        } else {
            $root = $this->_unserializer->getRootName();
            $data = $this->_unserializer->getUnserializedData();

            if (Services_Weather::isError($root)) {
                // Something wrong here...
                return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA);
            } elseif ($root == "error") {
                // We got an error back from weather.com
                $errno  = key(get_object_vars($data));
                return Services_Weather::raiseError($errno);
            } else {
                // Valid data, lets get started
                // Loop through the different sub-parts of the data fro processing
                foreach (get_object_vars($data) as $key => $val) {
                    switch ($key) {
                        case "head":
                            continue 2;
                            break;
                        case "loc":
                            $varname  = "location";
                            break;
                        case "cc":
                            $varname  = "weather";
                            break;
                        case "dayf":
                            $varname  = "forecast";
                            break;
                    }
                    // Save data in object
                    $this->{"_".$varname} = $val;
                    if ($this->_cacheEnabled) {
                        // ...and cache if possible
                        $expire = constant("SERVICES_WEATHER_EXPIRES_".strtoupper($varname));
                        $this->_cache->extSave($id, $val, "", $expire, $varname);
                    }
                }
            }
        }

        return true;
    }
    // }}}

    // {{{ searchLocation()
    /**
    * Searches IDs for given location, returns array of possible locations or single ID
    *
    * @param    string                      $location
    * @param    bool                        $useFirst       If set, first ID of result-array is returned
    * @return   PEAR_Error|array|string
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION
    * @access   public
    */
    function searchLocation($location, $useFirst = false)
    {
        // Get search data from server and unserialize
        $searchURL = "http://xoap.weather.com/search/search?where=".urlencode(trim($location));
        $status = $this->_unserializer->unserialize($searchURL, true, array("overrideOptions" => true, "complexType" => "array", "keyAttribute" => "id"));

        if (Services_Weather::isError($status)) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA);
        } else {
            $search = $this->_unserializer->getUnserializedData();

            if (Services_Weather::isError($search)) {
                return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA);
            } elseif (!is_array($search) || !sizeof($search)) {
                return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION);
            } else {
                if (!$useFirst && (sizeof($search) > 1)) {
                    $searchReturn = $search;
                } elseif ($useFirst || (sizeof($search) == 1)) {
                    $searchReturn = key($search);
                }
            }
        }

        return $searchReturn;
    }
    // }}}

    // {{{ searchLocationByCountry()
    /**
    * Returns only false, as weather.com offers no country listing via 
    * its XML services 
    *
    * @param    string                      $country
    * @return   bool
    * @access   public
    * @deprecated
    */
    function searchLocationByCountry($country = "")
    {
        return false;
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
        $locationURL    = "http://xoap.weather.com/weather/local/".$id."?prod=xoap&par=".$this->_partnerID."&key=".$this->_licenseKey."&unit=s";

        if ($this->_cacheEnabled && ($location = $this->_cache->get($id, "location"))) {
            // Get data from cache
            $this->_location = $location;
            $locationReturn["cache"] = "HIT";
        } else {
            // Same as in the function above...
            $status = $this->_parseWeatherData($id, $locationURL);

            if (Services_Weather::isError($status)) {
                return $status;
            }
            $locationReturn["cache"] = "MISS";
        }
        $locationReturn["name"]      = $this->_location->dnam;
        $locationReturn["time"]      = date($this->_timeFormat, strtotime($this->_location->tm));
        $locationReturn["latitude"]  = $this->_location->lat;
        $locationReturn["longitude"] = $this->_location->lon;
        $locationReturn["sunrise"]   = date($this->_timeFormat, strtotime($this->_location->sunr));
        $locationReturn["sunset"]    = date($this->_timeFormat, strtotime($this->_location->suns));
        $locationReturn["timezone"]  = $this->_location->zone;

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
        $weatherURL    = "http://xoap.weather.com/weather/local/".$id."?cc=*&prod=xoap&par=".$this->_partnerID."&key=".$this->_licenseKey."&unit=s";

        if ($this->_cacheEnabled && ($weather = $this->_cache->get($id, "weather"))) {
            // Same procedure...
            $this->_weather = $weather;
            $weatherReturn["cache"] = "HIT";
        } else {
            // ...as last function
            $status = $this->_parseWeatherData($id, $weatherURL);

            if (Services_Weather::isError($status)) {
                return $status;
            }
            $weatherReturn["cache"] = "MISS";
        }
        
        $update  = str_replace("Local Time", "", $this->_weather->lsup);
        $weatherReturn["update"]            = gmdate(trim($this->_dateFormat." ".$this->_timeFormat), strtotime($update));
        $weatherReturn["station"]           = $this->_weather->obst;
        $weatherReturn["temperature"]       = $this->convertTemperature($this->_weather->tmp, "f", $units["temp"]);
        $weatherReturn["feltTemperature"]   = $this->convertTemperature($this->_weather->flik, "f", $units["temp"]);
        $weatherReturn["condition"]         = $this->_weather->t;
        $weatherReturn["conditionIcon"]     = $this->_weather->icon;
        $weatherReturn["pressure"]          = $this->convertPressure($this->_weather->bar->r, "in", $units["pres"]);
        $weatherReturn["pressureTrend"]     = $this->_weather->bar->d;
        $weatherReturn["wind"]              = $this->convertSpeed($this->_weather->wind->s, "mph", $units["wind"]);
        $weatherReturn["windDegrees"]       = $this->_weather->wind->d;
        $weatherReturn["windDirection"]     = $this->_weather->wind->t;
        $weatherReturn["humidity"]          = $this->_weather->hmid;
        if (is_numeric($this->_weather->vis)) {
            $weatherReturn["visibility"]    = $this->convertDistance($this->_weather->vis, "sm", $units["vis"]);
        } else {
            $weatherReturn["visibility"]    = $this->_weather->vis;
        }
        $weatherReturn["uvIndex"]           = $this->_weather->uv->i;
        $weatherReturn["uvText"]            = $this->_weather->uv->t;
        $weatherReturn["dewPoint"]          = $this->convertTemperature($this->_weather->dewp, "f", $units["temp"]);

        return $weatherReturn;
    }
    // }}}

    // {{{ getForecast()
    /**
    * Get the forecast for the next days
    *
    * @param    string                      $id
    * @param    int                         $days           Values between 1 and 10
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
        if (!in_array($days, range(1, 10))) {
            $days = 2;
        }
        
        // Get other data
        $units    = $this->getUnitsFormat($unitsFormat);

        $forecastReturn = array();
        $forecastURL = "http://xoap.weather.com/weather/local/".$id."?dayf=10&prod=xoap&par=".$this->_partnerID."&key=".$this->_licenseKey."&unit=s";

        if ($this->_cacheEnabled && ($forecast = $this->_cache->get($id, "forecast"))) {
            // Encore...
            $this->_forecast = $forecast;
            $forecastReturn["cache"] = "HIT";
        } else {
            // ...
            $status = $this->_parseWeatherData($id, $forecastURL, $days);

            if (Services_Weather::isError($status)) {
                return $status;
            }
            $forecastReturn["cache"] = "MISS";
        }

        $update = implode(" ", array_slice(explode(" ", $this->_forecast->lsup ), 0, 3));

        $forecastReturn["update"] = date($this->_dateFormat." ".$this->_timeFormat, strtotime($update));
        $forecastReturn["days"]   = array();

        for ($i = 0; $i < $days; $i++) {
            $day = array(
                "tempertureHigh" => $this->convertTemperature($this->_forecast->day[$i]->hi, "f", $units["temp"]),
                "temperatureLow" => $this->convertTemperature($this->_forecast->day[$i]->low, "f", $units["temp"]),
                "sunrise"        => date($this->_timeFormat, strtotime($this->_forecast->day[$i]->sunr)),
                "sunset"         => date($this->_timeFormat, strtotime($this->_forecast->day[$i]->suns)),
                "day" => array(
                    "condition"     => $this->_forecast->day[$i]->part[0]->t,
                    "conditionIcon" => $this->_forecast->day[$i]->part[0]->icon,
                    "wind"          => $this->convertSpeed($this->_forecast->day[$i]->part[0]->wind->s, "mph", $units["wind"]),
                    "windGust"      => $this->convertSpeed($this->_forecast->day[$i]->part[0]->wind->gust, "mph", $units["wind"]),
                    "windDegrees"   => $this->_forecast->day[$i]->part[0]->wind->d,
                    "windDirection" => $this->_forecast->day[$i]->part[0]->wind->t,
                    "precipitation" => $this->_forecast->day[$i]->part[0]->ppcp,
                    "humidity"      => $this->_forecast->day[$i]->part[0]->hmid
                ),
                "night" => array (
                    "condition"     => $this->_forecast->day[$i]->part[1]->t,
                    "conditionIcon" => $this->_forecast->day[$i]->part[1]->icon,
                    "wind"          => $this->convertSpeed($this->_forecast->day[$i]->part[1]->wind->s, "mph", $units["wind"]),
                    "windGust"      => $this->convertSpeed($this->_forecast->day[$i]->part[1]->wind->gust, "mph", $units["wind"]),
                    "windDegrees"   => $this->_forecast->day[$i]->part[1]->wind->d,
                    "windDirection" => $this->_forecast->day[$i]->part[1]->wind->t,
                    "precipitation" => $this->_forecast->day[$i]->part[1]->ppcp,
                    "humidity"      => $this->_forecast->day[$i]->part[1]->hmid
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
