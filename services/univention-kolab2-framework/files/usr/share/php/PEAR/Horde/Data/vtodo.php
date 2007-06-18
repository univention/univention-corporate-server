<?php

include_once 'Horde/iCalendar.php';

/**
 * Implement the Horde_Data:: API for vTodo data.
 *
 * $Horde: framework/Data/Data/vtodo.php,v 1.6 2004/04/07 14:43:06 chuck Exp $
 *
 * Copyright 1999-2004 Jan Schneider <jan@horde.org>
 * Copyright 1999-2004 Chuck Hagenbuch <chuck@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @package Horde_Data
 * @since   Horde 3.0
 */
class Horde_Data_vtodo extends Horde_Data {

    function importData($text)
    {
        $iCal = &new Horde_iCalendar();
        if (!$iCal->parsevCalendar($text)) {
            return PEAR::raiseError('Error parsing iCalendar text.');
        }

        return $iCal->getComponents();
    }

    /**
     * Builds a vTodo file from a given data structure and returns it
     * as a string.
     *
     * @access public
     *
     * @param array $data  A two-dimensional array containing the data set.
     *
     * @return string  The vTodo data.
     */
    function exportData($data)
    {
        $iCal = &new Horde_iCalendar();

        foreach ($data as $todo) {
            $vTodo = Horde_iCalendar::newComponent('vtodo', $iCal);
            $vTodo->fromArray($todo);

            $iCal->addComponent($vTodo);
        }

        return $iCal->exportvCalendar();
    }

    /**
     * Builds a vTodo file from a given data structure and triggers
     * its download. It DOES NOT exit the current script but only
     * outputs the correct headers and data.
     *
     * @access public
     *
     * @param string $filename   The name of the file to be downloaded.
     * @param array  $data       A two-dimensional array containing the data set.
     */
    function exportFile($filename, $data)
    {
        $export = $this->exportData($data);
        $GLOBALS['browser']->downloadHeaders($filename, 'text/calendar', false, strlen($export));
        echo $export;
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
     *
     * @return mixed  Either the next step as an integer constant or imported
     *                data set after the final step.
     */
    function nextStep($action, $param = array())
    {
        switch ($action) {
        case IMPORT_FILE:
            $res = parent::nextStep($action, $param);
            if (is_a($res, 'PEAR_Error')) {
                return $res;
            }

            $import_data = $this->importFile($_FILES['import_file']['tmp_name']);
            if (is_a($import_data, 'PEAR_Error')) {
                return $import_data;
            }

            /* Build the result data set as an associative array. */
            $data = array();
            foreach ($import_data as $vtodo) {
                if (is_a($vtodo, 'Horde_iCalendar_vtodo')) {
                    $data[] = $vtodo->toArray();
                }
            }
            return $data;
            break;

        default:
            return parent::nextStep($action, $param);
            break;
        }
    }

}
