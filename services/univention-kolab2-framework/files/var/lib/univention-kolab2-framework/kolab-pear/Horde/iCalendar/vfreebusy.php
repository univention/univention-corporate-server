<?php
/**
 * Class representing vFreebusys.
 *
 * $Horde: framework/iCalendar/iCalendar/vfreebusy.php,v 1.12 2004/01/01 15:14:48 jan Exp $
 *
 * Copyright 2003-2004 Mike Cochrane <mike@graftonhall.co.nz>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Mike Cochrane <mike@graftonhall.co.nz>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 3.0
 * @package Horde_iCalendar
 */
class Horde_iCalendar_vfreebusy extends Horde_iCalendar {

    var $_busyPeriods = array();
    var $_extraParams = array();

    function Horde_iCalendar_vfreebusy(&$container)
    {
        $this->_container = $container;
    }

    function getType()
    {
        return 'vFreebusy';
    }

    function parsevCalendar($data)
    {
        parent::parsevCalendar($data, 'VFREEBUSY');

        // do something with all the busy periods
        foreach ($this->_attributes as $key => $attribute) {
            if ($attribute['name'] == 'FREEBUSY') {
                foreach ($attribute['value'] as $value) {
                    if (array_key_exists('duration', $attribute['value'])) {
                       $this->addBusyPeriod('BUSY', $value['start'], null, $value['duration'], (array_key_exists('params', $attribute) ? $attribute['params'] : array()));
                    } else {
                       $this->addBusyPeriod('BUSY', $value['start'], $value['end'], null, (array_key_exists('params', $attribute) ? $attribute['params'] : array()));
                    }
                }
                unset($this->_attributes[$key]);
            }
        }
    }

    function exportvCalendar(&$container)
    {
        foreach ($this->_busyPeriods as $start => $end) {
            $periods = array(array('start' => $start, 'end' => $end));
            $this->setAttribute('FREEBUSY', $periods, (array_key_exists($start, $this->_extraParams) ? $this->_extraParams[$start] : array()));
        }

        $res =  parent::_exportvData('VFREEBUSY');

        foreach ($this->_attributes as $key => $attribute) {
            if ($attribute['name'] == 'FREEBUSY') {
                unset($this->_attributes[$key]);
            }
        }

        return $res;
    }

    /**
     * Get a display name for this object.
     */
    function getName()
    {
        $name = '';
        $method = $this->_container->getAttribute('METHOD');
        if (is_a($method, 'PEAR_Error') || $method == 'PUBLISH') {
            $attr = 'ORGANIZER';
        } else if ($method == 'REPLY') {
            $attr = 'ATTENDEE';
        }

        $name = $this->getAttribute($attr, true);
        if (array_key_exists('CN', $name[0])) {
            return $name[0]['CN'];
        }

        $name = $this->getAttribute($attr);
        if (is_a($name, 'PEAR_Error')) {
            return '';
        } else {
            $name = parse_url($name);
            return $name['path'];
        }
    }

    /**
     * Get the email address for this object.
     */
    function getEmail()
    {
        $name = '';
        $method = $this->_container->getAttribute('METHOD');
        if (is_a($method, 'PEAR_Error') || $method == 'PUBLISH') {
            $attr = 'ORGANIZER';
        } else if ($method == 'REPLY') {
            $attr = 'ATTENDEE';
        }

        $name = $this->getAttribute($attr);
        if (is_a($name, 'PEAR_Error')) {
            return '';
        } else {
            $name = parse_url($name);
            return $name['path'];
        }
    }

    function getBusyPeriods()
    {
        return $this->_busyPeriods;
    }

    function getExtraParams()
    {
        return $this->_extraParams;
    }

    /**
     * Return all the free periods of time in a given period.
     */
    function getFreePeriods($startStamp, $endStamp)
    {
        $this->simplify();
        $periods = array();

        // Check that we have data for some part of this period.
        if ($this->getEnd() < $startStamp || $this->getStart() > $endStamp) {
            return $periods;
        }

        // Locate the first time in the requested period we have data
        // for.
        $nextstart = max($startStamp, $this->getStart());

        // Check each busy period and add free periods in between.
        foreach ($this->_busyPeriods as $start => $end) {
            if ($start <= $endStamp && $end >= $nextstart) {
                $periods[$nextstart] = min($start, $endStamp);
                $nextstart = min($end, $endStamp);
            }
        }

        // If we didn't read the end of the requested period but still
        // have data then mark as free to the end of the period or
        // available data.
        if ($nextstart < $endStamp && $nextstart < $this->getEnd()) {
            $periods[$nextstart] = min($this->getEnd(), $endStamp);
        }

        return $periods;
    }

