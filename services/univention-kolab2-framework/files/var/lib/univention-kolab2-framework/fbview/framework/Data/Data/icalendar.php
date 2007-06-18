<?php

/** We rely on the Horde_Data_imc:: abstract class. */
require_once dirname(__FILE__) . '/imc.php';

/**
 * This is iCalendar (vCalendar).
 *
 * $Horde: framework/Data/Data/icalendar.php,v 1.29 2004/03/19 14:50:46 chuck Exp $
 *
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Data
 * @since   Horde 3.0
 */
class Horde_Data_icalendar extends Horde_Data_imc {

    var $_params = array();

    function _build($data, &$i, $return = false)
    {
        // We shouldn't call this unless we're about to begin an
        // object of some sort.
        $uname = String::upper($data[$i]['name']);
        if ($uname != 'BEGIN') {
            return PEAR::raiseError(sprintf(_("Import Error: Expecting BEGIN on line %d."), $i));
        }

        $object = array('type' => String::upper($data[$i]['values'][0]),
                        'objects' => array(),
                        'params' => array());
        $i++;

        while (String::upper($data[$i]['name']) != 'END') {
            if (String::upper($data[$i]['name']) == 'BEGIN') {
                $object['objects'][] = $this->_build($data, $i, true);
            } else {
                $object['params'][String::upper($data[$i]['name'])] = array('params' => $data[$i]['params'],
                                                                            'values' => $data[$i]['values']);
            }
            $i++;
        }

        if (String::upper($data[$i]['values'][0]) != $object['type']) {
            return PEAR::raiseError(sprintf(_("Import Error: Mismatch; expecting END:%s on line %d"), $object['type'], $i));
        }

        if ($return) {
            return $object;
        } else {
            if (String::upper($object['type']) == 'VCALENDAR') {
                $this->_objects = $object['objects'];
                $this->_params = $object['params'];
            } else {
                $this->_objects[] = $object;
            }
        }
    }

    function getValues($attribute, $event = 0)
    {
        $values = array();
        $attribute = String::upper($attribute);

        if (isset($this->_objects[$event]['params'][$attribute])) {
            $count = count($this->_objects[$event]['params'][$attribute]['values']);
            for ($i = 0; $i < $count; $i++) {
                $values[$i] = $this->read($this->_objects[$event]['params'][$attribute], $i);
            }
        }
        return (count($values) > 0) ? $values : null;
    }

    function getAttributes($event = 0)
    {
        return array_keys($this->_objects[$event]['params']);
    }

    /**
     * Builds an iCalendar file from a given data structure and returns it as
     * a string.
     *
     * @access public
     *
     * @param array $data     A two-dimensional array containing the data set.
     * @param string $method  (optional) The iTip method to use.
     *
     * @return string      The iCalendar data.
     */
    function exportData($data, $method = 'REQUEST')
    {
        global $prefs;

        $DST = date('I');
        $TZNAME = date('T');
        $TZID = $prefs->getValue('timezone');
        $TZOFFSET = date('O');

        // These can be used later in a VTIMEZONE object:
        // $TZOffsetFrom = ($DST) ? $TZOFFSET - 100 : $TZOFFSET;
        // $TZOffsetTo   = ($DST) ? $TZOFFSET : $TZOFFSET - 100;

        $file = implode($this->_newline, array('BEGIN:VCALENDAR',
                                               'VERSION:2.0',
                                               'PRODID:-//Horde.org//Kronolith Generated',
                                               'METHOD:' . $method)) . $this->_newline;
        foreach ($data as $row) {
            $file .= 'BEGIN:VEVENT' . $this->_newline;
            foreach ($row as $key => $val) {
                if (!empty($val)) {
                    // Basic encoding. Newlines for now; more work
                    // here to make this RFC-compliant.
                    $file .= $key . ':' .  $this->_quoteAndFold($val);
                }
            }
            $file .= 'END:VEVENT' . $this->_newline;
        }
        $file .= 'END:VCALENDAR' . $this->_newline;

        return $file;
    }

    /**
     * Builds an iCalendar file from a given data structure and
     * triggers its download.  It DOES NOT exit the current script but
     * only outputs the correct headers and data.
     *
     * @access public
     * @param string $filename   The name of the file to be downloaded.
     * @param array $data        A two-dimensional array containing the data set.
     */
    function exportFile($filename, $data)
    {
        $export = $this->exportData($data);
        $GLOBALS['browser']->downloadHeaders($filename, 'text/calendar', false, strlen($export));
        echo $export;
    }

    function toHash($i = 0)
    {
        $hash = array();
        if (($title = $this->getValues('SUMMARY', $i)) !== null) {
            $hash['title'] = implode("\n", $title);
        }
        if (($desc = $this->getValues('DESCRIPTION', $i)) !== null) {
            $hash['description'] = implode("\n", $desc);
        }
        if (($location = $this->getValues('LOCATION', $i)) !== null) {
            $hash['location'] = implode("\n", $location);
        }

        if (($start = $this->getValues('DTSTART', $i)) !== null &&
            count($start) == 1) {
            $start = $this->mapDate($start[0]);
            $hash['start_date'] = $start['year'] . '-' . $start['month'] . '-' . $start['mday'];
            $hash['start_time'] = $start['hour'] . ':' . $start['min'] . ':' . $start['sec'];
        }

        if (($start = $this->getValues('DURATION', $i)) != null &&
            count($start) == 1) {
            preg_match('/^P([0-9]{1,2}[W])?([0-9]{1,2}[D])?([T]{0,1})?([0-9]{1,2}[H])?([0-9]{1,2}[M])?([0-9]{1,2}[S])?/', $start[0], $duration);
            $hash['duration'] = $duration;
        }

        if (($start = $this->getValues('DTEND', $i)) !== null &&
            count($start) == 1) {
            $end = $this->mapDate($start[0]);
            $hash['end_date'] = $end['year'] . '-' . $end['month'] . '-' . $end['mday'];
            $hash['end_time'] = $end['hour'] . ':' . $end['min'] . ':' . $end['sec'];
        }

        return $hash;
    }

    /**
     * Takes all necessary actions for the given import step,
     * parameters and form values and returns the next necessary step.
     *
     * @access public
     *
     * @param integer $action        The current step. One of the IMPORT_*
     *                               constants.
     * @param optional array $param  An associative array containing needed
     *                               parameters for the current step.
     * @return mixed  Either the next step as an integer constant or imported
     *                data set after the final step.
     */
    function nextStep($action, $param = array())
    {
        switch ($action) {
        case IMPORT_FILE:
            $next_step = parent::nextStep($action, $param);
            if (is_a($next_step, 'PEAR_Error')) {
                return $next_step;
            }

            $import_data = $this->importFile($_FILES['import_file']['tmp_name']);
            if (is_a($import_data, 'PEAR_Error')) {
                return $import_data;
            }
            /* Build the result data set as an associative array. */
            $data = array();
            for ($i = 0; $i < $this->count(); $i++) {
                $data[] = $this->toHash($i);
            }
            return $data;
            break;

        default:
            return parent::nextStep($action, $param);
            break;
        }
    }

}
