<?php
/**
 * This file contains the Nag_Recurrence class and according constants.
 *
 * $Horde: nag/lib/Recurrence.php,v 1.1.2.3 2009-01-06 15:25:05 jan Exp $
 *
 * Copyright 2007-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @since   Horde 3.2
 * @package Horde_Date
 */

/** Horde_Date */
require_once 'Horde/Date.php';

/** Date_Calc */
require_once 'Date/Calc.php';

/** No recurrence. */
define('NAG_RECUR_NONE', 0);
/** Recurs daily. */
define('NAG_RECUR_DAILY', 1);
/** Recurs weekly. */
define('NAG_RECUR_WEEKLY', 2);
/** Recurs monthly on the same date. */
define('NAG_RECUR_MONTHLY_DATE', 3);
/** Recurs monthly on the same week day. */
define('NAG_RECUR_MONTHLY_WEEKDAY', 4);
/** Recurs yearly on the same date. */
define('NAG_RECUR_YEARLY_DATE', 5);
/** Recurs yearly on the same day of the year. */
define('NAG_RECUR_YEARLY_DAY', 6);
/** Recurs yearly on the same week day. */
define('NAG_RECUR_YEARLY_WEEKDAY', 7);

/**
 * The Nag_Recurrence class implements algorithms for calculating
 * recurrences of events, including several recurrence types, intervals,
 * exceptions, and conversion from and to vCalendar and iCalendar recurrence
 * rules.
 *
 * All methods expecting dates as parameters accept all values that the
 * Horde_Date constructor accepts, i.e. a timestamp, another Horde_Date
 * object, an ISO time string or a hash.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @since   Horde 3.2
 * @package Horde_Date
 */
class Nag_Recurrence {

    /**
     * The start time of the event.
     *
     * @var Horde_Date
     */
    var $start;

    /**
     * The end date of the recurrence interval.
     *
     * @var Horde_Date
     */
    var $recurEnd = null;

    /**
     * The number of recurrences.
     *
     * @var integer
     */
    var $recurCount = null;

    /**
     * The type of recurrence this event follows. NAG_RECUR_* constant.
     *
     * @var integer
     */
    var $recurType = NAG_RECUR_NONE;

    /**
     * The length of time between recurrences. The time unit depends on the
     * recurrence type.
     *
     * @var integer
     */
    var $recurInterval = 1;

    /**
     * Any additional recurrence data.
     *
     * @var integer
     */
    var $recurData = null;

    /**
     * All the exceptions from recurrence for this event.
     *
     * @var array
     */
    var $exceptions = array();

    /**
     * All the dates this recurrence has been marked as completed.
     *
     * @var array
     */
    var $completions = array();

    /**
     * Constructor.
     *
     * @param Horde_Date $start  Start of the recurring event.
     */
    function Nag_Recurrence($start)
    {
        $this->start = new Horde_Date($start);
    }

    /**
     * Checks if this event recurs on a given day of the week.
     *
     * @param integer $dayMask  A mask consisting of HORDE_DATE_MASK_*
     *                          constants specifying the day(s) to check.
     *
     * @return boolean  True if this event recurs on the given day(s).
     */
    function recurOnDay($dayMask)
    {
        return ($this->recurData & $dayMask);
    }

    /**
     * Specifies the days this event recurs on.
     *
     * @param integer $dayMask  A mask consisting of HORDE_DATE_MASK_*
     *                          constants specifying the day(s) to recur on.
     */
    function setRecurOnDay($dayMask)
    {
        $this->recurData = $dayMask;
    }

    /**
     * Returns the days this event recurs on.
     *
     * @return integer  A mask consisting of HORDE_DATE_MASK_* constants
     *                  specifying the day(s) this event recurs on.
     */
    function getRecurOnDays()
    {
        return $this->recurData;
    }

    /**
     * Returns whether this event has a specific recurrence type.
     *
     * @param integer $recurrence  NAG_RECUR_* constant of the
     *                             recurrence type to check for.
     *
     * @return boolean  True if the event has the specified recurrence type.
     */
    function hasRecurType($recurrence)
    {
        return ($recurrence == $this->recurType);
    }

    /**
     * Sets a recurrence type for this event.
     *
     * @param integer $recurrence  A NAG_RECUR_* constant.
     */
    function setRecurType($recurrence)
    {
        $this->recurType = $recurrence;
    }

    /**
     * Returns recurrence type of this event.
     *
     * @return integer  A NAG_RECUR_* constant.
     */
    function getRecurType()
    {
        return $this->recurType;
    }

    /**
     * Returns a description of this event's recurring type.
     *
     * @return string  Human readable recurring type.
     */
    function getRecurName()
    {
        switch ($this->getRecurType()) {
            case NAG_RECUR_NONE: return _("No recurrence");
            case NAG_RECUR_DAILY: return _("Daily");
            case NAG_RECUR_WEEKLY: return _("Weekly");
            case NAG_RECUR_MONTHLY_DATE:
            case NAG_RECUR_MONTHLY_WEEKDAY: return _("Monthly");
            case NAG_RECUR_YEARLY_DATE:
            case NAG_RECUR_YEARLY_DAY:
            case NAG_RECUR_YEARLY_WEEKDAY: return _("Yearly");
        }
    }

    /**
     * Sets the length of time between recurrences of this event.
     *
     * @param integer $interval  The time between recurrences.
     */
    function setRecurInterval($interval)
    {
        if ($interval > 0) {
            $this->recurInterval = $interval;
        }
    }

    /**
     * Retrieves the length of time between recurrences of this event.
     *
     * @return integer  The number of seconds between recurrences.
     */
    function getRecurInterval()
    {
        return $this->recurInterval;
    }

