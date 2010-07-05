<?php

$block_name = _("Sunrise/Sunset");

/**
 * $Horde: horde/lib/Block/sunrise.php,v 1.14.10.4 2007-12-20 15:01:36 jan Exp $
 *
 * @package Horde_Block
 */
class Horde_Block_Horde_sunrise extends Horde_Block {

    var $_app = 'horde';

    function _title()
    {
        return _("Sunrise/Sunset");
    }

    function _params()
    {
        $params = array('location' => array('type' => 'mlenum',
                                            'name' => _("Location"),
                                            'default' => '51.517:-0.117'));

        global $coordinates;
        if (!is_array($coordinates)) {
            include 'Horde/NLS/coordinates.php';
            if (!is_array($coordinates)) {
                $coordinates = array();
            }
        }
        $params['location']['values'] = $coordinates;

        return $params;
    }

    function _content()
    {
        if (empty($this->_params['location'])) {
            return _("No location is set.");
        }

        // Set the timezone variable, if available.
        NLS::setTimeZone();

        list($lat, $long) = explode(':', $this->_params['location']);
        $rise = $this->_calculateSunset(time(), $lat, $long, false, floor(date('Z') / 3600));
        $set = $this->_calculateSunset(time(), $lat, $long, true, floor(date('Z') / 3600));

        $location = '';
        global $coordinates;
        if (!is_array($coordinates)) {
            require 'Horde/NLS/coordinates.php';
        }
        foreach ($coordinates as $country) {
            if (array_key_exists($this->_params['location'], $country)) {
                $location = $country[$this->_params['location']];
                break;
            }
        }

        return '<table width="100%" height="100%" cellspacing="0"><tr>' .
            '<td colspan="2" class="control"><strong>' . $location . '</strong></td></tr><tr height="100%">' .
            '<td width="50%" align="center">' .
            Horde::img('block/sunrise/sunrise.png', _("Sun Rise")) .
            '<br />' . $rise . '</td>' .
            '<td width="50%" align="center">' .
            Horde::img('block/sunrise/sunset.png', _("Sun Set")) .
            '<br />' . $set . '</td>' . '</tr></table>';
    }

    /**
     * http://www.zend.com/codex.php?id=135&single=1
     */
    function _calculateSunset($date, $latitude, $longitude, $sunset = true, $timezone)
    {
        $yday = date('z', $date);
        $mon = date('n', $date);
        $mday = date('j', $date);
        $year = date('Y', $date);

        if ($timezone == '13') {
            $timezone = '-11';
            $mday++;
            $yday++;
        }

        $A = 1.5708;
        $B = 3.14159;
        $C = 4.71239;
        $D = 6.28319;
        $E = 0.0174533 * $latitude;
        $F = 0.0174533 * $longitude;
        $G = 0.261799  * $timezone;

        // For astronomical twilight, use R = -.309017
        // For nautical twilight, use R = -.207912
        // For civil twilight, use R = -.104528
        // For sunrise or sunset, use R = -.0145439
        $R = -.0145439;

        if ($sunset) {
            $J = $C;
        } else {
            $J = $A;
        }

        $K = $yday + (($J - $F) / $D);
        $L = ($K * .017202) - .0574039;              // Solar Mean Anomoly
        $M = $L + .0334405 * sin($L);                // Solar True Longitude
        $M += 4.93289 + (3.49066E-04) * sin(2 * $L); // Quadrant Determination
        while ($M < 0) {
            $M = ($M + $D);
        }
        while ($M >= $D) {
            $M = ($M - $D);
        }

        if (($M / $A) - intval($M / $A) == 0) {
            $M += 4.84814E-06;
        }

        $P = sin($M) / cos($M);                   // Solar Right Ascension
        $P = atan2(.91746 * $P, 1);

        // Quadrant Adjustment
        if ($M > $C) {
            $P += $D;
        } elseif ($M > $A) {
            $P += $B;
        }

        $Q = .39782 * sin($M);            // Solar Declination
        $Q = $Q / sqrt(-$Q * $Q + 1);     // This is how the original author wrote it!
        $Q = atan2($Q, 1);

        $S = $R - (sin($Q) * sin($E));
        $S = $S / (cos($Q) * cos($E));

        if (abs($S) > 1) {
            return 'none';                // Null phenomenon
        }

        $S = $S / sqrt(-$S * $S + 1);
        $S = $A - atan2($S, 1);

        if (!$sunset) {
            $S = $D - $S ;
        }

        $T = $S + $P - 0.0172028 * $K - 1.73364; // Local apparent time
        $U = $T - $F;                            // Universal timer
        $V = $U + $G;                            // Wall clock time

        // Quadrant Determination
        while ($V < 0) {
            $V = ($V + $D);
        }
        while ($V >= $D) {
            $V = ($V - $D);
        }
        $V = $V * 3.81972;

        $hour = intval($V);
        $V   -= $hour;
        $min  = intval($V * 60);
        $V   -= $min / 60;
        $sec  = intval($V * 3600);

        return strftime('%X', mktime($hour, $min, $sec, $mon, $mday, $year));
    }

}
