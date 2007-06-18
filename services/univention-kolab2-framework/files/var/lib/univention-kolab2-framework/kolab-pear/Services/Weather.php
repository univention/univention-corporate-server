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
// $Id: Weather.php,v 1.1.2.1 2005/10/05 14:39:48 steuwer Exp $

// {{{ constants
// {{{ cache times
define("SERVICES_WEATHER_EXPIRES_UNITS",      900);
define("SERVICES_WEATHER_EXPIRES_LOCATION",   900);
define("SERVICES_WEATHER_EXPIRES_WEATHER",   1800);
define("SERVICES_WEATHER_EXPIRES_FORECAST",  7200);
define("SERVICES_WEATHER_EXPIRES_LINKS",    43200);
// }}}

// {{{ error codes
define("SERVICES_WEATHER_ERROR_SERVICE_NOT_FOUND",   10);
define("SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION",    11);
define("SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA",   12);
define("SERVICES_WEATHER_ERROR_CACHE_INIT_FAILED",   13);
define("SERVICES_WEATHER_ERROR_DB_NOT_CONNECTED",    14);
// }}}

// {{{ error codes defined by weather.com
define("SERVICES_WEATHER_ERROR_UNKNOWN_ERROR",            0);
define("SERVICES_WEATHER_ERROR_NO_LOCATION",              1);
define("SERVICES_WEATHER_ERROR_INVALID_LOCATION",         2);
define("SERVICES_WEATHER_ERROR_INVALID_PARTNER_ID",     100);
define("SERVICES_WEATHER_ERROR_INVALID_PRODUCT_CODE",   101);
define("SERVICES_WEATHER_ERROR_INVALID_LICENSE_KEY",    102);
// }}}
// }}}

// {{{ class Services_Weather
/**
* PEAR::Services_Weather
*
* This class acts as an interface to various online weather-services.
*
* Services_Weather searches for given locations and retrieves current weather data
* and, dependant on the used service, also forecasts. Up to now, SOAP services from
* CapeScience and EJSE, XML from weather.com and METAR from noaa.gov are supported,
* further services will get included, if they become available and are
* properly documented.
*
* @author       Alexander Wirtz <alex@pc4p.net>
* @package      Services_Weather
* @license      http://www.php.net/license/2_02.txt
* @version      1.2
*/
class Services_Weather {

    // {{{ &service()
    /**
    * Factory for creating the services-objects
    *
    * Usable keys for the options array are:
    * o debug               enables debugging output
    * --- Common Options
    * o cacheType           defines what type of cache to use
    * o cacheOptions        passes cache options
    * o unitsFormat         use (US)-standard, metric or custom units
    * o customUnitsFormat   defines the customized units format
    * o dateFormat          string to use for date output
    * o timeFormat          string to use for time output
    * --- EJSE Options
    * none
    * --- GlobalWeather Options
    * none
    * --- METAR Options
    * o dsn                 String for defining the DB connection
    * o dbOptions           passes DB options
    * o source              http, ftp or file - type of data-source
    * o sourcePath          where to look for the source, URI or filepath
    * --- weather.com Options
    * o partnerID           You'll receive these keys after registering
    * o licenseKey          with the weather.com XML-service
    *
    * @param    string                      $service
    * @param    array                       $options
    * @return   PEAR_Error|object
    * @throws   PEAR_Error
    * @throws   PEAR_Error::SERVICES_WEATHER_ERROR_SERVICE_NOT_FOUND
    * @access   public
    */
    function &service($service, $options = null)
    {
        $service = ucfirst(strtolower($service));
        $classname = "Services_Weather_".$service;

        // Check for debugging-mode and set stuff accordingly
        if (is_array($options) && isset($options["debug"]) && $options["debug"] >= 2) {
            if (!defined("SERVICES_WEATHER_DEBUG")) {
                define("SERVICES_WEATHER_DEBUG", true);
            }
            include_once("Services/Weather/".$service.".php");
        } else {
            if (!defined("SERVICES_WEATHER_DEBUG")) {
                define("SERVICES_WEATHER_DEBUG", false);
            }
            @include_once("Services/Weather/".$service.".php");
        }

        // No such service... bail out
        if (!class_exists($classname)) {
            return Services_Weather::raiseError(SERVICES_WEATHER_ERROR_SERVICE_NOT_FOUND);
        }

        // Create service and return
        $error = null;
        @$obj = &new $classname($options, $error);

        if (Services_Weather::isError($error)) {
            return $error;
        } else {
            return $obj;
        }
    }
    // }}}

    // {{{ apiVersion()
    /**
    * For your convenience, when I come up with changes in the API...
    *
    * @return   string
    * @access   public
    */
   function apiVersion()
    {
        return "1.2";
    }
    // }}}

    // {{{ _errorMessage()
    /**
    * Returns the message for a certain error code
    *
    * @param    PEAR_Error|int              $value
    * @return   string
    * @access   private
    */
    function _errorMessage($value)
    {
        static $errorMessages;
        if (!isset($errorMessages)) {
            $errorMessages = array(
                SERVICES_WEATHER_ERROR_SERVICE_NOT_FOUND         => "Requested service could not be found.",
                SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION          => "Unknown location provided.",
                SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA         => "Server data wrong or not available.",
                SERVICES_WEATHER_ERROR_CACHE_INIT_FAILED         => "Cache init was not completed.",
                SERVICES_WEATHER_ERROR_DB_NOT_CONNECTED          => "MetarDB is not connected.",
                SERVICES_WEATHER_ERROR_UNKNOWN_ERROR             => "An unknown error has occured.",
                SERVICES_WEATHER_ERROR_NO_LOCATION               => "No location provided.",
                SERVICES_WEATHER_ERROR_INVALID_LOCATION          => "Invalid location provided.",
                SERVICES_WEATHER_ERROR_INVALID_PARTNER_ID        => "Invalid partner id.",
                SERVICES_WEATHER_ERROR_INVALID_PRODUCT_CODE      => "Invalid product code.",
                SERVICES_WEATHER_ERROR_INVALID_LICENSE_KEY       => "Invalid license key."
            );
        }

        if (Services_Weather::isError($value)) {
            $value = $value->getCode();
        }

        return isset($errorMessages[$value]) ? $errorMessages[$value] : $errorMessages[SERVICES_WEATHER_ERROR_UNKNOWN_ERROR];
    }
    // }}}

    // {{{ isError()
    /**
    * Checks for an error object, same as in PEAR
    *
    * @param    PEAR_Error|mixed            $value
    * @return   bool
    * @access   public
    */
    function isError($value)
    {
        return (is_object($value) && (get_class($value) == "pear_error" || is_subclass_of($value, "pear_error")));
    }
    // }}}

    // {{{ &raiseError()
    /**
    * Creates error, same as in PEAR with a customized flavor
    *
    * @param    int                         $code
    * @return   PEAR_Error
    * @access   private
    */
    function &raiseError($code = SERVICES_WEATHER_ERROR_UNKNOWN_ERROR)
    {
        // This should improve the performance of the script, as PEAR is only included, when
        // really needed.
        include_once "PEAR.php";

        $message = "Services_Weather: ".Services_Weather::_errorMessage($code);

        return PEAR::raiseError($message, $code, PEAR_ERROR_RETURN, E_USER_NOTICE, "Services_Weather_Error", null, false);
    }
    // }}}
}
// }}}
?>