    /**
     * Sets the number of recurrences of this event.
     *
     * @param integer $count  The number of recurrences.
     */
    function setRecurCount($count)
    {
        if ($count > 0) {
            $this->recurCount = (int)$count;
            // Recurrence counts and end dates are mutually exclusive.
            $this->recurEnd = null;
        } else {
            $this->recurCount = null;
        }
    }

    /**
     * Retrieves the number of recurrences of this event.
     *
     * @return integer  The number recurrences.
     */
    function getRecurCount()
    {
        return $this->recurCount;
    }

    /**
     * Returns whether this event has a recurrence with a fixed count.
     *
     * @return boolean  True if this recurrence has a fixed count.
     */
    function hasRecurCount()
    {
        return isset($this->recurCount);
    }

    /**
     * Sets the start date of the recurrence interval.
     *
     * @param Horde_Date $start  The recurrence start.
     */
    function setRecurStart($start)
    {
        $this->start = new Horde_Date($start);
    }

    /**
     * Retrieves the start date of the recurrence interval.
     *
     * @return Horde_Date  The recurrence start.
     */
    function getRecurStart()
    {
        return $this->start;
    }

    /**
     * Sets the end date of the recurrence interval.
     *
     * @param Horde_Date $end  The recurrence end.
     */
    function setRecurEnd($end)
    {
        if (!empty($end)) {
            // Recurrence counts and end dates are mutually exclusive.
            $this->recurCount = null;
        }
        $this->recurEnd = new Horde_Date($end);
    }

    /**
     * Retrieves the end date of the recurrence interval.
     *
     * @return Horde_Date  The recurrence end.
     */
    function getRecurEnd()
    {
        return $this->recurEnd;
    }

    /**
     * Returns whether this event has a recurrence end.
     *
     * @return boolean  True if this recurrence ends.
     */
    function hasRecurEnd()
    {
        return isset($this->recurEnd) && isset($this->recurEnd->year) &&
            $this->recurEnd->year != 9999;
    }

