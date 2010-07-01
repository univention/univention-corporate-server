<?php

$block_name = _("Moon Phases");

/**
 * $Horde: horde/lib/Block/moon.php,v 1.16.10.5 2007-12-20 15:01:36 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Horde_moon extends Horde_Block {

    var $_app = 'horde';

    function _title()
    {
        return _("Moon Phases");
    }

    function _params()
    {
        return array(
            'phase' => array(
                'name' => _("Which phases"),
                'type' => 'enum',
                'default' => 'current',
                'values' => array('current' => _("Current 4 Phases"),
                                  'next' => _("Next 4 Phases"))),
            'hemisphere' => array(
                'name' => _("Hemisphere"),
                'type' => 'enum',
                'default' => 'northern',
                'values' => array('northern' => _("Northern Hemisphere"),
                                  'southern' => _("Southern Hemisphere"))),
            );
    }

    function _content()
    {
        $phases = $this->_calculateMoonPhases(date('Y'));
        $now = time();

        $lastNew = 0;
        $lastNewStamp = 0;
        $offset = 0;
        foreach ($phases as $key => $val) {
            if ($key < $now && $key > $lastNewStamp && $val == _("New Moon")) {
                $lastNew = $offset;
                $lastNewStamp = $key;
            }
            $offset++;
        }

        if (isset($this->_params['phase']) && $this->_params['phase'] == 'next') {
            $dates = array_slice(array_keys($phases), $lastNew + 4, 4);
        } else {
            $dates = array_slice(array_keys($phases), $lastNew, 4);
        }

        if (isset($this->_params['hemisphere']) && $this->_params['hemisphere'] == 'northern') {
            $location = _("Northern Hemisphere");
        } else {
            $location = _("Southern Hemisphere");
        }

        $html = '<table width="100%" height="100%" cellspacing="0">' .
            '<tr><td colspan="4" class="control"><strong>' . $location . '</strong></td></tr>' .
            '<tr height="100%"><td width="25%" align="center">' .
            Horde::img('block/moon/newmoon.png', _("New Moon")) .
            '<br />' . strftime('%d %b', $dates[0]) .
            '</td>';

        $html .= '<td width="25%" align="center">';
        if (isset($this->_params['hemisphere']) && $this->_params['hemisphere'] == 'northern') {
            $html .= Horde::img('block/moon/lastquarter.png', _("First Quarter"));
        } else {
            $html .= Horde::img('block/moon/firstquarter.png', _("First Quarter"));
        }
        $html .= '<br />' . strftime('%d %b', $dates[1]) . '</td>';

        $html .= '<td width="25%" align="center">' .
            Horde::img('block/moon/fullmoon.png', _("Full Moon")) .
            '<br />' . strftime('%d %b', $dates[2]) . '</td>';

        $html .= '<td width="25%" align="center">';
        if (isset($this->_params['hemisphere']) && $this->_params['hemisphere'] == 'northern') {
            $html .= Horde::img('block/moon/firstquarter.png', _("Last Quarter"));
        } else {
            $html .= Horde::img('block/moon/lastquarter.png', _("Last Quarter"));
        }
        $html .= '<br />' . strftime('%d %b', $dates[3]) . '</td></tr></table>';

        return $html;
    }

    /**
     * Returns an array with all the phases of the moon for a whole
     * year.
     *
     * Based on code from
     * http://www.zend.com/codex.php?id=830&single=1 by Are Pedersen.
     *
     * Converted from Basic by Roger W. Sinnot, Sky & Telescope, March 1985.
     * Converted from javascript by Are Pedersen 2002
     * Javascript found at http://www.stellafane.com/moon_phase/moon_phase.htm
     *
     * @param integer   $year   The four digit year to return the moon
     *                          phases for.
     *
     * @return array    The moon phases.
     */
    function _calculateMoonPhases($Y)
    {
        $R1 = 3.14159265 / 180;
        $U  = false;
        $K0 = intval(($Y - 1900) * 12.3685);
        $T  = ($Y - 1899.5) / 100;
        $T2 = $T * $T;
        $T3 = $T * $T * $T;
        $J0 = 2415020 + 29 * $K0;
        $F0 = 0.0001178 * $T2 - 0.000000155 * $T3;
        $F0 += (0.75933 + 0.53058868*$K0);
        $F0 -= (0.000837 * $T + 0.000335 * $T2);
        $M0  = $K0 * 0.08084821133;
        $M0  = 360 * ($M0 - intval($M0)) + 359.2242;
        $M0 -= 0.0000333 * $T2;
        $M0 -= 0.00000347 * $T3;
        $M1  = $K0 * 0.07171366128;
        $M1  = 360 * ($M1 - intval($M1)) + 306.0253;
        $M1 += 0.0107306 * $T2;
        $M1 += 0.00001236 * $T3;
        $B1  = $K0 * 0.08519585128;
        $B1  = 360 * ($B1 - intval($B1)) + 21.2964;
        $B1 -= 0.0016528 * $T2;
        $B1 -= 0.00000239 * $T3;
        for ($K9 = 0; $K9 <= 28; $K9 = $K9 + 0.5) {
            $J = $J0 + 14 * $K9;
            $F = $F0 + 0.765294 * $K9;
            $K = $K9 / 2;
            $M5 = ($M0 + $K * 29.10535608) * $R1;
            $M6 = ($M1 + $K * 385.81691806) * $R1;
            $B6 = ($B1 + $K * 390.67050646) * $R1;
            $F -= 0.4068 * sin($M6);
            $F += (0.1734 - 0.000393 * $T) * sin($M5);
            $F += 0.0161 * sin(2 * $M6);
            $F += 0.0104 * sin(2 * $B6);
            $F -= 0.0074 * sin($M5 - $M6);
            $F -= 0.0051 * sin($M5 + $M6);
            $F += 0.0021 * sin(2 * $M5);
            $F += 0.0010 * sin(2 * $B6 - $M6);

            /* Add 1/2 minute for proper rounding to minutes per Sky &
             * Tel article. */
            $F += 0.5 / 1440;
            $J += intval($F);
            $F -= intval($F);

            /* Convert from JD to Calendar Date. */
            $julian = $J + round($F);
            $parts  = explode('/', $this->_jdtogregorian($julian));
            $stamp  = gmmktime(0, 0, 0, $parts[0], $parts[1], $parts[2]);

            /* half K. */
            if (($K9 - floor($K9)) > 0) {
                if ($U) {
                    /* New half. */
                    $phases[$stamp] = _("First Half");
                } else {
                    /* Full half. */
                    $phases[$stamp] = _("Last Half");
                }
            } else {
                /* full K. */
                if (!$U) {
                    $phases[$stamp] = _("New Moon");
                } else {
                    $phases[$stamp] = _("Full Moon");
                }
                $U = !$U;
            }
        }

        return $phases;
    }

    /**
     * Checks if the jdtogregorian function exists, and if not
     * calculates the gregorian date manually.
     *
     * @param int $julian The julian date
     *
     * @return string m/d/Y
     */
    function _jdtogregorian($julian)
    {
        if (function_exists('jdtogregorian')) {
            return jdtogregorian($julian);
        } else {
            // From http://php.net/manual/en/function.jdtogregorian.php
            $julian = $julian - 1721119;
            $calc1 = 4 * $julian - 1;
            $year = floor($calc1 / 146097);
            $julian = floor($calc1 - 146097 * $year);
            $day = floor($julian / 4);
            $calc2 = 4 * $day + 3;
            $julian = floor($calc2 / 1461);
            $day = $calc2 - 1461 * $julian;
            $day = floor(($day + 4) / 4);
            $calc3 = 5 * $day - 3;
            $month = floor($calc3 / 153);
            $day = $calc3 - 153 * $month;
            $day = floor(($day + 5) / 5);
            $year = 100 * $year + $julian;

            if ($month < 10) {
                $month = $month + 3;
            } else {
                $month = $month - 9;
                $year = $year + 1;
            }
            return "$month/$day/$year";
        }
    }

}
