<?php

require_once 'Horde/iCalendar.php';

/**
 * Abstract implementation of the Horde_Data:: API for IMC data -
 * vCards and iCalendar data, etc. Provides a number of utility
 * methods that vCard and iCalendar implementation can share and rely
 * on.
 *
 * $Horde: framework/Data/Data/imc.php,v 1.32.10.12 2009-01-06 15:23:01 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @package Horde_Data
 * @since   Horde 3.0
 */
class Horde_Data_imc extends Horde_Data {

    var $_iCal = false;

    function importData($text)
    {
        $this->_iCal = new Horde_iCalendar();
        if (!$this->_iCal->parsevCalendar($text)) {
            return PEAR::raiseError(_("There was an error importing the iCalendar data."));
        }

        return $this->_iCal->getComponents();
    }

    /**
     * Builds an iCalendar file from a given data structure and
     * returns it as a string.
     *
     * @param array $data     An array containing Horde_iCalendar_vevent
     *                        objects
     * @param string $method  The iTip method to use.
     *
     * @return string  The iCalendar data.
     */
    function exportData($data, $method = 'REQUEST')
    {
        $this->_iCal = new Horde_iCalendar();
        $this->_iCal->setAttribute('METHOD', $method);

        foreach ($data as $event) {
            $this->_iCal->addComponent($event);
        }

        return $this->_iCal->exportvCalendar();
    }

    /**
     * Builds an iCalendar file from a given data structure and
     * triggers its download.  It DOES NOT exit the current script but
     * only outputs the correct headers and data.
     *
     * @param string $filename   The name of the file to be downloaded.
     * @param array $data        An array containing Horde_iCalendar_vevents
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
     * @param integer $action  The current step. One of the IMPORT_* constants.
     * @param array $param     An associative array containing needed
     *                         parameters for the current step.
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

            return $this->_iCal->getComponents();
            break;

        default:
            return parent::nextStep($action, $param);
            break;
        }
    }

}