    /**
     * Finds the next recurrence of this event that's after $afterDate.
     *
     * @param Horde_Date $afterDate  Return events after this date.
     *
     * @return Horde_Date|boolean  The date of the next recurrence or false
     *                             if the event does not recur after
     *                             $afterDate.
     */
    function nextRecurrence($afterDate)
    {
        $after = new Horde_Date($afterDate);
        $after->correct();

        if ($this->start->compareDateTime($after) >= 0) {
            return new Horde_Date($this->start);
        }

        if ($this->recurInterval == 0) {
            return false;
        }

        switch ($this->getRecurType()) {
        case NAG_RECUR_DAILY:
            $diff = Date_Calc::dateDiff($this->start->mday, $this->start->month, $this->start->year, $after->mday, $after->month, $after->year);
            $recur = ceil($diff / $this->recurInterval);
            if ($this->recurCount && $recur >= $this->recurCount) {
                return false;
            }
            $recur *= $this->recurInterval;
            $next = new Horde_Date($this->start);
            list($next->mday, $next->month, $next->year) = explode('/', Date_Calc::daysToDate(Date_Calc::dateToDays($next->mday, $next->month, $next->year) + $recur, '%e/%m/%Y'));
            if ((!$this->hasRecurEnd() ||
                 $next->compareDateTime($this->recurEnd) <= 0) &&
                $next->compareDateTime($after) >= 0) {
                return new Horde_Date($next);
            }
            break;

        case NAG_RECUR_WEEKLY:
            if (empty($this->recurData)) {
                return false;
            }

            list($start_week->mday, $start_week->month, $start_week->year) = explode('/', Date_Calc::beginOfWeek($this->start->mday, $this->start->month, $this->start->year, '%e/%m/%Y'));
            $start_week->hour = $this->start->hour;
            $start_week->min = $this->start->min;
            $start_week->sec = $this->start->sec;
            list($after_week->mday, $after_week->month, $after_week->year) = explode('/', Date_Calc::beginOfWeek($after->mday, $after->month, $after->year, '%e/%m/%Y'));
            $after_week_end = new Horde_Date($after_week);
            $after_week_end->mday += 7;
            $after_week_end->correct();

            $diff = Date_Calc::dateDiff($start_week->mday, $start_week->month, $start_week->year,
                                        $after_week->mday, $after_week->month, $after_week->year);
            $recur = $diff + ($diff % ($this->recurInterval * 7));
            if ($this->recurCount &&
                ceil($recur / 7) / $this->recurInterval >= $this->recurCount) {
                return false;
            }
            $next = $start_week;
            list($next->mday, $next->month, $next->year) = explode('/', Date_Calc::daysToDate(Date_Calc::dateToDays($next->mday, $next->month, $next->year) + $recur, '%e/%m/%Y'));
            $next = new Horde_Date($next);
            while ($next->compareDateTime($after) < 0 &&
                   $next->compareDateTime($after_week_end) < 0) {
                ++$next->mday;
                $next->correct();
            }
            if (!$this->hasRecurEnd() ||
                $next->compareDateTime($this->recurEnd) <= 0) {
                if ($next->compareDateTime($after_week_end) >= 0) {
                    return $this->nextRecurrence($after_week_end);
                }
                while (!$this->recurOnDay((int)pow(2, $next->dayOfWeek())) &&
                       $next->compareDateTime($after_week_end) < 0) {
                    ++$next->mday;
                    $next->correct();
                }
                if (!$this->hasRecurEnd() ||
                    $next->compareDateTime($this->recurEnd) <= 0) {
                    if ($next->compareDateTime($after_week_end) >= 0) {
                        return $this->nextRecurrence($after_week_end);
                    } else {
                        return $next;
                    }
                }
            }
            break;

        case NAG_RECUR_MONTHLY_DATE:
            $start = new Horde_Date($this->start);
            if ($after->compareDateTime($start) < 0) {
                $after = $start;
            }

            // If we're starting past this month's recurrence of the event,
            // look in the next month on the day the event recurs.
            if ($after->mday > $start->mday) {
                ++$after->month;
                $after->mday = $start->mday;
                $after->correct();
            }

            // Adjust $start to be the first match.
            $offset = ($after->month - $start->month) + ($after->year - $start->year) * 12;
            $offset = floor(($offset + $this->recurInterval - 1) / $this->recurInterval) * $this->recurInterval;

            if ($this->recurCount &&
                ($offset / $this->recurInterval) >= $this->recurCount) {
                return false;
            }
            $start->month += $offset;
            $count = $offset / $this->recurInterval;

            do {
                if ($this->recurCount &&
                    $count++ >= $this->recurCount) {
                    return false;
                }

                // Don't correct for day overflow; we just skip February 30th,
                // for example.
                $start->correct(HORDE_DATE_MASK_MONTH);

                // Bail if we've gone past the end of recurrence.
                if ($this->hasRecurEnd() &&
                    $this->recurEnd->compareDateTime($start) < 0) {
                    return false;
                }
                if ($start->isValid()) {
                    return $start;
                }

                // If the interval is 12, and the date isn't valid, then we
                // need to see if February 29th is an option. If not, then the
                // event will _never_ recur, and we need to stop checking to
                // avoid an infinite loop.
                if ($this->recurInterval == 12 && ($start->month != 2 || $start->mday > 29)) {
                    return false;
                }

                // Add the recurrence interval.
                $start->month += $this->recurInterval;
            } while (true);

            break;

        case NAG_RECUR_MONTHLY_WEEKDAY:
            // Start with the start date of the event.
            $estart = new Horde_Date($this->start);

            // What day of the week, and week of the month, do we recur on?
            $nth = ceil($this->start->mday / 7);
            $weekday = $estart->dayOfWeek();

            // Adjust $estart to be the first candidate.
            $offset = ($after->month - $estart->month) + ($after->year - $estart->year) * 12;
            $offset = floor(($offset + $this->recurInterval - 1) / $this->recurInterval) * $this->recurInterval;

            // Adjust our working date until it's after $after.
            $estart->month += $offset - $this->recurInterval;

            $count = $offset / $this->recurInterval;
            do {
                if ($this->recurCount &&
                    $count++ >= $this->recurCount) {
                    return false;
                }

                $estart->month += $this->recurInterval;
                $estart->correct();

                $next = new Horde_Date($estart);
                $next->setNthWeekday($weekday, $nth);

                if ($next->compareDateTime($after) < 0) {
                    // We haven't made it past $after yet, try again.
                    continue;
                }
                if ($this->hasRecurEnd() &&
                    $next->compareDateTime($this->recurEnd) > 0) {
                    // We've gone past the end of recurrence; we can give up
                    // now.
                    return false;
                }

                // We have a candidate to return.
                break;
            } while (true);

            return $next;

        case NAG_RECUR_YEARLY_DATE:
            // Start with the start date of the event.
            $estart = new Horde_Date($this->start);

            if ($after->month > $estart->month ||
                ($after->month == $estart->month && $after->mday > $estart->mday)) {
                ++$after->year;
                $after->month = $estart->month;
                $after->mday = $estart->mday;
            }

            // Seperate case here for February 29th
            if ($estart->month == 2 && $estart->mday == 29) {
                while (!Horde_Date::isLeapYear($after->year)) {
                    ++$after->year;
                }
            }

            // Adjust $estart to be the first candidate.
            $offset = $after->year - $estart->year;
            if ($offset > 0) {
                $offset = floor(($offset + $this->recurInterval - 1) / $this->recurInterval) * $this->recurInterval;
                $estart->year += $offset;
            }

            // We've gone past the end of recurrence; give up.
            if ($this->recurCount &&
                $offset >= $this->recurCount) {
                return false;
            }
            if ($this->hasRecurEnd() &&
                $this->recurEnd->compareDateTime($estart) < 0) {
                return false;
            }

            return $estart;

        case NAG_RECUR_YEARLY_DAY:
            // Check count first.
            $dayofyear = $this->start->dayOfYear();
            $count = ($after->year - $this->start->year) / $this->recurInterval + 1;
            if ($this->recurCount &&
                ($count > $this->recurCount ||
                 ($count == $this->recurCount &&
                  $after->dayOfYear() > $dayofyear))) {
                return false;
            }

            // Start with a rough interval.
            $estart = new Horde_Date($this->start);
            $estart->year += floor($count - 1) * $this->recurInterval;

            // Now add the difference to the required day of year.
            $estart->mday += $dayofyear - $estart->dayOfYear();
            $estart->correct();

            // Add an interval if the estimation was wrong.
            if ($estart->compareDate($after) < 0) {
                $estart->year += $this->recurInterval;
                $estart->mday += $dayofyear - $estart->dayOfYear();
                $estart->correct();
            }

            // We've gone past the end of recurrence; give up.
            if ($this->hasRecurEnd() &&
                $this->recurEnd->compareDateTime($estart) < 0) {
                return false;
            }

            return $estart;

        case NAG_RECUR_YEARLY_WEEKDAY:
            // Start with the start date of the event.
            $estart = new Horde_Date($this->start);

            // What day of the week, and week of the month, do we recur on?
            $nth = ceil($this->start->mday / 7);
            $weekday = $estart->dayOfWeek();

            // Adjust $estart to be the first candidate.
            $offset = floor(($after->year - $estart->year + $this->recurInterval - 1) / $this->recurInterval) * $this->recurInterval;

            // Adjust our working date until it's after $after.
            $estart->year += $offset - $this->recurInterval;

            $count = $offset / $this->recurInterval;
            do {
                if ($this->recurCount &&
                    $count++ >= $this->recurCount) {
                    return false;
                }

                $estart->year += $this->recurInterval;
                $estart->correct();

                $next = new Horde_Date($estart);
                $next->setNthWeekday($weekday, $nth);

                if ($next->compareDateTime($after) < 0) {
                    // We haven't made it past $after yet, try again.
                    continue;
                }
                if ($this->hasRecurEnd() &&
                    $next->compareDateTime($this->recurEnd) > 0) {
                    // We've gone past the end of recurrence; we can give up
                    // now.
                    return false;
                }

                // We have a candidate to return.
                break;
            } while (true);

            return $next;
        }

        // We didn't find anything, the recurType was bad, or something else
        // went wrong - return false.
        return false;
    }

