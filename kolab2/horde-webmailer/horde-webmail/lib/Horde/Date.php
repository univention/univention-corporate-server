<?php

define('HORDE_DATE_SUNDAY',    0);
define('HORDE_DATE_MONDAY',    1);
define('HORDE_DATE_TUESDAY',   2);
define('HORDE_DATE_WEDNESDAY', 3);
define('HORDE_DATE_THURSDAY',  4);
define('HORDE_DATE_FRIDAY',    5);
define('HORDE_DATE_SATURDAY',  6);

define('HORDE_DATE_MASK_SUNDAY',    1);
define('HORDE_DATE_MASK_MONDAY',    2);
define('HORDE_DATE_MASK_TUESDAY',   4);
define('HORDE_DATE_MASK_WEDNESDAY', 8);
define('HORDE_DATE_MASK_THURSDAY', 16);
define('HORDE_DATE_MASK_FRIDAY',   32);
define('HORDE_DATE_MASK_SATURDAY', 64);
define('HORDE_DATE_MASK_WEEKDAYS', 62);
define('HORDE_DATE_MASK_WEEKEND',  65);
define('HORDE_DATE_MASK_ALLDAYS', 127);

define('HORDE_DATE_MASK_SECOND',    1);
define('HORDE_DATE_MASK_MINUTE',    2);
define('HORDE_DATE_MASK_HOUR',      4);
define('HORDE_DATE_MASK_DAY',       8);
define('HORDE_DATE_MASK_MONTH',    16);
define('HORDE_DATE_MASK_YEAR',     32);
define('HORDE_DATE_MASK_ALLPARTS', 63);

/**
 * Horde Date wrapper/logic class, including some calculation
 * functions.
 *
 * $Horde: framework/Date/Date.php,v 1.8.10.19 2009-12-10 12:19:58 jan Exp $
 *
 * @package Horde_Date
 */
class Horde_Date {

    /**
     * Year
     *
     * @var integer
     */
    var $year;

    /**
     * Month
     *
     * @var integer
     */
    var $month;

    /**
     * Day
     *
     * @var integer
     */
    var $mday;

    /**
     * Hour
     *
     * @var integer
     */
    var $hour = 0;

    /**
     * Minute
     *
     * @var integer
     */
    var $min = 0;

    /**
     * Second
     *
     * @var integer
     */
    var $sec = 0;

    /**
     * Internally supported strftime() specifiers.
     *
     * @var string
     */
    var $_supportedSpecs = '%CdDeHImMnRStTyY';

    /**
     * Build a new date object. If $date contains date parts, use them to
     * initialize the object.
     *
     * Recognized formats:
     * - arrays with keys 'year', 'month', 'mday', 'day' (since Horde 3.2),
     *   'hour', 'min', 'minute' (since Horde 3.2), 'sec'
     * - objects with properties 'year', 'month', 'mday', 'hour', 'min', 'sec'
     * - yyyy-mm-dd hh:mm:ss (since Horde 3.1)
     * - yyyymmddhhmmss (since Horde 3.1)
     * - yyyymmddThhmmssZ (since Horde 3.1.4)
     * - unix timestamps
     */
    function Horde_Date($date = null)
    {
        if (function_exists('nl_langinfo')) {
            $this->_supportedSpecs .= 'bBpxX';
        }

        if (is_array($date) || is_object($date)) {
            foreach ($date as $key => $val) {
                if (in_array($key, array('year', 'month', 'mday', 'hour', 'min', 'sec'))) {
                    $this->$key = (int)$val;
                }
            }

            // If $date['day'] is present and numeric we may have been passed
            // a Horde_Form_datetime array.
            if (is_array($date) && isset($date['day']) &&
                is_numeric($date['day'])) {
                $this->mday = (int)$date['day'];
            }
            // 'minute' key also from Horde_Form_datetime
            if (is_array($date) && isset($date['minute'])) {
                $this->min = $date['minute'];
            }
        } elseif (!is_null($date)) {
            // Match YYYY-MM-DD HH:MM:SS, YYYYMMDDHHMMSS and YYYYMMDD'T'HHMMSS'Z'.
            if (preg_match('/(\d{4})-?(\d{2})-?(\d{2})T? ?(\d{2}):?(\d{2}):?(\d{2})Z?/', $date, $parts)) {
                $this->year = (int)$parts[1];
                $this->month = (int)$parts[2];
                $this->mday = (int)$parts[3];
                $this->hour = (int)$parts[4];
                $this->min = (int)$parts[5];
                $this->sec = (int)$parts[6];
            } else {
                // Try as a timestamp.
                $parts = @getdate($date);
                if ($parts) {
                    $this->year = $parts['year'];
                    $this->month = $parts['mon'];
                    $this->mday = $parts['mday'];
                    $this->hour = $parts['hours'];
                    $this->min = $parts['minutes'];
                    $this->sec = $parts['seconds'];
                }
            }
        }
    }

