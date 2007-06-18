<?php

require_once 'PEAR.php';

// Import constants
/** @const IMPORT_MAPPED Import already mapped csv data.          */ define('IMPORT_MAPPED', 1);
/** @const IMPORT_DATETIME Map date and time entries of csv data. */ define('IMPORT_DATETIME', 2);
/** @const IMPORT_CSV Import generic CSV data.                    */ define('IMPORT_CSV', 3);
/** @const IMPORT_OUTLOOK Import MS Outlook data.                 */ define('IMPORT_OUTLOOK', 4);
/** @const IMPORT_ICALENDAR Import vCalendar/iCalendar data.      */ define('IMPORT_ICALENDAR', 5);
/** @const IMPORT_VCARD Import vCards.                            */ define('IMPORT_VCARD', 6);
/** @const IMPORT_TSV Import generic tsv data.                    */ define('IMPORT_TSV', 7);
/** @const IMPORT_MULBERRY Import Mulberry address book data      */ define('IMPORT_MULBERRY', 8);
/** @const IMPORT_PINE Import Pine address book data.             */ define('IMPORT_PINE', 9);
/** @const IMPORT_PDB Import palm datebook (.pdb).                */ define('IMPORT_PDB', 10);
/** @const IMPORT_FILE Import file.                               */ define('IMPORT_FILE', 11);
/** @const IMPORT_DATA Import data.                               */ define('IMPORT_DATA', 12);

// Export constants
/** @const EXPORT_CSV Export generic CSV data.     */ define('EXPORT_CSV', 100);
/** @const EXPORT_ICALENDAR Export iCalendar data. */ define('EXPORT_ICALENDAR', 101);
/** @const EXPORT_VCARD Export vCards.             */ define('EXPORT_VCARD', 102);
/** @const EXPORT_TSV Export TSV data.             */ define('EXPORT_TSV', 103);

/**
 * Abstract class to handle different kinds of Data formats and to
 * help data exchange between Horde applications and external sources.
 *
 * $Horde: framework/Data/Data.php,v 1.77 2004/05/25 15:52:43 jan Exp $
 *
 * Copyright 1999-2004 Jan Schneider <jan@horde.org>
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @version $Revision: 1.1.2.1 $
 * @since   Horde 1.3
 * @package Horde_Data
 */
class Horde_Data extends PEAR {

    var $_extension;
    var $_contentType = 'text/plain';

    /**
     * Stub to import passed data.
     */
    function importData()
    {
    }

    /**
     * Stub to return exported data.
     */
    function exportData()
    {
    }

    /**
     * Stub to import a file.
     */
    function importFile($filename, $header = false)
    {
        $fp = @fopen($filename, 'r');
        $data = @fread($fp, @filesize($filename));
        @fclose($fp);
        return $this->importData($data, $header);
    }

    /**
     * Stub to export data to a file.
     */
    function exportFile()
    {
    }

    /**
     * Tries to determine the expected newline character based on the
     * platform information passed by the browser's agent header.
     *
     * @access public
     * @return string  The guessed expected newline characters, either \n, \r
     *                 or \r\n.
     */
    function getNewline()
    {
        require_once 'Horde/Browser.php';
        $browser = &Browser::singleton();

        switch ($browser->getPlatform()) {
        case 'win':
            return "\r\n";

        case 'mac':
            return "\r";

        case 'unix':
        default:
            return "\n";
        }
    }

    function getFilename($basename)
    {
        return $basename . '.' . $this->_extension;
    }

    function getContentType()
    {
        return $this->_contentType;
    }

    /**
     * Attempts to return a concrete Data instance based on $format.
     *
     * @param mixed $format  The type of concrete Data subclass to return.
     *                       This is based on the storage driver ($format). The
     *                       code is dynamically included. If $format is an array,
     *                       then we will look in $format[0]/lib/Data/ for the subclass
     *                       implementation named $format[1].php.
     *
     * @return object Data   The newly created concrete Data instance, or false
     *                       on an error.
     */
    function &factory($format)
    {
        if (is_array($format)) {
            $app = $format[0];
            $format = $format[1];
        }

        $format = basename($format);

        if (empty($format) || (strcmp($format, 'none') == 0)) {
            return $ret = &new Horde_Data();
        }

        if (!empty($app)) {
            require_once $GLOBALS['registry']->getParam('fileroot', $app) . '/lib/Data/' . $format . '.php';
        } else {
            require_once 'Horde/Data/' . $format . '.php';
        }
        $class = 'Horde_Data_' . $format;
        if (class_exists($class)) {
            return $ret = &new $class();
        } else {
            return PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }
    }

    /**
     * Attempts to return a reference to a concrete Data instance
     * based on $format. It will only create a new instance if no Data
     * instance with the same parameters currently exists.
     *
     * This should be used if multiple data sources (and,
     * thus, multiple Data instances) are required.
     *
     * This method must be invoked as: $var = &Data::singleton()
     *
     * @param string $format The type of concrete Data subclass to return.
     *                       This is based on the storage driver ($format). The
     *                       code is dynamically included.
     *
     * @return object Data  The concrete Data reference, or false on an error.
     */
    function &singleton($format)
    {
        static $instances;
        if (!isset($instances)) {
            $instances = array();
        }

        $signature = serialize($format);
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Horde_Data::factory($format);
        }