    /**
     * Returns whether this event has any date that matches the recurrence
     * rules and is not an exception.
     *
     * @return boolean  True if an active recurrence exists.
     */
    function hasActiveRecurrence()
    {
        if (!$this->hasRecurEnd()) {
            return true;
        }

        $next = $this->nextRecurrence(new Horde_Date($this->start));
        while (is_object($next)) {
            if (!$this->hasException($next->year, $next->month, $next->mday) &&
                !$this->hasCompletion($next->year, $next->month, $next->mday)) {
                return true;
            }

            $next = $this->nextRecurrence(array('year' => $next->year,
                                                'month' => $next->month,
                                                'mday' => $next->mday + 1,
                                                'hour' => $next->hour,
                                                'min' => $next->min,
                                                'sec' => $next->sec));
        }

        return false;
    }

    /**
     * Returns the next active recurrence.
     *
     * @param Horde_Date $afterDate  Return events after this date.
     *
     * @return Horde_Date|boolean The date of the next active
     *                             recurrence or false if the event
     *                             has no active recurrence after
     *                             $afterDate.
     */
    function nextActiveRecurrence($afterDate)
    {
        $next = $this->nextRecurrence($afterDate);
        while (is_object($next)) {
            if (!$this->hasException($next->year, $next->month, $next->mday) &&
                !$this->hasCompletion($next->year, $next->month, $next->mday)) {
                return $next;
            }
            $next->mday++;
            $next = $this->nextRecurrence($next);
        }

        return false;
    }

    /**
     * Adds an exception to a recurring event.
     *
     * @param integer $year   The year of the execption.
     * @param integer $month  The month of the execption.
     * @param integer $mday   The day of the month of the exception.
     */
    function addException($year, $month, $mday)
    {
        $this->exceptions[] = sprintf('%04d%02d%02d', $year, $month, $mday);
    }

    /**
     * Deletes an exception from a recurring event.
     *
     * @param integer $year   The year of the execption.
     * @param integer $month  The month of the execption.
     * @param integer $mday   The day of the month of the exception.
     */
    function deleteException($year, $month, $mday)
    {
        $key = array_search(sprintf('%04d%02d%02d', $year, $month, $mday), $this->exceptions);
        if ($key !== false) {
            unset($this->exceptions[$key]);
        }
    }

    /**
     * Checks if an exception exists for a given reccurence of an event.
     *
     * @param integer $year   The year of the reucrance.
     * @param integer $month  The month of the reucrance.
     * @param integer $mday   The day of the month of the reucrance.
     *
     * @return boolean  True if an exception exists for the given date.
     */
    function hasException($year, $month, $mday)
    {
        return in_array(sprintf('%04d%02d%02d', $year, $month, $mday),
                        $this->getExceptions());
    }

    /**
     * Retrieves all the exceptions for this event.
     *
     * @return array  Array containing the dates of all the exceptions in
     *                YYYYMMDD form.
     */
    function getExceptions()
    {
        return $this->exceptions;
    }

    /**
     * Adds a completion to a recurring event.
     *
     * @param integer $year   The year of the execption.
     * @param integer $month  The month of the execption.
     * @param integer $mday   The day of the month of the completion.
     */
    function addCompletion($year, $month, $mday)
    {
        $this->completions[] = sprintf('%04d%02d%02d', $year, $month, $mday);
    }

    /**
     * Deletes a completion from a recurring event.
     *
     * @param integer $year   The year of the execption.
     * @param integer $month  The month of the execption.
     * @param integer $mday   The day of the month of the completion.
     */
    function deleteCompletion($year, $month, $mday)
    {
        $key = array_search(sprintf('%04d%02d%02d', $year, $month, $mday), $this->completions);
        if ($key !== false) {
            unset($this->completions[$key]);
        }
    }

    /**
     * Checks if a completion exists for a given reccurence of an event.
     *
     * @param integer $year   The year of the reucrance.
     * @param integer $month  The month of the recurrance.
     * @param integer $mday   The day of the month of the recurrance.
     *
     * @return boolean  True if a completion exists for the given date.
     */
    function hasCompletion($year, $month, $mday)
    {
        return in_array(sprintf('%04d%02d%02d', $year, $month, $mday),
                        $this->getCompletions());
    }

    /**
     * Retrieves all the completions for this event.
     *
     * @return array  Array containing the dates of all the completions in
     *                YYYYMMDD form.
     */
    function getCompletions()
    {
        return $this->completions;
    }