    /**
     * @static
     */
    function isLeapYear($year)
    {
        if (strlen($year) != 4 || preg_match('/\D/', $year)) {
            return false;
        }

        return (($year % 4 == 0 && $year % 100 != 0) || $year % 400 == 0);
    }

    /**
     * Returns the day of the year (1-366) that corresponds to the
     * first day of the given week.
     *
     * TODO: with PHP 5.1+, see http://derickrethans.nl/calculating_start_and_end_dates_of_a_week.php
     *
     * @param integer $week  The week of the year to find the first day of.
     * @param integer $year  The year to calculate for.
     *
     * @return integer  The day of the year of the first day of the given week.
     */
    function firstDayOfWeek($week, $year)
    {
        $jan1 = new Horde_Date(array('year' => $year, 'month' => 1, 'mday' => 1));
        $start = $jan1->dayOfWeek();
        if ($start > HORDE_DATE_THURSDAY) {
            $start -= 7;
        }
        return (($week * 7) - (7 + $start)) + 1;
    }

    /**
     * @static
     */
    function daysInMonth($month, $year)
    {
        if ($month == 2) {
            if (Horde_Date::isLeapYear($year)) {
                return 29;
            } else {
                return 28;
            }
        } elseif ($month == 4 || $month == 6 || $month == 9 || $month == 11) {
            return 30;
        } else {
            return 31;
        }
    }

    /**
     * Return the day of the week (0 = Sunday, 6 = Saturday) of this
     * object's date.
     *
     * @return integer  The day of the week.
     */
    function dayOfWeek()
    {
        if ($this->month > 2) {
            $month = $this->month - 2;
            $year = $this->year;
        } else {
            $month = $this->month + 10;
            $year = $this->year - 1;
        }

        $day = (floor((13 * $month - 1) / 5) +
                $this->mday + ($year % 100) +
                floor(($year % 100) / 4) +
                floor(($year / 100) / 4) - 2 *
                floor($year / 100) + 77);

        return (int)($day - 7 * floor($day / 7));
    }

    /**
     * Returns the day number of the year (1 to 365/366).
     *
     * @return integer  The day of the year.
     */
    function dayOfYear()
    {
        $monthTotals = array(0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334);
        $dayOfYear = $this->mday + $monthTotals[$this->month - 1];
        if (Horde_Date::isLeapYear($this->year) && $this->month > 2) {
            ++$dayOfYear;
        }

        return $dayOfYear;
    }

    /**
     * Returns the week of the month.
     *
     * @since Horde 3.2
     *
     * @return integer  The week number.
     */
    function weekOfMonth()
    {
        return ceil($this->mday / 7);
    }

    /**
     * Returns the week of the year, first Monday is first day of first week.
     *
     * @return integer  The week number.
     */
    function weekOfYear()
    {
        return $this->format('W');
    }

    /**
     * Return the number of weeks in the given year (52 or 53).
     *
     * @static
     *
     * @param integer $year  The year to count the number of weeks in.
     *
     * @return integer $numWeeks   The number of weeks in $year.
     */
    function weeksInYear($year)
    {
        // Find the last Thursday of the year.
        $day = 31;
        $date = new Horde_Date(array('year' => $year, 'month' => 12, 'mday' => $day, 'hour' => 0, 'min' => 0, 'sec' => 0));
        while ($date->dayOfWeek() != HORDE_DATE_THURSDAY) {
            --$date->mday;
        }
        return $date->weekOfYear();
    }

    /**
     * Set the date of this object to the $nth weekday of $weekday.
     *
     * @param integer $weekday  The day of the week (0 = Sunday, etc).
     * @param integer $nth      The $nth $weekday to set to (defaults to 1).
     */
    function setNthWeekday($weekday, $nth = 1)
    {
        if ($weekday < HORDE_DATE_SUNDAY || $weekday > HORDE_DATE_SATURDAY) {
            return false;
        }

        $this->mday = 1;
        $first = $this->dayOfWeek();
        if ($weekday < $first) {
            $this->mday = 8 + $weekday - $first;
        } else {
            $this->mday = $weekday - $first + 1;
        }
        $this->mday += 7 * $nth - 7;

        $this->correct();

        return true;
    }