    /**
     * Add a busy period to the info.
     */
    function addBusyPeriod($type, $start, $end = null, $duration = null, $extra = array())
    {
        if ($type == "FREE") {
            // Make sure this period is not marked as busy.
            return false;
        }

        // Calculate the end time is duration was specified.
        $tempEnd = is_null($duration) ? $end : $start + $duration;

        // Make sure the period length is always positive.
        $end = max($start, $tempEnd);
        $start = min($start, $tempEnd);

        if (isset($this->_busyPeriods[$start])) {
            // Already a period starting at this time. Extend to the
            // length of the longest of the two.
            $this->_busyPeriods[$start] = max($end, $this->_busyPeriods[$start]);
        } else {
            // Add a new busy period.
            $this->_busyPeriods[$start] = $end;
        }
        $this->_extraParams[$start] = $extra;

        return true;
    }

    /**
     * Get the timestamp of the start of the time period this free
     * busy information covers.
     */
    function getStart()
    {
        if (!is_a($this->getAttribute('DTSTART'), 'PEAR_Error')) {
            return $this->getAttribute('DTSTART');
        } else if (count($this->_busyPeriods)) {
            return min(array_keys($this->_busyPeriods));
        } else {
            return false;
        }
    }

    /**
     * Get the timestamp of the end of the time period this free busy
     * information covers.
     */
    function getEnd()
    {
        if (!is_a($this->getAttribute('DTEND'), 'PEAR_Error')) {
            return $this->getAttribute('DTEND');
        } else if (count($this->_busyPeriods)) {
            return max(array_values($this->_busyPeriods));
        } else {
            return false;
        }
    }

    /**
     * Merge the busy periods of another VFreebusy into this one.
     */
    function merge($freebusy, $simplify = true)
    {
        if (!is_a($freebusy, 'Horde_iCalendar_vfreebusy')) {
            return false;
        }

        $extra = $freebusy->getExtraParams();
        foreach ($freebusy->getBusyPeriods() as $start => $end) {
            $this->addBusyPeriod('BUSY', $start, $end, null, (array_key_exists($start, $extra) ? $extra[$start] : array()));
        }
        if ($simplify) {
            $this->simplify();
        }
        return true;
    }

    /**
     * Remove all overlaps and simplify the busy periods array as much
     * as possible.
     */
    function simplify()
    {
        $checked = array();
        $checkedExtra = array();
        $checkedEmpty = true;
        foreach ($this->_busyPeriods as $start => $end) {
            if ($checkedEmpty) {
                $checked[$start] = $end;
                $checkedExtra[$start] = (array_key_exists($start, $this->_extraParams) ? $this->_extraParams[$start] : array());
                $checkedEmpty = false;
            } else {
                $added = false;
                foreach ($checked as $testStart => $testEnd) {
                    if ($start == $testStart) {
                        $checked[$testStart] = max($testEnd, $end);
                        $checkedExtra[$testStart] = (array_key_exists($testStart, $this->_extraParams) ? $this->_extraParams[$testStart] : array());
                        $added = true;
                    } else if ($end <= $testEnd && $end >= $testStart) {
                        unset($checked[$testStart]);
                        if (array_key_exists($testStart, $checkedExtra)) {
                            unset($checkedExtra[$testStart]);
                        }
                        $m = min($testStart, $start);
                        $checked[$m] = max($testEnd, $end);
                        $checkedExtra[$m] = (array_key_exists($start, $this->_extraParams) ? $this->_extraParams[$start] : array());
                        $added = true;
                    }
                    if ($added) {
                        break;
                    }
                }
                if (!$added) {
                    $checked[$start] = $end;
                    $checkedExtra[$start] = (array_key_exists($start, $this->_extraParams) ? $this->_extraParams[$start] : array());
                }
            }
        }
        ksort($checked, SORT_NUMERIC);
        ksort($checkedExtra, SORT_NUMERIC);
        $this->_busyPeriods = $checked;
        $this->_extraParams = $checkedExtra;
    }

}