    /**
     * Parses a vCalendar 1.0 recurrence rule.
     *
     * @link http://www.imc.org/pdi/vcal-10.txt
     * @link http://www.shuchow.com/vCalAddendum.html
     *
     * @param string $rrule  A vCalendar 1.0 conform RRULE value.
     */
    function fromRRule10($rrule)
    {
        if (!$rrule) {
            return;
        }

        if (!preg_match('/([A-Z]+)(\d+)?(.*)/', $rrule, $matches)) {
            // No recurrence data - event does not recur.
            $this->setRecurType(NAG_RECUR_NONE);
        }

        // Always default the recurInterval to 1.
        $this->setRecurInterval(!empty($matches[2]) ? $matches[2] : 1);

        $remainder = trim($matches[3]);

        switch ($matches[1]) {
        case 'D':
            $this->setRecurType(NAG_RECUR_DAILY);
            break;

        case 'W':
            $this->setRecurType(NAG_RECUR_WEEKLY);
            if (!empty($remainder)) {
                $maskdays = array('SU' => HORDE_DATE_MASK_SUNDAY,
                                  'MO' => HORDE_DATE_MASK_MONDAY,
                                  'TU' => HORDE_DATE_MASK_TUESDAY,
                                  'WE' => HORDE_DATE_MASK_WEDNESDAY,
                                  'TH' => HORDE_DATE_MASK_THURSDAY,
                                  'FR' => HORDE_DATE_MASK_FRIDAY,
                                  'SA' => HORDE_DATE_MASK_SATURDAY);
                $mask = 0;
                while (preg_match('/^ ?[A-Z]{2} ?/', $remainder, $matches)) {
                    $day = trim($matches[0]);
                    $remainder = substr($remainder, strlen($matches[0]));
                    $mask |= $maskdays[$day];
                }
                $this->setRecurOnDay($mask);
            } else {
                // Recur on the day of the week of the original recurrence.
                $maskdays = array(HORDE_DATE_SUNDAY => HORDE_DATE_MASK_SUNDAY,
                                  HORDE_DATE_MONDAY => HORDE_DATE_MASK_MONDAY,
                                  HORDE_DATE_TUESDAY => HORDE_DATE_MASK_TUESDAY,
                                  HORDE_DATE_WEDNESDAY => HORDE_DATE_MASK_WEDNESDAY,
                                  HORDE_DATE_THURSDAY => HORDE_DATE_MASK_THURSDAY,
                                  HORDE_DATE_FRIDAY => HORDE_DATE_MASK_FRIDAY,
                                  HORDE_DATE_SATURDAY => HORDE_DATE_MASK_SATURDAY);
                $this->setRecurOnDay($maskdays[$this->start->dayOfWeek()]);
            }
            break;

        case 'MP':
            $this->setRecurType(NAG_RECUR_MONTHLY_WEEKDAY);
            break;

        case 'MD':
            $this->setRecurType(NAG_RECUR_MONTHLY_DATE);
            break;

        case 'YM':
            $this->setRecurType(NAG_RECUR_YEARLY_DATE);
            break;

        case 'YD':
            $this->setRecurType(NAG_RECUR_YEARLY_DAY);
            break;
        }

        // We don't support modifiers at the moment, strip them.
        while ($remainder && !preg_match('/^(#\d+|\d{8})($| |T\d{6})/', $remainder)) {
               $remainder = substr($remainder, 1);
        }
        if (!empty($remainder)) {
            if (strpos($remainder, '#') !== false) {
                $this->setRecurCount(substr($remainder, 1));
            } else {
                list($year, $month, $mday) = sscanf($remainder, '%04d%02d%02d');
                $this->setRecurEnd(new Horde_Date(array('year' => $year,
                                                        'month' => $month,
                                                        'mday' => $mday)));
            }
        }
    }

    /**
     * Creates a vCalendar 1.0 recurrence rule.
     *
     * @link http://www.imc.org/pdi/vcal-10.txt
     * @link http://www.shuchow.com/vCalAddendum.html
     *
     * @param Horde_iCalendar $calendar  A Horde_iCalendar object instance.
     *
     * @return string  A vCalendar 1.0 conform RRULE value.
     */
    function toRRule10($calendar)
    {
        switch ($this->recurType) {
        case NAG_RECUR_NONE:
            return '';

        case NAG_RECUR_DAILY:
            $rrule = 'D' . $this->recurInterval;
            break;

        case NAG_RECUR_WEEKLY:
            $rrule = 'W' . $this->recurInterval;
            $vcaldays = array('SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA');

            for ($i = 0; $i <= 7 ; ++$i) {
                if ($this->recurOnDay(pow(2, $i))) {
                    $rrule .= ' ' . $vcaldays[$i];
                }
            }
            break;

        case NAG_RECUR_MONTHLY_DATE:
            $rrule = 'MD' . $this->recurInterval . ' ' . trim($this->start->mday);
            break;

        case NAG_RECUR_MONTHLY_WEEKDAY:
            $next_week = new Horde_Date($this->start);
            $next_week->mday += 7;
            $next_week->correct();

            if ($this->start->month != $next_week->month) {
                $p = 5;
            } else {
                $p = (int)($this->start->mday / 7);
                if (($this->start->mday % 7) > 0) {
                    $p++;
                }
            }

            $vcaldays = array('SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA');
            $rrule = 'MP' . $this->recurInterval . ' ' . $p . '+ ' . $vcaldays[$this->start->dayOfWeek()];
            break;

        case NAG_RECUR_YEARLY_DATE:
            $rrule = 'YM' . $this->recurInterval . ' ' . trim($this->start->month);
            break;

        case NAG_RECUR_YEARLY_DAY:
            $rrule = 'YD' . $this->recurInterval . ' ' . $this->start->dayOfYear();
            break;

        default:
            return '';
        }

        return $this->hasRecurEnd() ?
            $rrule . ' ' . $calendar->_exportDate($this->recurEnd) :
            $rrule . ' #' . (int)$this->getRecurCount();
    }

