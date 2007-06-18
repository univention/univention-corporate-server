<?php
/**
 * The Horde_Block_weatherdotcom class provides an applet for the portal screen
 * to display weather and forecast data from weather.com for a specified
 * location.
 *
 * $Horde: horde/lib/Block/weatherdotcom.php,v 1.16 2004/05/29 16:21:03 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_weatherdotcom extends Horde_Block {

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
    function getParams()
    {
        if (!@include_once 'Services/Weather.php') {
            Horde::logMessage('The weather.com block will not work without Services_Weather from PEAR. Run pear install Services_Weather.',
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
                    'default' => 's',
                    'values' => array(
                        'standard' => _("Standard"),
                        'metric' => _("Metric")
                    )
                ),
                'days' => array(
                    'type' => 'enum',
                    'name' => _("Forecast Days (note that the returned forecast returns both day and night; a large number here could result in a wide block)"),
                    'default' => '3',
                    'values' => array(
                        '1' => '1',
                        '2' => '2',
                        '3' => '3',
                        '4' => '4',
                        '5' => '5',
                        '6' => '6',
                        '7' => '7',
                        '8' => '8'
                    )
                ),
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
        if (!@include_once 'Services/Weather.php') {
            Horde::logMessage('The weather.com block will not work without Services_Weather from PEAR. Run pear install Services_Weather.',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return _("The weather.com block is not available.");
        }

        global $conf;

        $cacheDir = Horde::getTempDir();
        $html = '';

        if (empty($this->_params['location'])) {
            return _("No location is set.");
        }


        $weatherDotCom = &Services_Weather::service("WeatherDotCom");

        $weatherDotCom->setAccountData(
            (isset($conf['weatherdotcom']['partner_id']) ? $conf['weatherdotcom']['partner_id']
            : ''),
            (isset($conf['weatherdotcom']['license_key']) ? $conf['weatherdotcom']['license_key']
            : ''));
        if (!$cacheDir) {
            return PEAR::raiseError(
                _("No temporary directory available for cache."),
                'horde.error');
        } else {
            $weatherDotCom->setCache("file",
                array("cache_dir" => ($cacheDir . '/')));
        }
        $weatherDotCom->setDateTimeFormat("m.d.Y", "H:i");
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
            return $search->getmessage();
        }

        if (is_array($search)) {
            // Several locations returned due to imprecise location parameter
            $html = _("Several locations possible with the parameter: ");
            $html .= $this->_params['location'];
            $html .= "<br/><ul>";
            foreach ($search as $id_weather=>$real_location) {
                $html .= "<li>$real_location ($id_weather)</li>\n";
            }
            $html .= "</ul>";
            return $html;
        }

        $location = $weatherDotCom->getLocation($search);
        if (is_a($location, 'PEAR_Error')) {
            return $location->getmessage();
        }
        $weather = $weatherDotCom->getWeather($search);
        if (is_a($weather, 'PEAR_Error')) {
            return $weather->getmessage();
        }
        $forecast = $weatherDotCom->getForecast($search, $this->_params['days']);
        if (is_a($forecast, 'PEAR_Error')) {
            return $forecast->getmessage();
        }

        // Location and local time.
        $html .= '<table cellspacing="0" width="100%"><tr><td class="control">';
        $html .= '<b>' . $location['name'] . '</b> ' . _("Local time: ") . $location['time'];
        $html .= '</b></td></tr></table>';

        // Sunrise/sunset.
        $html .= '<b>' . _("Sunrise: ") . '</b>' .
            Horde::img('block/sunrise/sunrise.gif', _("Sunrise")) .
            $location['sunrise'];
        $html .= ' <b>' . _("Sunset: ") . '</b>' .
            Horde::img('block/sunrise/sunset.gif', _("Sunset")) .
            $location['sunset'];

        // Temperature.
        $html .= '<br /><b>' . _("Temperature: ") . '</b>';
        $html .= round($weather['temperature']) . '&deg;' . String::upper($units['temp']);

        // Dew point.
        $html .= ' <b>' . _("Dew point: ") . '</b>';
        $html .= round($weather['dewPoint']) . '&deg;' . String::upper($units['temp']);

        // Feels like temperature.
        $html .= ' <b>' . _("Feels like: ") . '</b>';
        $html .= round($weather['feltTemperature']) . '&deg;' . String::upper($units['temp']);

        // Pressure and trend.
        $html .= '<br /><b>' . _("Pressure: ") . '</b>';
        $html .= number_format($weather['pressure'], 2) . ' ' . $units['pres'];
        $html .= _(" and ") . $weather['pressureTrend'];

        // Wind.
        $html .= '<br /><b>' . _("Wind: ") . '</b>';
        if ($weather['windDirection'] == 'VAR') {
            $html .= _("Variable");
        } elseif ($weather['windDirection'] == 'CALM') {
            $html .= _("Calm");
        } else {
            $html .= _("From the ") . $weather['windDirection'];
            $html .= ' (' . $weather['windDegrees'] . ')';
        }
        $html .= _(" at ") . $weather['wind'] . ' ' . $units['wind'];

        // Humidity.
        $html .= '<br /><b>' . _("Humidity: ") . '</b>';
        $html .= $weather['humidity'] . '%';

        // Visibility.
        $html .= ' <b>' . _("Visibility: ") . '</b>';
        $html .= $weather['visibility'] . (is_numeric($weather['visibility']) ?
            ' ' . $units['vis'] : '');

        // UV index.
        $html .= ' <b>' . _("U.V. index: ") . '</b>';
        $html .= $weather['uvIndex'] . ' - ' . $weather['uvText'];

        // Current condition.
        $html .= '<br /><b>' . _("Current condition: ") . '</b>' .
            Horde::img('block/weatherdotcom/32x32/' .
            $weather['conditionIcon'] . '.png',
            _(String::lower($weather['condition'])),
            'align="middle"');
        $html .= ' ' . $weather['condition'];

        // Do the forecast now.
        $html .= '<table cellspacing="0" width="100%"><tr>';
        $html .= '<tr><td class="control" colspan="'
            . $this->_params['days'] * 2
            . '"><center><b>' . sprintf(_("%d-day forecast"), $this->_params['days'])
            . '</b></center></td></tr><tr>';
        $futureDays = 0;
        $item = 0;
        foreach ($forecast['days'] as $which => $day) {
            $item++;
            $html .= '<td colspan="2" align="center" class="item' . ($item % 2) . '">';

            // Day name.
            $html .= '<b>';
            if ($which == 0) {
                $html .= _("Today");
            } elseif ($which == 1) {
                $html .= _("Tomorrow");
            } else {
                $html .= strftime('%A', mktime(0, 0, 0, date('m'), date('d') + $futureDays, date('Y')));
            }
            $html .= '</b><br />';
            $futureDays++;

            // High/low temp. If after 2 p.m. local time, the "day"
            // forecast is no longer valid.
            if ($which > 0 || ($which == 0 &&
                (strtotime($location['time']) < strtotime('14:00')))) {
                $html .= '<span style="color:red">' . round($day['temperatureHigh']) .
                    '&deg;' . String::upper($units['temp']) . '</span>/';
            }
            $html .= '<span style="color:blue">' . round($day['temperatureLow']) .
                '&deg;' . String::upper($units['temp']) . '</span>';
            $html .= '</td>';
        }
        $html .= '</tr><tr>';

        $elementWidth = 100 / ($this->_params['days'] * 2);

        $item = 0;
        foreach ($forecast['days'] as $which => $day) {
            $item++;
            // Day forecast.
            $html .= '<td align="center" valign="top" width="'
                . $elementWidth . '%" class="item' . ($item % 2) . '">';
            if ($which > 0 || ($which == 0 &&
                (strtotime($location['time']) < strtotime('14:00')))) {
                $html .= '<b><i>' . _("Day") . '</i></b><br />';
                $html .= Horde::img('block/weatherdotcom/23x23/' .
                    $day['day']['conditionIcon'] . '.png',
                    $day['day']['condition']);
                    $html .= '<br />' . $day['day']['condition'];
            } else {
                $html .= '&nbsp;';
            }
            $html .= '</td>';

            // Night forecast.
            $html .= '<td align="center" valign="top" width="'
                . $elementWidth . '%" class="item' . ($item % 2) . '">';

            $html .= '<b><i>' . _("Night") . '</i></b><br />';
            $html .= Horde::img('block/weatherdotcom/23x23/' .
                $day['night']['conditionIcon'] . '.png',
                $day['night']['condition']);
            $html .= '<br />' . $day['night']['condition'];
            $html .= '</td>';
        }
        $html .= '</tr></table>';

        // Display a bar at the bottom of the block with the required
        // attribution to weather.com and the logo, both linked to
        // weather.com with the partner ID.
        $html .= '<table cellspacing="0" width=100%><tr>';
        $html .= '<td align=right class=control>';
        $html .= 'Weather data provided by ';
        $html .= Horde::link('http://www.weather.com/?prod=xoap&par=' .
            $weatherDotCom->_partnerID,
            'weather.com', '', '_blank', '', 'weather.com');
        $html .= '<i>weather.com</i>&reg; ';
        $html .= Horde::img('block/weatherdotcom/32x32/TWClogo_32px.png',
            'weather.com logo');
        $html .= '</a></td></tr></table>';

        return $html;
    }

}
