<?php
/**
 * Helper functions to handle format conversions.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/Date.php,v 1.2.2.5 2009-01-06 15:23:13 jan Exp $
 *
 * @package Kolab_Format
 */

/**
 * Kolab date handling functions. Based upon Kolab.php from Stuart Binge.
 *
 * $Horde: framework/Kolab_Format/lib/Horde/Kolab/Format/Date.php,v 1.2.2.5 2009-01-06 15:23:13 jan Exp $
 *
 * Copyright 2004-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
 *
 * @author  Stuart Binge <omicron@mighty.co.za>
 * @author  Thomas Jarosch <thomas.jarosch@intra2net.com>
 * @package Kolab_Format
 */
class Horde_Kolab_Format_Date
{
    /**
     * Returns a UNIX timestamp corresponding the given date string which is in
     * the format prescribed by the Kolab Format Specification.
     *
     * @param string $date  The string representation of the date.
     *
     * @return integer  The unix timestamp corresponding to $date.
     */
    function decodeDate($date)
    {
        if (empty($date)) {
            return 0;
        }

        list($year, $month, $day) = explode('-', $date);

        return mktime(0, 0, 0, $month, $day, $year);
    }

    /**
     * Returns a UNIX timestamp corresponding the given date-time string which
     * is in the format prescribed by the Kolab Format Specification.
     *
     * @param string $datetime  The string representation of the date & time.
     *
     * @return integer  The unix timestamp corresponding to $datetime.
     */
    function decodeDateTime($datetime)
    {
        if (empty($datetime)) {
            return 0;
        }

        list($year, $month, $day, $hour, $minute, $second)
            = sscanf($datetime, '%d-%d-%dT%d:%d:%dZ');
        return gmmktime($hour, $minute, $second, $month, $day, $year);
    }

    /**
     * Returns a UNIX timestamp corresponding the given date or date-time
     * string which is in either format prescribed by the Kolab Format
     * Specification.
     *
     * @param string $date  The string representation of the date (& time).
     *
     * @return integer  The unix timestamp corresponding to $date.
     */
    function decodeDateOrDateTime($date)
    {
        if (empty($date)) {
            return 0;
        }

        return (strlen($date) == 10 ? Horde_Kolab_Format_Date::decodeDate($date) : Horde_Kolab_Format_Date::decodeDateTime($date));
    }

    /**
     * Returns a string containing the current UTC date in the format
     * prescribed by the Kolab Format Specification.
     *
     * @return string  The current UTC date in the format 'YYYY-MM-DD'.
     */
    function encodeDate($date = false)
    {
        if ($date === false) {
            $date = time();
        }

        return strftime('%Y-%m-%d', $date);
    }

    /**
     * Returns a string containing the current UTC date and time in the format
     * prescribed by the Kolab Format Specification.
     *
     * @return string    The current UTC date and time in the format
     *                   'YYYY-MM-DDThh:mm:ssZ', where the T and Z are literal
     *                   characters.
     */
    function encodeDateTime($datetime = false)
    {
        if ($datetime === false) {
            $datetime = time();
        }

        return gmstrftime('%Y-%m-%dT%H:%M:%SZ', $datetime);
    }
}