    /**
     * Parses an iCalendar 2.0 recurrence rule.
     *
     * @link http://rfc.net/rfc2445.html#s4.8.5
     * @link http://www.shuchow.com/vCalAddendum.html
     *
     * @param string $rrule  An iCalendar 2.0 conform RRULE value.
     */
    function fromRRule20($rrule)
    {
        // Parse the recurrence rule into keys and values.
        $rdata = array();
        $parts = explode(';', $rrule);
        foreach ($parts as $part) {
            list($key, $value) = explode('=', $part, 2);
            $rdata[String::upper($key)] = $value;
        }

        if (isset($rdata['FREQ'])) {
            // Always default the recurInterval to 1.
            $this->setRecurInterval(isset($rdata['INTERVAL']) ? $rdata['INTERVAL'] : 1);

            switch (String::upper($rdata['FREQ'])) {
            case 'DAILY':
                $this->setRecurType(NAG_RECUR_DAILY);
                break;

            case 'WEEKLY':
                $this->setRecurType(NAG_RECUR_WEEKLY);
                if (isset($rdata['BYDAY'])) {
                    $maskdays = array('SU' => HORDE_DATE_MASK_SUNDAY,
                                      'MO' => HORDE_DATE_MASK_MONDAY,
                                      'TU' => HORDE_DATE_MASK_TUESDAY,
                                      'WE' => HORDE_DATE_MASK_WEDNESDAY,
                                      'TH' => HORDE_DATE_MASK_THURSDAY,
                                      'FR' => HORDE_DATE_MASK_FRIDAY,
                                      'SA' => HORDE_DATE_MASK_SATURDAY);
                    $days = explode(',', $rdata['BYDAY']);
                    $mask = 0;
                    foreach ($days as $day) {
                        $mask |= $maskdays[$day];
                    }
                    $this->setRecurOnDay($mask);
                } else {
                    // Recur on the day of the week of the original
                    // recurrence.
                    $maskdays = array(
                        HORDE_DATE_SUNDAY => HORDE_DATE_MASK_SUNDAY,
                        HORDE_DATE_MONDAY => HORDE_DATE_MASK_MONDAY,
                        HORDE_DATE_TUESDAY => HORDE_DATE_MASK_TUESDAY,
                        HORDE_DATE_WEDNESDAY => HORDE_DATE_MASK_WEDNESDAY,
                        HORDE_DATE_THURSDAY => HORDE_DATE_MASK_THURSDAY,
                        HORDE_DATE_FRIDAY => HORDE_DATE_MASK_FRIDAY,
                        HORDE_DATE_SATURDAY => HORDE_DATE_MASK_SATURDAY);
                    $this->setRecurOnDay($maskdays[$this->start->dayOfWeek()]);
                }
                break;

            case 'MONTHLY':
                if (isset($rdata['BYDAY'])) {
                    $this->setRecurType(NAG_RECUR_MONTHLY_WEEKDAY);
                } else {
                    $this->setRecurType(NAG_RECUR_MONTHLY_DATE);
                }
                break;

            case 'YEARLY':
                if (isset($rdata['BYYEARDAY'])) {
                    $this->setRecurType(NAG_RECUR_YEARLY_DAY);
                } elseif (isset($rdata['BYDAY'])) {
                    $this->setRecurType(NAG_RECUR_YEARLY_WEEKDAY);
                } else {
                    $this->setRecurType(NAG_RECUR_YEARLY_DATE);
                }
                break;
            }

            if (isset($rdata['UNTIL'])) {
                list($year, $month, $mday) = sscanf($rdata['UNTIL'],
                                                    '%04d%02d%02d');
                $this->setRecurEnd(new Horde_Date(array('year' => $year,
                                                        'month' => $month,
                                                        'mday' => $mday)));
            }
            if (isset($rdata['COUNT'])) {
                $this->setRecurCount($rdata['COUNT']);
            }
        } else {
            // No recurrence data - event does not recur.
            $this->setRecurType(NAG_RECUR_NONE);
        }
    }