    function dump($prefix = '')
    {
        echo ($prefix ? $prefix . ': ' : '') . $this->year . '-' . $this->month . '-' . $this->mday . "<br />\n";
    }

    /**
     * Is the date currently represented by this object a valid date?
     *
     * @return boolean  Validity, counting leap years, etc.
     */
    function isValid()
    {
        if ($this->year < 0 || $this->year > 9999) {
            return false;
        }
        return checkdate($this->month, $this->mday, $this->year);
    }

    /**
     * Correct any over- or underflows in any of the date's members.
     *
     * @param integer $mask  We may not want to correct some overflows.
     */
    function correct($mask = HORDE_DATE_MASK_ALLPARTS)
    {
        if ($mask & HORDE_DATE_MASK_SECOND) {
            while ($this->sec < 0) {
                --$this->min;
                $this->sec += 60;
            }
            while ($this->sec > 59) {
                ++$this->min;
                $this->sec -= 60;
            }
        }

        if ($mask & HORDE_DATE_MASK_MINUTE) {
            while ($this->min < 0) {
                --$this->hour;
                $this->min += 60;
            }
            while ($this->min > 59) {
                ++$this->hour;
                $this->min -= 60;
            }
        }

        if ($mask & HORDE_DATE_MASK_HOUR) {
            while ($this->hour < 0) {
                --$this->mday;
                $this->hour += 24;
            }
            while ($this->hour > 23) {
                ++$this->mday;
                $this->hour -= 24;
            }
        }

        if ($mask & HORDE_DATE_MASK_MONTH) {
            while ($this->month > 12) {
                ++$this->year;
                $this->month -= 12;
            }
            while ($this->month < 1) {
                --$this->year;
                $this->month += 12;
            }
        }

        if ($mask & HORDE_DATE_MASK_DAY) {
            while ($this->mday > Horde_Date::daysInMonth($this->month, $this->year)) {
                $this->mday -= Horde_Date::daysInMonth($this->month, $this->year);
                ++$this->month;
                $this->correct(HORDE_DATE_MASK_MONTH);
            }
            while ($this->mday < 1) {
                --$this->month;
                $this->correct(HORDE_DATE_MASK_MONTH);
                $this->mday += Horde_Date::daysInMonth($this->month, $this->year);
            }
        }
    }

    /**
     * Compare this date to another date object to see which one is
     * greater (later). Assumes that the dates are in the same
     * timezone.
     *
     * @param mixed $date  The date to compare to.
     *
     * @return integer  ==  0 if the dates are equal
     *                  >=  1 if this date is greater (later)
     *                  <= -1 if the other date is greater (later)
     */
    function compareDate($date)
    {
        if (!is_a($date, 'Horde_Date')) {
            $date = new Horde_Date($date);
        }

        if ($this->year != $date->year) {
            return $this->year - $date->year;
        }
        if ($this->month != $date->month) {
            return $this->month - $date->month;
        }

        return $this->mday - $date->mday;
    }

    /**
     * Compare this to another date object by time, to see which one
     * is greater (later). Assumes that the dates are in the same
     * timezone.
     *
     * @param mixed $date  The date to compare to.
     *
     * @return integer  ==  0 if the dates are equal
     *                  >=  1 if this date is greater (later)
     *                  <= -1 if the other date is greater (later)
     */
    function compareTime($date)
    {
        if (!is_a($date, 'Horde_Date')) {
            $date = new Horde_Date($date);
        }

        if ($this->hour != $date->hour) {
            return $this->hour - $date->hour;
        }
        if ($this->min != $date->min) {
            return $this->min - $date->min;
        }

        return $this->sec - $date->sec;
    }

    /**
     * Compare this to another date object, including times, to see
     * which one is greater (later). Assumes that the dates are in the
     * same timezone.
     *
     * @param mixed $date  The date to compare to.
     *
     * @return integer  ==  0 if the dates are equal
     *                  >=  1 if this date is greater (later)
     *                  <= -1 if the other date is greater (later)
     */
    function compareDateTime($date)
    {
        if (!is_a($date, 'Horde_Date')) {
            $date = new Horde_Date($date);
        }

        if ($diff = $this->compareDate($date)) {
            return $diff;
        }

        return $this->compareTime($date);
    }

