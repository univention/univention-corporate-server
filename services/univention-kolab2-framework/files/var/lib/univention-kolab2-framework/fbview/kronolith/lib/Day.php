<?php
/**
 * The Kronolith_Day:: class provides an API for dealing with days.
 *
 * $Horde: kronolith/lib/Day.php,v 1.23 2004/04/03 03:40:07 chuck Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith_Day {

    var $month;
    var $mday;
    var $year;
    var $time;
    var $hours;

    function Kronolith_Day($month = null, $day = null, $year = null, $timestamp = null)
    {
        if (!empty($timestamp)) {
            $this->time = $timestamp;
        } else {
            if (empty($month)) {
                $month = date('n');
            }
            if (empty($year)) {
                $year = date('Y');
            }
            if (empty($day)) {
                $day = date('j');
            }

            // Now, compensate for any wrap around.
            $this->time = mktime(0, 0, 0, $month, $day, $year);
        }

        $this->month = date('n', $this->time);
        $this->year = date('Y', $this->time);
        $this->mday = date('j', $this->time);

        // Make the data array.
        $this->makeHours();
    }

    function makeHours()
    {
        $this->hours = array();

        $row = 0;
        for ($i = 0; $i < 48; $i++) {
            $this->hours[$i]['timestamp'] = mktime(0, $i * 30, 0, $this->month, $this->mday, $this->year);
        }
    }

    function getTime($format, $offset = 0)
    {
        return strftime($format,
                        mktime(0, 0, 0, $this->month, ($this->mday + $offset), $this->year));
    }

    function getTomorrow()
    {
        return mktime(0, 0, 0, $this->month, $this->mday + 1, $this->year);
    }

    function getStamp()
    {
        return mktime(0, 0, 0, $this->month, $this->mday, $this->year);
    }

    function isToday()
    {
        return (mktime(0, 0, 0, $this->month, $this->mday, $this->year) == mktime(0, 0, 0));
    }

    function isTomorrow()
    {
        return (mktime(0, 0, 0, $this->month, $this->mday - 1, $this->year) == mktime(0, 0, 0));
    }

}