    /**
     * Creates an iCalendar 2.0 recurrence rule.
     *
     * @link http://rfc.net/rfc2445.html#s4.8.5
     * @link http://www.shuchow.com/vCalAddendum.html
     *
     * @param Horde_iCalendar $calendar  A Horde_iCalendar object instance.
     *
     * @return string  An iCalendar 2.0 conform RRULE value.
     */
    function toRRule20($calendar)
    {
        switch ($this->recurType) {
        case NAG_RECUR_NONE:
            return '';

        case NAG_RECUR_DAILY:
            $rrule = 'FREQ=DAILY;INTERVAL='  . $this->recurInterval;
            break;

        case NAG_RECUR_WEEKLY:
            $rrule = 'FREQ=WEEKLY;INTERVAL=' . $this->recurInterval . ';BYDAY=';
            $vcaldays = array('SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA');

            for ($i = $flag = 0; $i <= 7 ; ++$i) {
                if ($this->recurOnDay(pow(2, $i))) {
                    if ($flag) {
                        $rrule .= ',';
                    }
                    $rrule .= $vcaldays[$i];
                    $flag = true;
                }
            }
            break;

        case NAG_RECUR_MONTHLY_DATE:
            $rrule = 'FREQ=MONTHLY;INTERVAL=' . $this->recurInterval;
            break;

        case NAG_RECUR_MONTHLY_WEEKDAY:
            $next_week = new Horde_Date($this->start);
            $next_week->mday += 7;
            $next_week->correct();
            if ($this->start->month != $next_week->month) {
                $p = 5;
            } else {
                $p = (int)($this->start->mday / 7);
                if (($this->start->mday % 7) > 0) {
                    $p++;
                }
            }
            $vcaldays = array('SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA');
            $rrule = 'FREQ=MONTHLY;INTERVAL=' . $this->recurInterval
                . ';BYDAY=' . $p . $vcaldays[$this->start->dayOfWeek()];
            break;

        case NAG_RECUR_YEARLY_DATE:
            $rrule = 'FREQ=YEARLY;INTERVAL=' . $this->recurInterval;
            break;

        case NAG_RECUR_YEARLY_DAY:
            $rrule = 'FREQ=YEARLY;INTERVAL=' . $this->recurInterval
                . ';BYYEARDAY=' . $this->start->dayOfYear();
            break;

        case NAG_RECUR_YEARLY_WEEKDAY:
            $vcaldays = array('SU', 'MO', 'TU', 'WE', 'TH', 'FR', 'SA');
            $weekday = new Horde_Date(array('month' => $this->start->month,
                                            'mday' => 1,
                                            'year' => $this->start->year));
            $rrule = 'FREQ=YEARLY;INTERVAL=' . $this->recurInterval
                . ';BYDAY='
                . ($this->start->weekOfYear() - $weekday->weekOfYear() + 1)
                . $vcaldays[$this->start->dayOfWeek()]
                . ';BYMONTH=' . $this->start->month;
            break;
        }

        if ($this->hasRecurEnd()) {
            $rrule .= ';UNTIL=' . $calendar->_exportDate($this->recurEnd);
        }
        if ($count = $this->getRecurCount()) {
            $rrule .= ';COUNT=' . $count;
        }
        return $rrule;
    }

    /**
     * Parses the recurrence data from a hash.
     *
     * @param array $hash  The hash to convert.
     *
     * @return boolean  True if the hash seemed valid, false otherwise.
     */
    function fromHash($hash)
    {
        if (!isset($hash['interval']) || !isset($hash['interval']) ||
            !isset($hash['range-type'])) {
            $this->setRecurType(NAG_RECUR_NONE);
            return false;
        }

        $this->setRecurInterval((int) $hash['interval']);

        $parse_day = false;
        $set_daymask = false;
        $update_month = false;
        $update_daynumber = false;
        $update_weekday = false;
        $nth_weekday = -1;

        switch ($hash['cycle']) {
        case 'daily':
            $this->setRecurType(NAG_RECUR_DAILY);
            break;

        case 'weekly':
            $this->setRecurType(NAG_RECUR_WEEKLY);
            $parse_day = true;
            $set_daymask = true;
            break;

        case 'monthly':
            if (!isset($hash['daynumber'])) {
                $this->setRecurType(NAG_RECUR_NONE);
                return false;
            }

            switch ($hash['type']) {
            case 'daynumber':
                $this->setRecurType(NAG_RECUR_MONTHLY_DATE);
                $update_daynumber = true;
                break;

            case 'weekday':
                $this->setRecurType(NAG_RECUR_MONTHLY_WEEKDAY);
                $nth_weekday = (int) $hash['daynumber'];
                $hash['daynumber'] = 1;
                $parse_day = true;
                $update_daynumber = true;
                $update_weekday = true;
                break;
            }
            break;

        case 'yearly':
            if (!isset($hash['type'])) {
                $this->setRecurType(NAG_RECUR_NONE);
                return false;
            }

            switch ($hash['type']) {
            case 'monthday':
                $this->setRecurType(NAG_RECUR_YEARLY_DATE);
                $update_month = true;
                $update_daynumber = true;
                break;

            case 'yearday':
                if (!isset($hash['month'])) {
                    $this->setRecurType(NAG_RECUR_NONE);
                    return false;
                }

                $this->setRecurType(NAG_RECUR_YEARLY_DAY);
                // Start counting days in January.
                $hash['month'] = 'january';
                $update_month = true;
                $update_daynumber = true;
                break;

            case 'weekday':
                if (!isset($hash['daynumber'])) {
                    $this->setRecurType(NAG_RECUR_NONE);
                    return false;
                }

                $this->setRecurType(NAG_RECUR_YEARLY_WEEKDAY);
                $nth_weekday = (int) $hash['daynumber'];
                $hash['daynumber'] = 1;
                $parse_day = true;
                $update_month = true;
                $update_daynumber = true;
                $update_weekday = true;
                break;
            }
        }

        switch ($hash['range-type']) {
        case 'number':
            if (!isset($hash['range'])) {
                $this->setRecurType(NAG_RECUR_NONE);
                return false;
            }

            $this->setRecurCount((int) $hash['range']);
            break;

        case 'date':
            $recur_end = new Horde_Date($hash['range']);
            $recur_end->hour = 23;
            $recur_end->min = 59;
            $recur_end->sec = 59;
            $this->setRecurEnd($recur_end);
            break;
        }

        // Need to parse <day>?
        $last_found_day = -1;
        if ($parse_day) {
            if (!isset($hash['day'])) {
                $this->setRecurType(NAG_RECUR_NONE);
                return false;
            }

            $mask = 0;
            $bits = array(
                'monday' => HORDE_DATE_MASK_MONDAY,
                'tuesday' => HORDE_DATE_MASK_TUESDAY,
                'wednesday' => HORDE_DATE_MASK_WEDNESDAY,
                'thursday' => HORDE_DATE_MASK_THURSDAY,
                'friday' => HORDE_DATE_MASK_FRIDAY,
                'saturday' => HORDE_DATE_MASK_SATURDAY,
                'sunday' => HORDE_DATE_MASK_SUNDAY,
            );
            $days = array(
                'monday' => HORDE_DATE_MONDAY,
                'tuesday' => HORDE_DATE_TUESDAY,
                'wednesday' => HORDE_DATE_WEDNESDAY,
                'thursday' => HORDE_DATE_THURSDAY,
                'friday' => HORDE_DATE_FRIDAY,
                'saturday' => HORDE_DATE_SATURDAY,
                'sunday' => HORDE_DATE_SUNDAY,
            );

            foreach ($hash['day'] as $day) {
                // Validity check.
                if (empty($day) || !isset($bits[$day])) {
                    continue;
                }

                $mask |= $bits[$day];
                $last_found_day = $days[$day];
            }

            if ($set_daymask) {
                $this->setRecurOnDay($mask);
            }
        }

        if ($update_month || $update_daynumber || $update_weekday) {
            if ($update_month) {
                $month2number = array(
                    'january'   => 1,
                    'february'  => 2,
                    'march'     => 3,
                    'april'     => 4,
                    'may'       => 5,
                    'june'      => 6,
                    'july'      => 7,
                    'august'    => 8,
                    'september' => 9,
                    'october'   => 10,
                    'november'  => 11,
                    'december'  => 12,
                );

                if (isset($month2number[$hash['month']])) {
                    $this->start->month = $month2number[$hash['month']];
                }
            }

            if ($update_daynumber) {
                if (!isset($hash['daynumber'])) {
                    $this->setRecurType(NAG_RECUR_NONE);
                    return false;
                }

                $this->start->mday = $hash['daynumber'];
            }

            if ($update_weekday) {
                $this->start->setNthWeekday($last_found_day, $nth_weekday);
            }

            $this->start->correct();
        }

        // Exceptions.
        if (isset($hash['exceptions'])) {
            $this->exceptions = $hash['exceptions'];
        }

        if (isset($hash['completions'])) {
            $this->completions = $hash['completions'];
        }

        return true;
    }

