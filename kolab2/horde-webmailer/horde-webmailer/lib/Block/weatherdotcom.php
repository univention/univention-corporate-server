<?php

/* Disable block if not configured. */
if (!empty($GLOBALS['conf']['weatherdotcom']['partner_id']) &&
    !empty($GLOBALS['conf']['weatherdotcom']['license_key'])) {
    $block_name = _("weather.com");
}

/**
 * The Horde_Block_weatherdotcom class provides an applet for the
 * portal screen to display weather and forecast data from weather.com
 * for a specified location.
 *
 * $Horde: horde/lib/Block/weatherdotcom.php,v 1.37.4.17 2009-06-17 21:19:16 mrubinsk Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Horde_weatherdotcom extends Horde_Block {

    /**
     * Whether this block has changing content.
     */
    var $updateable = true;

    var $_app = 'horde';

    /**
     * The title to go in this block.
     *
     * @return string   The title text.
     */
    function _title()
    {
        return _("Weather Forecast");
    }

    /**
     * The parameters to go with this block.
     *
     * @return array  An array containing the parameters.
     */
    function _params()
    {
        if (!(@include_once 'Services/Weather.php') ||
            !(@include_once 'Cache.php') ||
            !(@include_once 'XML/Serializer.php') ||
            !ini_get('allow_url_fopen')) {
            Horde::logMessage('The weather.com block will not work without PEAR\'s Services_Weather, Cache, and XML_ Serializer packages, and allow_url_fopen enabled. Run `pear install Services_Weather Cache XML_Serializer´ and ensure that allow_url_fopen is enabled in php.ini.',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            $params = array(
                'error' => array(
                    'type' => 'error',
                    'name' => _("Error"),
                    'default' => _("The weather.com block is not available.")
                )
            );
        } else {
            $params = array(
                'location' => array(
                    // 'type' => 'weatherdotcom',
                    'type' => 'text',
                    'name' => _("Location"),
                    'default' => 'Boston, MA'
                ),
                'units' => array(
                    'type' => 'enum',
                    'name' => _("Units"),
                    'default' => 'standard',
                    '0' => 'none',
                    'values' => array(
                        'standard' => _("Standard"),
                        'metric' => _("Metric")
                    )
                ),
                'days' => array(
                    'type' => 'enum',
                    'name' => _("Forecast Days (note that the returned forecast returns both day and night; a large number here could result in a wide block)"),
                    'default' => 3,
                    'values' => array(
                        '1' => 1,
                        '2' => 2,
                        '3' => 3,
                        '4' => 4,
                        '5' => 5,
                    )
                ),
                'detailedForecast' => array(
                    'type' => 'checkbox',
                    'name' => _("Display detailed forecast"),
                    'default' => 0
                )
            );
        }

        return $params;
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        if (!(@include_once 'Services/Weather.php') ||
            !(@include_once 'Cache.php') ||
            !ini_get('allow_url_fopen')) {
            Horde::logMessage('The weather.com block will not work without the PEARServices_Weather and Cache packages, and allow_url_fopen enabled. Run pear install Services_Weather Cache, and ensure that allow_url_fopen_wrappers is enabled in php.ini.',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return _("The weather.com block is not available.");
        }

        global $conf;

        $options = array();
        if (!empty($conf['http']['proxy']['proxy_host'])) {
            $proxy = 'http://';
            if (!empty($conf['http']['proxy']['proxy_user'])) {
                $proxy .= urlencode($conf['http']['proxy']['proxy_user']);
                if (!empty($conf['http']['proxy']['proxy_pass'])) {
                    $proxy .= ':' . urlencode($conf['http']['proxy']['proxy_pass']);
                }
                $proxy .= '@';
            }
            $proxy .= $conf['http']['proxy']['proxy_host'];
            if (!empty($conf['http']['proxy']['proxy_port'])) {
                $proxy .= ':' . $conf['http']['proxy']['proxy_port'];
            }

            $options['httpProxy'] = $proxy;
        }

        if (empty($this->_params['location'])) {
            return _("No location is set.");
        }

        $weatherDotCom = &Services_Weather::service('WeatherDotCom', $options);
        $weatherDotCom->setAccountData(
            (isset($conf['weatherdotcom']['partner_id']) ? $conf['weatherdotcom']['partner_id'] : ''),
            (isset($conf['weatherdotcom']['license_key']) ? $conf['weatherdotcom']['license_key'] : ''));

        $cacheDir = Horde::getTempDir();
        if (!$cacheDir) {
            return PEAR::raiseError(_("No temporary directory available for cache."), 'horde.error');
        } else {
            $weatherDotCom->setCache('file', array('cache_dir' => ($cacheDir . '/')));
        }
        $weatherDotCom->setDateTimeFormat('m.d.Y', 'H:i');
        $weatherDotCom->setUnitsFormat($this->_params['units']);
        $units = $weatherDotCom->getUnitsFormat();

        // If the user entered a zip code for the location, no need to
        // search (weather.com accepts zip codes as location IDs).
        // The location ID should already have been validated in
        // getParams.
        $search = (preg_match('/\b(?:\\d{5}(-\\d{5})?)|(?:[A-Z]{4}\\d{4})\b/',
            $this->_params['location'], $matches) ?
            $matches[0] :
            $weatherDotCom->searchLocation($this->_params['location']));
        if (is_a($search, 'PEAR_Error')) {
            switch ($search->getCode()) {
            case SERVICES_WEATHER_ERROR_SERVICE_NOT_FOUND:
                return _("Requested service could not be found.");
            case SERVICES_WEATHER_ERROR_UNKNOWN_LOCATION:
                return _("Unknown location provided.");
            case SERVICES_WEATHER_ERROR_WRONG_SERVER_DATA:
                return _("Server data wrong or not available.");
            case SERVICES_WEATHER_ERROR_CACHE_INIT_FAILED:
                return _("Cache init was not completed.");
            case SERVICES_WEATHER_ERROR_DB_NOT_CONNECTED:
                return _("MetarDB is not connected.");
            case SERVICES_WEATHER_ERROR_UNKNOWN_ERROR:
                return _("An unknown error has occured.");
            case SERVICES_WEATHER_ERROR_NO_LOCATION:
                return _("No location provided.");
            case SERVICES_WEATHER_ERROR_INVALID_LOCATION:
                return _("Invalid location provided.");
            case SERVICES_WEATHER_ERROR_INVALID_PARTNER_ID:
                return _("Invalid partner id.");
            case SERVICES_WEATHER_ERROR_INVALID_PRODUCT_CODE:
                return _("Invalid product code.");
            case SERVICES_WEATHER_ERROR_INVALID_LICENSE_KEY:
                return _("Invalid license key.");
            default:
                return $search->getMessage();
            }
        }

        $html = '';
        if (is_array($search)) {
            // Several locations returned due to imprecise location
            // parameter.
            $html = _("Several locations possible with the parameter: ") .
                $this->_params['location'] .
                '<br /><ul>';
            foreach ($search as $id_weather => $real_location) {
                $html .= "<li>$real_location ($id_weather)</li>\n";
            }
            $html .= '</ul>';
            return $html;
        }

        $location = $weatherDotCom->getLocation($search);
        if (is_a($location, 'PEAR_Error')) {
            return $location->getMessage();
        }
        $weather = $weatherDotCom->getWeather($search);
        if (is_a($weather, 'PEAR_Error')) {
            return $weather->getMessage();
        }
        $forecast = $weatherDotCom->getForecast($search, (integer)$this->_params['days']);
        if (is_a($forecast, 'PEAR_Error')) {
            return $forecast->getMessage();
        }

        // Location and local time.
        $html .= '<div class="control">' .
            '<strong>' . $location['name'] . '</strong> ' . _("Local time: ") . $location['time'] .
            '</div>';

        // Sunrise/sunset.
        $html .= '<strong>' . _("Sunrise: ") . '</strong>' .
            Horde::img('block/sunrise/sunrise.png', _("Sunrise")) .
            $location['sunrise'];
        $html .= ' <strong>' . _("Sunset: ") . '</strong>' .
            Horde::img('block/sunrise/sunset.png', _("Sunset")) .
            $location['sunset'];

        // Temperature.
        $html .= '<br /><strong>' . _("Temperature: ") . '</strong>' .
            round($weather['temperature']) . '&deg;' . String::upper($units['temp']);

        // Dew point.
        $html .= ' <strong>' . _("Dew point: ") . '</strong>' .
            round($weather['dewPoint']) . '&deg;' . String::upper($units['temp']);

        // Feels like temperature.
        $html .= ' <strong>' . _("Feels like: ") . '</strong>' .
            round($weather['feltTemperature']) . '&deg;' . String::upper($units['temp']);

        // Pressure and trend.
        $html .= '<br /><strong>' . _("Pressure: ") . '</strong>';
        $trend = $weather['pressureTrend'];
        $html .= sprintf(_("%d %s and %s"),
                         round($weather['pressure']), $units['pres'],
                         _($trend));

        // Wind.
        $html .= '<br /><strong>' . _("Wind: ") . '</strong>';
        if ($weather['windDirection'] == 'VAR') {
            $html .= _("Variable");
        } elseif ($weather['windDirection'] == 'CALM') {
            $html .= _("Calm");
        } else {
            $html .= _("From the ") . $weather['windDirection'];
        if (isset($weather['windGust']) && $weather['windGust'] > 0) {
            $html .= ', ' . _("gusting") . ' ' . $weather['windGust'] .
                ' ' . $units['wind'];
        }

            $html .= ' (' . $weather['windDegrees'] . ')';
        }
        $html .= _(" at ") . round($weather['wind']) . ' ' . $units['wind'];

        // Humidity.
        $html .= '<br /><strong>' . _("Humidity: ") . '</strong>' .
            $weather['humidity'] . '%';

        // Visibility.
        $html .= ' <strong>' . _("Visibility: ") . '</strong>' .
            (is_numeric($weather['visibility'])
             ? round($weather['visibility']) . ' ' . $units['vis']
             : $weather['visibility']);

        // UV index.
        $html .= ' <strong>' . _("U.V. index: ") . '</strong>';
        $uv = $weather['uvText'];
        $html .= $weather['uvIndex'] . ' - ' . _($uv);

        // Current condition.
        $condition = implode(' / ', array_map('_', explode(' / ', $weather['condition'])));
        $html .= '<br /><strong>' . _("Current condition: ") . '</strong>' .
            Horde::img('block/weatherdotcom/32x32/' .
                       ($weather['conditionIcon'] == '-' ? 'na' : $weather['conditionIcon']) . '.png',
                       $condition);
        $html .= ' ' . $condition;

        // Do the forecast now (if requested).
        if ($this->_params['days'] > 0) {
            $html .= '<div class="control"><strong>' .
                sprintf(_("%d-day forecast"), $this->_params['days']) .
                '</strong></div>';

            $futureDays = 0;
            $html .= '<table width="100%" cellspacing="3">';
            // Headers.
            $html .= '<tr>';
            $html .= '<th>' . _("Day") . '</th><th>&nbsp;</th><th>' .
                sprintf(_("Temperature<br />(%sHi%s/%sLo%s) &deg;%s"),
                        '<span style="color:red">', '</span>',
                        '<span style="color:blue">', '</span>',
                        String::upper($units['temp'])) .
                '</th><th>' . _("Condition") . '</th>' .
                '<th>' . _("Precipitation<br />chance") . '</th>';
            if (isset($this->_params['detailedForecast'])) {
                $html .= '<th>' . _("Humidity") . '</th><th>' . _("Wind") . '</th>';
            }
            $html .= '</tr>';

            foreach ($forecast['days'] as $which => $day) {
                $html .= '<tr class="item0">';

                // Day name.
                $html .= '<td rowspan="2" style="border:1px solid #ddd; text-align:center"><strong>';
                if ($which == 0) {
                    $html .= _("Today");
                } elseif ($which == 1) {
                    $html .= _("Tomorrow");
                } else {
                    $html .= strftime('%A', mktime(0, 0, 0, date('m'), date('d') + $futureDays, date('Y')));
                }
                $html .= '</strong><br />' .
                    strftime('%b %d', mktime(0, 0, 0, date('m'), date('d') + $futureDays, date('Y'))) .
                    '</td>' .
                    '<td style="border:1px solid #ddd; text-align:center">' .
                    '<span style="color:orange">' .
                    _("Day") . '</span></td>';

                // The day portion of the forecast is no longer available after 2:00 p.m. local today.
                if ($which == 0 && (strtotime($location['time']) >= strtotime('14:00'))) {
                    // Balance the grid.
                    $html .= '<td colspan="' .
                            ((isset($this->_params['detailedForecast']) ? '5' : '3') . '"') .
                            ' style="border:1px solid #ddd; text-align:center">' .
                            '&nbsp;<br />' . _("Information no longer available.") . '<br />&nbsp;' .
                            '</td>';
                } else {
                    // Forecast condition.
                    $condition = implode(' / ', array_map('_', explode(' / ', $day['day']['condition'])));

                    // High temperature.
                    $html .= '<td style="border:1px solid #ddd; text-align:center">' .
                        '<span style="color:red">' .
                        round($day['temperatureHigh']) . '</span></td>';

                    // Condition.
                    $html .= '<td style="border:1px solid #ddd; text-align:center">' .
                        Horde::img('block/weatherdotcom/23x23/' . ($day['day']['conditionIcon'] == '-' ? 'na' : $day['day']['conditionIcon']) . '.png', $condition) .
                        '<br />' . $condition . '</td>';

                    // Precipitation chance.
                    $html .= '<td style="border:1px solid #ddd; text-align:center">' .
                        $day['day']['precipitation'] . '%' . '</td>';

                    // If a detailed forecast was requested, show humidity and
                    // winds.
                    if (isset($this->_params['detailedForecast'])) {

                        // Humidity.
                        $html .= '<td style="border:1px solid #ddd; text-align:center">' .
                            $day['day']['humidity'] . '%</td>';

                        // Winds.
                        $html .= '<td style="border:1px solid #ddd">' .
                            _("From the ") . $day['day']['windDirection'] .
                            _(" at ") . $day['day']['wind'] .
                            ' ' . $units['wind'];
                        if (isset($day['day']['windGust']) &&
                            $day['day']['windGust'] > 0) {
                            $html .= _(", gusting ") . $day['day']['windGust'] .
                                ' ' . $units['wind'];
                        }
                    }

                    $html .= '</tr>';
                }

                // Night forecast
                $night = implode(' / ', array_map('_', explode(' / ', $day['night']['condition'])));

                // Shade it for visual separation.
                $html .= '<tr class="item1">';

                $html .= '<td style="border:1px solid #ddd; text-align:center">' .
                    _("Night") . '</td>';

                // Low temperature.
                $html .= '<td style="border:1px solid #ddd; text-align:center">' .
                    '<span style="color:blue">' .
                    round($day['temperatureLow']) . '</span></td>';

                // Condition.
                $html .= '<td style="border:1px solid #ddd; text-align:center">' .
                    Horde::img('block/weatherdotcom/23x23/' . ($day['night']['conditionIcon'] == '-' ? 'na' : $day['night']['conditionIcon']) . '.png', $night) .
                    '<br />' . $night . '</td>';

                // Precipitation chance.
                $html .= '<td style="border:1px solid #ddd; text-align:center">' .
                    $day['night']['precipitation'] . '%</td>';

                // If a detailed forecast was requested, display humidity and
                // winds.
                if (isset($this->_params['detailedForecast'])) {

                    // Humidity.
                    $html .= '<td style="border:1px solid #ddd; text-align:center">' .
                        $day['night']['humidity'] . '%</td>';

                    // Winds.
                    $html .= '<td style="border:1px solid #ddd">' .
                        _("From the ") . $day['night']['windDirection'] .
                        _(" at ") . $day['night']['wind'] .
                        ' ' . $units['wind'];
                    if (isset($day['night']['windGust']) && $day['night']['windGust'] > 0) {
                        $html .= _(", gusting ") . $day['night']['windGust'] .
                            ' ' . $units['wind'];
                    }
                }

                $html .= '</tr>';

                // Prepare for next day.
                $futureDays++;
            }
            $html .= '</table>';
        }

        // Display a bar at the bottom of the block with the required
        // attribution to weather.com and the logo, both linked to
        // weather.com with the partner ID.
        return $html . '<div class="rightAlign linedRow">' .
            _("Weather data provided by") . ' ' .
            Horde::link(Horde::externalUrl('http://www.weather.com/?prod=xoap&amp;par=' .
                        $weatherDotCom->_partnerID),
                        'weather.com', '', '_blank', '', 'weather.com') .
            '<em>weather.com</em>&reg; ' .
            Horde::img('block/weatherdotcom/32x32/TWClogo_32px.png', 'weather.com logo') .
            '</a></div>';
    }

}