        return $instances[$signature];
    }

    /**
     * Maps a date/time string to an associative array.
     *
     * @access private
     * @param string $date             The date.
     * @param string $type             One of 'date', 'time' or 'datetime'.
     * @param string $delimiter        The character that seperates the different
     *                                 date/time parts.
     * @param optional string $format  If 'ampm' and $date contains a time we
     *                                 assume that it is in AM/PM format.
     * @return string                  The date or time in ISO format.
     */
    function mapDate($date, $type, $delimiter, $format = null)
    {
        switch ($type) {
        case 'date':
            $dates = explode($delimiter, $date);
            if (count($dates) != 3) {
                return $date;
            }
            $index = array_flip(explode('/', $format));
            return $dates[$index['year']] . '-' . $dates[$index['month']] . '-' . $dates[$index['mday']];

        case 'time':
            $dates = explode($delimiter, $date);
            if (count($dates) < 2 || count($dates) > 3) {
                return $date;
            }
            if ($format == 'ampm') {
                if (strpos(strtolower($dates[count($dates)-1]), 'pm') !== false) {
                    if ($dates[0] !== '12') {
                        $dates[0] += 12;
                    }
                } elseif ($dates[0] == '12') {
                    $dates[0] = '0';
                }
                $dates[count($dates)-1] = (int) $dates[count($dates)-1];
            }
            return $dates[0] . ':' . $dates[1] . (count($dates) == 3 ? (':' . $dates[2]) : ':00');

        case 'datetime':
            return '';

        }
    }

    /**
     * Takes all necessary actions for the given import step, parameters and
     * form values and returns the next necessary step.
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
        /* First step. */
        if (is_null($action)) {
            $_SESSION['import_data'] = array();
            return IMPORT_FILE;
        }

        switch ($action) {
        case IMPORT_FILE:
            /* Sanitize uploaded file. */
            $import_format = Util::getFormData('import_format');
            $check_upload = Browser::wasFileUploaded('import_file', $param['file_types'][$import_format]);
            if (is_a($check_upload, 'PEAR_Error')) {
                return $check_upload;
            }
            if ($_FILES['import_file']['size'] <= 0) {
                return PEAR::raiseError(_("The file contained no data."));
            }
            $_SESSION['import_data']['format'] = $import_format;
            break;

        case IMPORT_MAPPED:
            $dataKeys = Util::getFormData('dataKeys', '');
            $appKeys = Util::getFormData('appKeys', '');
            if (empty($dataKeys) || empty($appKeys)) {
                global $registry;
                return PEAR::raiseError(sprintf(_("You didn't map any fields from the imported file to the corresponding fields in %s."),
                                                $registry->getParam('name')));
            }
            $dataKeys = explode("\t", $dataKeys);
            $appKeys = explode("\t", $appKeys);
            $map = array();
            $dates = array();
            foreach ($appKeys as $key => $app) {
                $map[$dataKeys[$key]] = $app;
                if (array_key_exists('time_fields', $param) &&
                    array_key_exists($app, $param['time_fields'])) {
                    $dates[$dataKeys[$key]]['type'] = $param['time_fields'][$app];
                    $dates[$dataKeys[$key]]['values'] = array();
                    $i = 0;
                    /* Build an example array of up to 10 date/time fields. */
                    while ($i < count($_SESSION['import_data']['data']) && count($dates[$dataKeys[$key]]['values']) < 10) {
                        if (!empty($_SESSION['import_data']['data'][$i][$dataKeys[$key]])) {
                            $dates[$dataKeys[$key]]['values'][] = $_SESSION['import_data']['data'][$i][$dataKeys[$key]];
                        }
                        $i++;
                    }
                }
            }
            $_SESSION['import_data']['map'] = $map;
            if (count($dates) > 0) {
                $_SESSION['import_data']['dates'] = $dates;
                return IMPORT_DATETIME;
            }
            return $this->nextStep(IMPORT_DATA, $param);

        case IMPORT_DATETIME:
        case IMPORT_DATA:
            if ($action == IMPORT_DATETIME) {
                $delimiter = Util::getFormData('delimiter');
                $format = Util::getFormData('format');
            }
            if (!array_key_exists('data', $_SESSION['import_data'])) {
                return PEAR::raiseError(_("The uploaded data was lost since the previous step."));
            }
            /* Build the result data set as an associative array. */
            $data = array();
            foreach ($_SESSION['import_data']['data'] as $row) {
                $data_row = array();
                foreach ($row as $key => $val) {
                    if (array_key_exists($key, $_SESSION['import_data']['map'])) {
                        $mapped_key = $_SESSION['import_data']['map'][$key];
                        if ($action == IMPORT_DATETIME &&
                            !empty($val) &&
                            array_key_exists('time_fields', $param) &&
                            array_key_exists($mapped_key, $param['time_fields'])) {
                            $val = $this->mapDate($val, $param['time_fields'][$mapped_key], $delimiter[$key], $format[$key]);
                        }
                        $data_row[$_SESSION['import_data']['map'][$key]] = $val;
                    }
                }
                $data[] = $data_row;
            }
            return $data;
        }
    }

    /**
     * Cleans the session data up and removes any uploaded and moved
     * files. If a function called "_cleanup()" exists, this gets
     * called too.
     *
     * @return mixed  If _cleanup() was called, the return value of this call.
     *                This should be the value of the first import step.
     */
    function cleanup()
    {
        if (array_key_exists('file_name', $_SESSION['import_data'])) {
            @unlink($_SESSION['import_data']['file_name']);
        }
        $_SESSION['import_data'] = array();
        if (function_exists('_cleanup')) {
            return _cleanup();
        }
    }

}
