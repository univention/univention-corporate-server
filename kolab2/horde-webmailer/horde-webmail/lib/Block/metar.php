<?php

if ((@include_once 'Services/Weather.php') &&
    !empty($GLOBALS['conf']['sql']['phptype'])) {
    $block_name = _("Metar Weather");
}

/**
 * The Horde_Block_metar class provides an applet for the portal
 * screen to display METAR weather data for a specified location
 * (currently airports).
 *
 * $Horde: horde/lib/Block/metar.php,v 1.22.10.11 2009-01-16 17:05:59 mrubinsk Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Horde_metar extends Horde_Block {

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
        return _("Current Weather");
    }

    function _params()
    {
        if (!@include_once 'Services/Weather.php') {
            Horde::logMessage('The metar block will not work without Services_Weather from PEAR. Run pear install Services_Weather.',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return array(
                'error' => array(
                    'type' => 'error',
                    'name' => _("Error"),
                    'default' => _("Metar block not available.")
                )
            );
        } else {
            global $conf;

            // Get locations from the database.
            require_once 'DB.php';
            $db = &DB::connect($conf['sql']);
            if (is_a($db, 'PEAR_Error')) {
                return $db;
            }

            // Set DB portability options.
            switch ($db->phptype) {
            case 'mssql':
                $db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS | DB_PORTABILITY_RTRIM);
                break;
            default:
                $db->setOption('portability', DB_PORTABILITY_LOWERCASE | DB_PORTABILITY_ERRORS);
            }

            $result = $db->query('SELECT icao, name, country FROM metarAirports ORDER BY country');
            if (is_a($result, 'PEAR_Error')) {
                return $result;
            }

            $locations = array();
            while ($row = $result->fetchRow(DB_FETCHMODE_ASSOC)) {
                $locations[$row['country']][$row['icao']] = $row['name'];
            }

            return array(
                'location' => array(
                    'type' => 'mlenum',
                    'name' => _("Location"),
                    'default' => 'KSFB',
                    'values' => $locations,
                ),
                'units' => array(
                    'type' => 'enum',
                    'name' => _("Units"),
                    'default' => 's',
                    'values' => array(
                        's' => _("Standard"),
                        'm' => _("Metric")
                    )
                ),
                'knots' => array(
                    'type' => 'checkbox',
                    'name' => _("Wind speed in knots"),
                    'default' => 0
                ),
                'taf' => array(
                    'type' => 'checkbox',
                    'name' => _("Display forecast (TAF)"),
                    'default' => 0
                )
            );
        }
    }

    function _row($label, $content)
    {
        return '<br /><strong>' . $label . ':</strong> ' . $content;
    }

    function _sameRow($label, $content)
    {
        return ' <strong>' . $label . ':</strong> ' . $content;
    }

    /**
     * The content to go in this block.
     *
     * @return string   The content
     */
    function _content()
    {
        if (!@include_once 'Services/Weather.php') {
            Horde::logMessage('The metar block will not work without Services_Weather from PEAR. Run pear install Services_Weather.',
                              __FILE__, __LINE__, PEAR_LOG_ERR);
            return _("Metar block not available. Details have been logged for the administrator.");
        }

        global $conf;
        static $metarLocs;

        if (!isset($conf['sql'])) {
            return _("A database backend is required for this block.");
        }

        if (empty($this->_params['location'])) {
            return _("No location is set.");
        }

        if (!is_array($metarLocs)) {
            $metarLocs = $this->getParams();
        }

        $metar = &Services_Weather::service('METAR', array('debug' => 0));
        $metar->setMetarDB($conf['sql']);
        $metar->setUnitsFormat($this->_params['units']);
        $metar->setDateTimeFormat('M j, Y', 'H:i');
        $metar->setMetarSource('http');

        $units = $metar->getUnitsFormat($this->_params['units']);
        $weather = $metar->getWeather($this->_params['location']);
        if (is_a($weather, 'PEAR_Error')) {
            $html = $weather->getMessage();
            return $html;
        }
        $html = '<table width="100%" cellspacing="0">' .
            '<tr><td class="control"><strong>' .
            sprintf('%s, %s (%s)',
                    $metarLocs['location']['values'][$this->_params['__location']][$this->_params['location']],
                    $this->_params['__location'],
                    $this->_params['location']) .
            '</strong></td></tr></table><strong>' . _("Last Updated:") . '</strong> ' .
            $weather['update'] . '<br /><br />';

        // Wind.
        if (isset($weather['wind'])) {
            $html .= '<strong>' . _("Wind:") . '</strong> ';
            if ($weather['windDirection'] == 'Variable') {
                if (!empty($this->_params['knots'])) {
                    $html .= sprintf(_("%s at %s %s"),
                        $weather['windDirection'],
                        round($metar->convertSpeed($weather['wind'],
                            $units['wind'], 'kt')),
                        'kt');
                } else {
                    $html .= sprintf(_("%s at %s %s"),
                        $weather['windDirection'],
                        round($weather['wind']),
                        $units['wind']);
                }
            } elseif (($weather['windDegrees'] == '000') &&
                        ($weather['wind'] == '0')) {
                $html .= sprintf(_("calm"));
            } else {
                $html .= sprintf(_("from the %s (%s) at %s %s"),
                                 $weather['windDirection'],
                                 $weather['windDegrees'],
                                 empty($this->_params['knots']) ?
                                 round($weather['wind']) :
                                 round($metar->convertSpeed($weather['wind'], $units['wind'], 'kt')),
                                 empty($this->_params['knots']) ?
                                 $units['wind'] :
                                 'kt');
            }
        }
        if (isset($weather['windGust'])) {
            if ($weather['windGust']) {
                if (!empty($this->_params['knots'])) {
                    $html .= sprintf(_(", gusting %s %s"),
                        round($metar->convertSpeed($weather['windGust'],
                        $units['wind'], 'kt')),
                        'kt');
                } else {
                    $html .= sprintf(_(", gusting %s %s"),
                        round($weather['windGust']),
                        $units['wind']);
                }
            }
        }
        if (isset($weather['windVariability'])) {
            if ($weather['windVariability']['from']) {
                $html .= sprintf(_(", variable from %s to %s"),
                    $weather['windVariability']['from'],
                    $weather['windVariability']['to']);
            }
        }

        // Visibility.
        if (isset($weather['visibility'])) {
            $html .= $this->_sameRow(_("Visibility"), $weather['visibility'] . ' ' . $units['vis']);
        }

        // Temperature/DewPoint.
        if (isset($weather['temperature'])) {
            $html .= $this->_row(_("Temperature"), round($weather['temperature']) . '&deg;' . String::upper($units['temp']));
        }
        if (isset($weather['dewPoint'])) {
            $html .= $this->_sameRow(_("Dew Point"), round($weather['dewPoint']) . '&deg;' . String::upper($units['temp']));
        }
        if (isset($weather['feltTemperature'])) {
            $html .= $this->_sameRow(_("Feels Like"), round($weather['feltTemperature']) . '&deg;' . String::upper($units['temp']));
        }

        // Pressure.
        if (isset($weather['pressure'])) {
            $html .= $this->_row(_("Pressure"), $weather['pressure'] . ' ' . $units['pres']);
        }

        // Humidity.
        if (isset($weather['humidity'])) {
            $html .= $this->_sameRow(_("Humidity"), round($weather['humidity']) . '%');
        }

        // Clouds.
        if (isset($weather['clouds'])) {
            $clouds = '';
            foreach ($weather['clouds'] as $cloud) {
                $clouds .= '<br />';
                if (isset($cloud['height'])) {
                    $clouds .= sprintf(_("%s at %s %s"), $cloud['amount'], $cloud['height'], $units['height']);
                } else {
                    $clouds .= $cloud['amount'];
                }
            }
            $html .= $this->_row(_("Clouds"), $clouds);
        }

        // Conditions.
        if (isset($weather['condition'])) {
            $html .= $this->_row(_("Conditions"), $weather['condition']);
        }

        // Remarks.
        if (isset($weather['remark'])) {
            $remarks = '';
            $other = '';
            foreach ($weather['remark'] as $remark => $value) {
                switch ($remark) {
                case 'seapressure':
                    $remarks .= '<br />' . _("Pressure at sea level: ") . $value . ' ' . $units['pres'];
                    break;

                case 'precipitation':
                    foreach ($value as $precip) {
                        if (is_numeric($precip['amount'])) {
                            $remarks .= '<br />' .
                                sprintf(ngettext("Precipitation for last %d hour: ", "Precipitation for last %d hours: ", $precip['hours']),
                                        $precip['hours']) .
                                $precip['amount'] . ' ' . $units['rain'];
                        } else {
                            $remarks .= '<br />' .
                                sprintf(ngettext("Precipitation for last %d hour: ", "Precipitation for last %d hours: ", $precip['hours']),
                                        $precip['hours']) . $precip['amount'];
                        }
                    }
                    break;

                case 'snowdepth':
                    $remarks .= '<br />' . _("Snow depth: ") . $value . ' ' . $units['rain'];
                    break;

                case 'snowequiv':
                    $remarks .= '<br />' . _("Snow equivalent in water: ") . $value . ' ' . $units['rain'];
                    break;

                case 'sunduration':
                    $remarks .= '<br />' . sprintf(_("%d minutes"), $value);
                    break;

                case '1htemp':
                    $remarks .= '<br />' . _("Temp for last hour: ") . round($value) . '&deg;' . String::upper($units['temp']);
                    break;

                case '1hdew':
                    $remarks .= '<br />' . _("Dew Point for last hour: ") . round($value) . '&deg;' . String::upper($units['temp']);
                    break;

                case '6hmaxtemp':
                    $remarks .= '<br />' . _("Max temp last 6 hours: ") . round($value) . '&deg;' . String::upper($units['temp']);
                    break;

                case '6hmintemp':
                    $remarks .= '<br />' . _("Min temp last 6 hours: ") . round($value) . '&deg;' . String::upper($units['temp']);
                    break;

                case '24hmaxtemp':
                    $remarks .= '<br />' . _("Max temp last 24 hours: ") . round($value) . '&deg;' . String::upper($units['temp']);
                    break;

                case '24hmintemp':
                    $remarks .= '<br />' . _("Min temp last 24 hours: ") . round($value) . '&deg;' . String::upper($units['temp']);
                    break;

                case 'sensors':
                    foreach ($value as $sensor) {
                        $remarks .= '<br />' .
                            _("Sensor: ") . $sensor;
                    }
                    break;

                default:
                    $other .= '<br />' . $value;
                    break;
                }
            }

            $html .= $this->_row(_("Remarks"), $remarks . $other);
        }

        // TAF
        if (!empty($this->_params['taf'])) {
            $taf = $metar->getForecast($this->_params['location']);
            if (!is_a($taf, 'PEAR_Error')) {
                $forecast = '<table width="100%" cellspacing="0">';
                $forecast .= '<tr><td class="control" colspan="2"><center><strong>' . _("Forecast (TAF)") . '</strong></td></tr></table>';
                $forecast .= '<strong>Valid: </strong>' . $taf['validFrom'] . ' - ' . $taf['validTo'] . '<br /><br />';
                $item = 0;
                foreach ($taf['time'] as $time => $entry) {
                    $item++;
                    $forecast .= '<table width="100%" cellspacing="0">';
                    $forecast .= '<tr class="item' . ($item % 2) . '">';
                    $forecast .= '<td align="center" width="50">' . $time . '</td><td><strong>Wind:</strong> ';
                    if (isset($entry['wind'])) {
                        if ($entry['windDirection'] == 'Variable') {
                            if (!empty($this->_params['knots'])) {
                                $forecast .= sprintf(_("%s at %s %s"),
                                    strtolower($entry['windDirection']),
                                    round($metar->convertSpeed($entry['wind'],
                                        $units['wind'], 'kt')),
                                    'kt');
                            } else {
                                $forecast .= sprintf(_("%s at %s %s"),
                                    $entry['windDirection'],
                                    round($entry['wind']),
                                    $units['wind']);
                            }
                        } elseif (($entry['windDegrees'] == '000') &&
                                    ($entry['wind'] == '0')) {
                            $forecast .= sprintf(_("calm"));
                        } else {
                            $forecast .= sprintf(_("from the %s (%s) at %s %s"),
                                             $entry['windDirection'],
                                             $entry['windDegrees'],
                                             empty($this->_params['knots']) ?
                                             round($entry['wind']) :
                                             round($metar->convertSpeed($entry['wind'], $units['wind'], 'kt')),
                                             empty($this->_params['knots']) ?
                                             $units['wind'] :
                                             'kt');
                        }
                        $forecast .= '<br />';
                    }
                    if (isset($entry['temperatureLow']) || isset($entry['temperatureHigh'])) {
                        $forecast .= '<strong>Temperature</strong>';
                        if (isset($entry['temperatureLow'])) {
                            $forecast .= '<strong> Low:</strong>';
                            $forecast .= $entry['temperatureLow'];
                        }
                        if (isset($entry['temperatureHigh'])) {
                            $forecast .= '<strong> High:</strong>';
                            $forecast .= $entry['temperatureHigh'];
                        }
                        $forecast .= '<br />';
                    }
                    if (isset($entry['windshear'])) {
                        $forecast .= '<strong>Windshear:</strong>';
                        $forecast .= sprintf(_("from the %s (%s) at %s %s"),
                                        $entry['windshearDirection'],
                                        $entry['windshearDegrees'],
                                        $entry['windshearHeight'],
                                        $units['height']);
                        $forecast .= '<br />';
                    }
                    if (isset($entry['visibility'])) {
                        $forecast .= '<strong>Visibility:</strong> ';
                        $forecast .= strtolower($entry['visQualifier']) . ' ' . $entry['visibility'] . ' ' . $units['vis'];
                        $forecast .= '<br />';
                    }
                    if (isset($entry['condition'])) {
                        $forecast .= '<strong>Conditions:</strong> ';
                        $forecast .= $entry['condition'];
                        $forecast .= '<br />';
                    }
                    $forecast .= '<strong>Clouds:</strong> ';
                    foreach ($entry['clouds'] as $clouds) {
                        if (isset($clouds['type'])) {
                            $forecast .= ' ' . $clouds['type'];
                        }
                        $forecast .= ' ' . $clouds['amount'];
                        if (isset($clouds['height'])) {
                            $forecast .= ' at ' . $clouds['height'] . ' ' . $units['height'];
                        } else {
                            $forecast .= ' ';
                        }
                    }
                    $forecast .= '</td></tr>';
                    if (isset($entry['fmc'])) {
                        $item++;
                        foreach ($entry['fmc'] as $fmcEntry) {
                            $forecast .= '<tr class="item' . ($item % 2) . '">';
                            $forecast .= '<td align="center" width="50">';
                            $forecast .= '* ' . $fmcEntry['from'] . '<br /> - ' . $fmcEntry['to'] . '</td>';
                            $forecast .= '<td>';
                            $forecast .= '<strong>Type: </strong>' . $fmcEntry['type'];
                            if (isset($fmcEntry['probability'])) {
                                $forecast .= ' <strong> Prob: </strong>' . $fmcEntry['probability'] . '%';
                            }
                            if (isset($fmcEntry['condition'])) {
                                $forecast .= ' <strong> Conditions: </strong>' . $fmcEntry['condition'];
                            }
                            if (isset($fmcEntry['clouds'])) {
                                $forecast .= ' <strong>Clouds:</strong>';
                                foreach ($fmcEntry['clouds'] as $fmcClouds) {
                                    if (isset($fmcClouds['type'])) {
                                        $forecast .= ' ' . $fmcClouds['type'];
                                    }
                                    if (isset($fmcClouds['height'])) {
                                        $forecast .= ' ' . $fmcClouds['amount'];
                                        $forecast .= ' ' . $fmcClouds['height'];
                                        $forecast .= ' ' . $units['height'];
                                    } else {
                                        $forecast .= ' ' . $fmcClouds['amount'];
                                    }
                                }
                            }
                            if (isset($fmcEntry['visQualifier'])) {
                                $forecast .= ' <strong>Visibility:</strong> ';
                                $forecast .= strtolower($fmcEntry['visQualifier']) . ' ';
                                $forecast .= $fmcEntry['visibility'] . ' ' . $units['vis'];
                            }
                            $forecast .= '</td></tr>';
                        }
                    }

                }
                $forecast .= '</table>';

                $html .= $forecast;
            }
        }

        return $html;
    }

}
