<?php
/**
 * The Horde_Block_metar class provides an applet for the portal
 * screen to display METAR weather data for a specified location
 * (currently airports).
 *
 * $Horde: horde/lib/Block/metar.php,v 1.17 2004/05/29 16:21:03 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_metar extends Horde_Block {

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

    function getParams()
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
                )
            );
        }
    }

    function _row($label, $content)
    {
        return '<br /><b>' . $label . ':</b> ' . $content;
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

        require_once 'Services/Weather.php';
        $metar = &Services_Weather::service('METAR', array('debug' => 0));
        $dbString = $conf['sql']['phptype'] . '://';
        $dbString .= $conf['sql']['username'] . ':';
        $dbString .= $conf['sql']['password'] . '@';
        $dbString .= $conf['sql']['hostspec'] . '/';
        $dbString .= $conf['sql']['database'];
        $metar->setMetarDB($dbString);
        $metar->setUnitsFormat($this->_params['units']);
        $metar->setDateTimeFormat('M j, Y', 'H:i');
        $metar->setMetarSource('http');

        $units = $metar->getUnits(0, $this->_params['units']);
        $weather = $metar->getWeather($this->_params['location']);

        $html = '<table width="100%" border="0" cellpadding="0" cellspacing="0">' .
            '<tr><td class="control"><b>' .
            sprintf('%s, %s (%s)',
                    $metarLocs['location']['values'][$this->_params['__location']][$this->_params['location']],
                    $this->_params['__location'],
                    $this->_params['location']) .
            '</td></tr></table><b>' . _("Last Updated:") . '</b> ' .
            $weather['update'] . '<br /><br />';

        // Wind.
        if (isset($weather['wind'])) {
            $html .= '<b>' . _("Wind:") . '</b> ';
            if ($weather['windDirection'] == 'Variable') {
                if (!empty($this->_params['knots'])) {
                    $html .= sprintf(_('%s at %s %s'),
                        $weather['windDirection'],
                        round($metar->convertSpeed($weather['wind'],
                            $units['wind'], 'kt')),
                        'kt');
                } else {
                    $html .= sprintf(_('%s at %s %s'),
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
            $html .= $this->_row(_("Visibility"), $weather['visibility'] . ' ' . $units['vis']);
        }

        // Temperature/DewPoint.
        if (isset($weather['temperature'])) {
            $html .= $this->_row(_("Temperature"), round($weather['temperature']) . '&deg;' . String::upper($units['temp']));
        }
        if (isset($weather['dewPoint'])) {
            $html .= $this->_row(_("Dew Point"), round($weather['dewPoint']) . '&deg;' . String::upper($units['temp']));
        }
        if (isset($weather['feltTemperature'])) {
            $html .= $this->_row(_("Feels Like"), round($weather['feltTemperature']) . '&deg;' . String::upper($units['temp']));
        }

        // Pressure.
        if (isset($weather['pressure'])) {
            $html .= $this->_row(_("Pressure"), $weather['pressure'] . ' ' . $units['pres']);
        }

        // Humidity.
        if (isset($weather['humidity'])) {
            $html .= $this->_row(_("Humidity"), round($weather['humidity']) . '%');
        }

        // Clouds.
        if (isset($weather['clouds'])) {
            $clouds = '';
            foreach ($weather['clouds'] as $cloud) {
                $clouds .= '<br />';
                if (isset($cloud['height'])) {
                    $clouds .= sprintf(_("%s at %s ft"), $cloud['amount'], $cloud['height']);
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
                                sprintf(_("Precipitation for last %s hour(s): "),
                                        $precip['hours']) .
                                $precip['amount'] . ' ' . $units['rain'];
                        } else {
                            $remarks .= '<br />' .
                                sprintf(_("Precipitation for last %s hour(s): "),
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
                    $remarks .= '<br />' . sprintf(_("%s minutes"), $value);
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

        return $html;
    }

}