    /**
     * Get the time offset for local time zone.
     *
     * @param boolean $colon  Place a colon between hours and minutes?
     *
     * @return string  Timezone offset as a string in the format +HH:MM.
     */
    function tzOffset($colon = true)
    {
        $secs = $this->format('Z');

        if ($secs < 0) {
            $sign = '-';
            $secs = -$secs;
        } else {
            $sign = '+';
        }
        $colon = $colon ? ':' : '';
        $mins = intval(($secs + 30) / 60);
        return sprintf('%s%02d%s%02d',
                       $sign, $mins / 60, $colon, $mins % 60);
    }

    /**
     * Return the unix timestamp representation of this date.
     *
     * @return integer  A unix timestamp.
     */
    function timestamp()
    {
        if (class_exists('DateTime')) {
            return $this->format('U');
        } else {
            return Horde_Date::_mktime($this->hour, $this->min, $this->sec, $this->month, $this->mday, $this->year);
        }
    }

    /**
     * Return the unix timestamp representation of this date, 12:00am.
     *
     * @return integer  A unix timestamp.
     */
    function datestamp()
    {
        if (class_exists('DateTime')) {
            $dt = new DateTime();
            $dt->setDate($this->year, $this->month, $this->mday);
            $dt->setTime(0, 0, 0);
            return $dt->format('U');
        } else {
            return Horde_Date::_mktime(0, 0, 0, $this->month, $this->mday, $this->year);
        }
    }

    /**
     * Format time using the specifiers available in date() or in the DateTime
     * class' format() method.
     *
     * @since Horde 3.3
     *
     * @param string $format
     *
     * @return string  Formatted time.
     */
    function format($format)
    {
        if (class_exists('DateTime')) {
            $dt = new DateTime();
            $dt->setDate($this->year, $this->month, $this->mday);
            $dt->setTime($this->hour, $this->min, $this->sec);
            return $dt->format($format);
        } else {
            return date($format, $this->timestamp());
        }
    }

    /**
     * Format time in ISO-8601 format. Works correctly since Horde 3.2.
     *
     * @return string  Date and time in ISO-8601 format.
     */
    function iso8601DateTime()
    {
        return $this->rfc3339DateTime() . $this->tzOffset();
    }

    /**
     * Format time in RFC 2822 format.
     *
     * @return string  Date and time in RFC 2822 format.
     */
    function rfc2822DateTime()
    {
        return $this->format('D, j M Y H:i:s') . ' ' . $this->tzOffset(false);
    }

    /**
     * Format time in RFC 3339 format.
     *
     * @since Horde 3.1
     *
     * @return string  Date and time in RFC 3339 format. The seconds part has
     *                 been added with Horde 3.2.
     */
    function rfc3339DateTime()
    {
        return $this->format('Y-m-d\TH:i:s');
    }

    /**
     * Format time in the format we use for SQL queries.
     *
     * @since Horde 3.3.6
     *
     * @return string  Date and time in SQL format.
     */
    function sqlDateTime()
    {
        return $this->format('Y-m-d H:i:s');
    }

    /**
     * Format time to standard 'ctime' format.
     *
     * @return string  Date and time.
     */
    function cTime()
    {
        return $this->format('D M j H:i:s Y');
    }

    /**
     * Format date and time using strftime() format.
     *
     * @since Horde 3.1
     *
     * @return string  strftime() formatted date and time.
     */
    function strftime($format)
    {
        if (preg_match('/%[^' . $this->_supportedSpecs . ']/', $format)) {
            return strftime($format, $this->timestamp());
        } else {
            return $this->_strftime($format);
        }
    }

    /**
     * Format date and time using a limited set of the strftime() format.
     *
     * @return string  strftime() formatted date and time.
     */
    function _strftime($format)
    {
        if (preg_match('/%[bBpxX]/', $format)) {
            require_once 'Horde/NLS.php';
        }

        return preg_replace(
            array('/%b/e',
                  '/%B/e',
                  '/%C/e',
                  '/%d/e',
                  '/%D/e',
                  '/%e/e',
                  '/%H/e',
                  '/%I/e',
                  '/%m/e',
                  '/%M/e',
                  '/%n/',
                  '/%p/e',
                  '/%R/e',
                  '/%S/e',
                  '/%t/',
                  '/%T/e',
                  '/%x/e',
                  '/%X/e',
                  '/%y/e',
                  '/%Y/',
                  '/%%/'),
            array('$this->_strftime(NLS::getLangInfo(constant(\'ABMON_\' . (int)$this->month)))',
                  '$this->_strftime(NLS::getLangInfo(constant(\'MON_\' . (int)$this->month)))',
                  '(int)($this->year / 100)',
                  'sprintf(\'%02d\', $this->mday)',
                  '$this->_strftime(\'%m/%d/%y\')',
                  'sprintf(\'%2d\', $this->mday)',
                  'sprintf(\'%02d\', $this->hour)',
                  'sprintf(\'%02d\', $this->hour == 0 ? 12 : ($this->hour > 12 ? $this->hour - 12 : $this->hour))',
                  'sprintf(\'%02d\', $this->month)',
                  'sprintf(\'%02d\', $this->min)',
                  "\n",
                  '$this->_strftime(NLS::getLangInfo($this->hour < 12 ? AM_STR : PM_STR))',
                  '$this->_strftime(\'%H:%M\')',
                  'sprintf(\'%02d\', $this->sec)',
                  "\t",
                  '$this->_strftime(\'%H:%M:%S\')',
                  '$this->_strftime(NLS::getLangInfo(D_FMT))',
                  '$this->_strftime(NLS::getLangInfo(T_FMT))',
                  'substr(sprintf(\'%04d\', $this->year), -2)',
                  (int)$this->year,
                  '%'),
            $format);
    }

