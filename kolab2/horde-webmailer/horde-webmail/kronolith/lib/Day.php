<?php
/**
 * The Kronolith_Day:: class provides an API for dealing with days.
 *
 * $Horde: kronolith/lib/Day.php,v 1.26.10.3 2007-12-20 14:12:32 jan Exp $
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Kronolith 0.1
 * @package Kronolith
 */
class Kronolith_Day extends Horde_Date {

    /**
     * How many time slots are we dividing each hour into? Set from user
     * preferences.
     *
     * @var integer
     */
    var $_slotsPerHour;

    /**
     * How many slots do we have per day? Calculated from $_slotsPerHour.
     *
     * @see $_slotsPerHour
     * @var integer
     */
    var $_slotsPerDay;

    /**
     * How many minutes are in each slot? Calculated from $_slotsPerHour.
     *
     * @see $_slotsPerHour
     * @var integer
     */
    var $_slotLength;

    /**
     * Array of slots holding timestamps for each piece of this day.
     *
     * @var array
     */
    var $slots = array();

    function Kronolith_Day($month = null, $day = null, $year = null)
    {
        if (empty($month)) {
            $month = date('n');
        }
        if (empty($year)) {
            $year = date('Y');
        }
        if (empty($day)) {
            $day = date('j');
        }

        $this->Horde_Date(array('year' => $year, 'month' => $month, 'mday' => $day));
        $this->correct();

        $this->_slotsPerHour = $GLOBALS['prefs']->getValue('slots_per_hour');
        if (!$this->_slotsPerHour) {
            $this->_slotsPerHour = 1;
        }
        $this->_slotsPerDay = $this->_slotsPerHour * 24;
        $this->_slotLength = 60 / $this->_slotsPerHour;

        for ($i = 0; $i < $this->_slotsPerDay; $i++) {
            $this->slots[$i]['timestamp'] = mktime(0, $i * $this->_slotLength, 0,
                                                   $this->month, $this->mday, $this->year);
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

    function getStamp($offset = 0)
    {
        return mktime(0, 0, 0, $this->month, ($this->mday + $offset), $this->year);
    }

    function isToday()
    {
        return (mktime(0, 0, 0, $this->month, $this->mday, $this->year) == mktime(0, 0, 0));
    }

    function isTomorrow()
    {
        return (mktime(0, 0, 0, $this->month, $this->mday - 1, $this->year) == mktime(0, 0, 0));
    }

    function diff()
    {
        $day2 = &new Kronolith_Day();
        return Date_Calc::dateDiff($this->mday, $this->month, $this->year,
                                   $day2->mday, $day2->month, $day2->year);
    }

}