    /**
     * Export this object into a hash.
     *
     * @return array  The recurrence hash.
     */
    function toHash()
    {
        if ($this->getRecurType() == NAG_RECUR_NONE) {
            return array();
        }

        $day2number = array(
            0 => 'sunday',
            1 => 'monday',
            2 => 'tuesday',
            3 => 'wednesday',
            4 => 'thursday',
            5 => 'friday',
            6 => 'saturday'
        );
        $month2number = array(
            1 => 'january',
            2 => 'february',
            3 => 'march',
            4 => 'april',
            5 => 'may',
            6 => 'june',
            7 => 'july',
            8 => 'august',
            9 => 'september',
            10 => 'october',
            11 => 'november',
            12 => 'december'
        );

        $hash = array('interval' => $this->getRecurInterval());
        $start = $this->getRecurStart();

        switch ($this->getRecurType()) {
        case NAG_RECUR_DAILY:
            $hash['cycle'] = 'daily';
            break;

        case NAG_RECUR_WEEKLY:
            $hash['cycle'] = 'weekly';
            $bits = array(
                'monday' => HORDE_DATE_MASK_MONDAY,
                'tuesday' => HORDE_DATE_MASK_TUESDAY,
                'wednesday' => HORDE_DATE_MASK_WEDNESDAY,
                'thursday' => HORDE_DATE_MASK_THURSDAY,
                'friday' => HORDE_DATE_MASK_FRIDAY,
                'saturday' => HORDE_DATE_MASK_SATURDAY,
                'sunday' => HORDE_DATE_MASK_SUNDAY,
            );
            $days = array();
            foreach($bits as $name => $bit) {
                if ($this->recurOnDay($bit)) {
                    $days[] = $name;
                }
            }
            $hash['day'] = $days;
            break;

        case NAG_RECUR_MONTHLY_DATE:
            $hash['cycle'] = 'monthly';
            $hash['type'] = 'daynumber';
            $hash['daynumber'] = $start->mday;
            break;

        case NAG_RECUR_MONTHLY_WEEKDAY:
            $hash['cycle'] = 'monthly';
            $hash['type'] = 'weekday';
            $hash['daynumber'] = $start->weekOfMonth();
            $hash['day'] = array ($day2number[$start->dayOfWeek()]);
            break;

        case NAG_RECUR_YEARLY_DATE:
            $hash['cycle'] = 'yearly';
            $hash['type'] = 'monthday';
            $hash['daynumber'] = $start->mday;
            $hash['month'] = $month2number[$start->month];
            break;

        case NAG_RECUR_YEARLY_DAY:
            $hash['cycle'] = 'yearly';
            $hash['type'] = 'yearday';
            $hash['daynumber'] = $start->dayOfYear();
            break;

        case NAG_RECUR_YEARLY_WEEKDAY:
            $hash['cycle'] = 'yearly';
            $hash['type'] = 'weekday';
            $hash['daynumber'] = $start->weekOfMonth();
            $hash['day'] = array ($day2number[$start->dayOfWeek()]);
            $hash['month'] = $month2number[$start->month];
        }

        if ($this->hasRecurCount()) {
            $hash['range-type'] = 'number';
            $hash['range'] = $this->getRecurCount();
        } elseif ($this->hasRecurEnd()) {
            $date = $this->getRecurEnd();
            $hash['range-type'] = 'date';
            $hash['range'] = $date->datestamp();
        } else {
            $hash['range-type'] = 'none';
            $hash['range'] = '';
        }

        // Recurrence exceptions
        $hash['exceptions'] = $this->exceptions;
        $hash['completions'] = $this->completions;

        return $hash;
    }

}