    /**
     * mktime() implementation that supports dates outside of 1970-2038,
     * from http://phplens.com/phpeverywhere/adodb_date_library.
     *
     * @TODO remove in Horde 4
     *
     * This does NOT work with pre-1970 daylight saving times.
     *
     * @static
     */
    function _mktime($hr, $min, $sec, $mon = false, $day = false,
                     $year = false, $is_dst = false, $is_gmt = false)
    {
        if ($mon === false) {
            return $is_gmt
                ? @gmmktime($hr, $min, $sec)
                : @mktime($hr, $min, $sec);
        }

        if ($year > 1901 && $year < 2038 &&
            ($year >= 1970 || version_compare(PHP_VERSION, '5.0.0', '>='))) {
            return $is_gmt
                ? @gmmktime($hr, $min, $sec, $mon, $day, $year)
                : @mktime($hr, $min, $sec, $mon, $day, $year);
        }

        $gmt_different = $is_gmt
            ? 0
            : (mktime(0, 0, 0, 1, 2, 1970, 0) - gmmktime(0, 0, 0, 1, 2, 1970, 0));

        $mon = intval($mon);
        $day = intval($day);
        $year = intval($year);

        if ($mon > 12) {
            $y = floor($mon / 12);
            $year += $y;
            $mon -= $y * 12;
        } elseif ($mon < 1) {
            $y = ceil((1 - $mon) / 12);
            $year -= $y;
            $mon += $y * 12;
        }

        $_day_power = 86400;
        $_hour_power = 3600;
        $_min_power = 60;

        $_month_table_normal = array('', 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31);
        $_month_table_leaf = array('', 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31);

        $_total_date = 0;
        if ($year >= 1970) {
            for ($a = 1970; $a <= $year; $a++) {
                $leaf = Horde_Date::isLeapYear($a);
                if ($leaf == true) {
                    $loop_table = $_month_table_leaf;
                    $_add_date = 366;
                } else {
                    $loop_table = $_month_table_normal;
                    $_add_date = 365;
                }
                if ($a < $year) {
                    $_total_date += $_add_date;
                } else {
                    for ($b = 1; $b < $mon; $b++) {
                        $_total_date += $loop_table[$b];
                    }
                }
            }

            return ($_total_date + $day - 1) * $_day_power + $hr * $_hour_power + $min * $_min_power + $sec + $gmt_different;
        }

        for ($a = 1969 ; $a >= $year; $a--) {
            $leaf = Horde_Date::isLeapYear($a);
            if ($leaf == true) {
                $loop_table = $_month_table_leaf;
                $_add_date = 366;
            } else {
                $loop_table = $_month_table_normal;
                $_add_date = 365;
            }
            if ($a > $year) {
                $_total_date += $_add_date;
            } else {
                for ($b = 12; $b > $mon; $b--) {
                    $_total_date += $loop_table[$b];
                }
            }
        }

        $_total_date += $loop_table[$mon] - $day;
        $_day_time = $hr * $_hour_power + $min * $_min_power + $sec;
        $_day_time = $_day_power - $_day_time;
        $ret = -($_total_date * $_day_power + $_day_time - $gmt_different);
        if ($ret < -12220185600) {
            // If earlier than 5 Oct 1582 - gregorian correction.
            return $ret + 10 * 86400;
        } elseif ($ret < -12219321600) {
            // If in limbo, reset to 15 Oct 1582.
            return -12219321600;
        } else {
            return $ret;
        }
    }

}
