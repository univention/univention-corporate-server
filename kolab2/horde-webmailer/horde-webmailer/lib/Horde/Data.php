<?php

require_once 'PEAR.php';

// Import constants
/** Import already mapped csv data.        */ define('IMPORT_MAPPED', 1);
/** Map date and time entries of csv data. */ define('IMPORT_DATETIME', 2);
/** Import generic CSV data.               */ define('IMPORT_CSV', 3);
/** Import MS Outlook data.                */ define('IMPORT_OUTLOOK', 4);
/** Import vCalendar/iCalendar data.       */ define('IMPORT_ICALENDAR', 5);
/** Import vCards.                         */ define('IMPORT_VCARD', 6);
/** Import generic tsv data.               */ define('IMPORT_TSV', 7);
/** Import Mulberry address book data      */ define('IMPORT_MULBERRY', 8);
/** Import Pine address book data.         */ define('IMPORT_PINE', 9);
/** Import file.                           */ define('IMPORT_FILE', 11);
/** Import data.                           */ define('IMPORT_DATA', 12);

// Export constants
/** Export generic CSV data. */ define('EXPORT_CSV', 100);
/** Export iCalendar data.   */ define('EXPORT_ICALENDAR', 101);
/** Export vCards.           */ define('EXPORT_VCARD', 102);
/** Export TSV data.         */ define('EXPORT_TSV', 103);
/** Export Outlook CSV data. */ define('EXPORT_OUTLOOKCSV', 104);

/**
 * Abstract class to handle different kinds of Data formats and to
 * help data exchange between Horde applications and external sources.
 *
 * $Horde: framework/Data/Data.php,v 1.80.10.19 2009-01-06 15:23:00 jan Exp $
 *
 * Copyright 1999-2009 The Horde Project (http://www.horde.org/)
 *
 * See the enclosed file COPYING for license information (LGPL). If you
 * did not receive this file, see http://www.fsf.org/copyleft/lgpl.html.
 *
 * @author  Jan Schneider <jan@horde.org>
 * @author  Chuck Hagenbuch <chuck@horde.org>
 * @since   Horde 1.3
 * @package Horde_Data
 */
class Horde_Data extends PEAR {

    /**
     * File extension.
     *
     * @var string
     */
    var $_extension;

    /**
     * MIME content type.
     *
     * @var string
     */
    var $_contentType = 'text/plain';

    /**
     * A list of warnings raised during the last operation.
     *
     * @var array
     * @since Horde 3.1
     */
    var $_warnings = array();

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
        $data = file_get_contents($filename);
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

    /**
     * Returns the full filename including the basename and extension.
     *
     * @param string $basename  Basename for the file.
     * 
     * @return string  The file name.
     */
    function getFilename($basename)
    {
        return $basename . '.' . $this->_extension;
    }

    /**
     * Returns the content type.
     *
     * @return string  The content type.
     */
    function getContentType()
    {
        return $this->_contentType;
    }

    /**
     * Returns a list of warnings that have been raised during the last
     * operation.
     *
     * @since Horde 3.1
     *
     * @return array  A (possibly empty) list of warnings.
     */
    function warnings()
    {
        return $this->_warnings;
    }

    /**
     * Attempts to return a concrete Horde_Data instance based on $format.
     *
     * @param mixed $format  The type of concrete Horde_Data subclass to
     *                       return. If $format is an array, then we will look
     *                       in $format[0]/lib/Data/ for the subclass
     *                       implementation named $format[1].php.
     *
     * @return Horde_Data  The newly created concrete Horde_Data instance, or
     *                     false on an error.
     */
    function &factory($format)
    {
        if (is_array($format)) {
            $app = $format[0];
            $format = $format[1];
        }

        $format = basename($format);

        if (empty($format) || (strcmp($format, 'none') == 0)) {
            $data =& new Horde_Data();
            return $data;
        }

        if (!empty($app)) {
            require_once $GLOBALS['registry']->get('fileroot', $app) . '/lib/Data/' . $format . '.php';
        } else {
            require_once 'Horde/Data/' . $format . '.php';
        }
        $class = 'Horde_Data_' . $format;
        if (class_exists($class)) {
            $data =& new $class();
        } else {
            $data = PEAR::raiseError('Class definition of ' . $class . ' not found.');
        }

        return $data;
    }

    /**
     * Attempts to return a reference to a concrete Horde_Data instance
     * based on $format. It will only create a new instance if no Horde_Data
     * instance with the same parameters currently exists.
     *
     * This should be used if multiple data sources (and, thus, multiple
     * Horde_Data instances) are required.
     *
     * This method must be invoked as: $var = &Horde_Data::singleton()
     *
     * @param string $format  The type of concrete Horde_Data subclass to
     *                        return.
     *
     * @return Horde_Data  The concrete Horde_Data reference, or false on an
     *                     error.
     */
    function &singleton($format)
    {
        static $instances = array();

        $signature = serialize($format);
        if (!isset($instances[$signature])) {
            $instances[$signature] = &Horde_Data::factory($format);
        }

        return $instances[$signature];
    }

    /**
     * Maps a date/time string to an associative array.
     *
     * The method signature has changed in Horde 3.1.3.
     *
     * @access private
     *
     * @param string $date   The date.
     * @param string $type   One of 'date', 'time' or 'datetime'.
     * @param array $params  Two-dimensional array with additional information
     *                       about the formatting. Possible keys are:
     *                       - delimiter - The character that seperates the
     *                         different date/time parts.
     *                       - format - If 'ampm' and $date contains a time we
     *                         assume that it is in AM/PM format.
     *                       - order - If $type is 'datetime' the order of the
     *                         day and time parts: -1 (timestamp), 0
     *                         (day/time), 1 (time/day).
     * @param integer $key   The key to use for $params.
     *
     * @return string  The date or time in ISO format.
     */
    function mapDate($date, $type, $params, $key)
    {
        switch ($type) {
        case 'date':
        case 'monthday':
        case 'monthdayyear':
            $dates = explode($params['delimiter'][$key], $date);
            if (count($dates) != 3) {
                return $date;
            }
            $index = array_flip(explode('/', $params['format'][$key]));
            return $dates[$index['year']] . '-' . $dates[$index['month']] . '-' . $dates[$index['mday']];

        case 'time':
            $dates = explode($params['delimiter'][$key], $date);
            if (count($dates) < 2 || count($dates) > 3) {
                return $date;
            }
            if ($params['format'][$key] == 'ampm') {
                if (strpos(strtolower($dates[count($dates)-1]), 'pm') !== false) {
                    if ($dates[0] !== '12') {
                        $dates[0] += 12;
                    }
                } elseif ($dates[0] == '12') {
                    $dates[0] = '0';
                }
                $dates[count($dates) - 1] = sprintf('%02d', $dates[count($dates)-1]);
            }
            return $dates[0] . ':' . $dates[1] . (count($dates) == 3 ? (':' . $dates[2]) : ':00');

        case 'datetime':
            switch ($params['order'][$key]) {
            case -1:
                return (string)(int)$date == $date
                    ? date('Y-m-d H:i:s', $date)
                    : $date;
            case 0:
                list($day, $time) = explode(' ', $date, 2);
                break;
            case 1:
               list($time, $day) = explode(' ', $date, 2);
               break;
            }
            $date = $this->mapDate($day, 'date',
                                   array('delimiter' => $params['day_delimiter'],
                                         'format' => $params['day_format']),
                                   $key);
            $time = $this->mapDate($time, 'time',
                                   array('delimiter' => $params['time_delimiter'],
                                         'format' => $params['time_format']),
                                   $key);
            return $date . ' ' . $time;

        }
    }

    /**
     * Takes all necessary actions for the given import step, parameters and
     * form values and returns the next necessary step.
     *
     * @param integer $action  The current step. One of the IMPORT_* constants.
     * @param array $param     An associative array containing needed
     *                         parameters for the current step.
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
                                                $registry->get('name')));
            }
            $dataKeys = explode("\t", $dataKeys);
            $appKeys = explode("\t", $appKeys);
            $map = array();
            $dates = array();
            foreach ($appKeys as $key => $app) {
                $map[$dataKeys[$key]] = $app;
                if (isset($param['time_fields']) &&
                    isset($param['time_fields'][$app])) {
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
                foreach ($dates as $key => $data) {
                    if (count($data['values'])) {
                        $_SESSION['import_data']['dates'] = $dates;
                        return IMPORT_DATETIME;
                    }
                }
            }
            return $this->nextStep(IMPORT_DATA, $param);

        case IMPORT_DATETIME:
        case IMPORT_DATA:
            if ($action == IMPORT_DATETIME) {
                $params = array('delimiter' => Util::getFormData('delimiter'),
                                'format' => Util::getFormData('format'),
                                'order' => Util::getFormData('order'),
                                'day_delimiter' => Util::getFormData('day_delimiter'),
                                'day_format' => Util::getFormData('day_format'),
                                'time_delimiter' => Util::getFormData('time_delimiter'),
                                'time_format' => Util::getFormData('time_format'));
            }
            if (!isset($_SESSION['import_data']['data'])) {
                return PEAR::raiseError(_("The uploaded data was lost since the previous step."));
            }
            /* Build the result data set as an associative array. */
            $data = array();
            foreach ($_SESSION['import_data']['data'] as $row) {
                $data_row = array();
                foreach ($row as $key => $val) {
                    if (isset($_SESSION['import_data']['map'][$key])) {
                        $mapped_key = $_SESSION['import_data']['map'][$key];
                        if ($action == IMPORT_DATETIME &&
                            !empty($val) &&
                            isset($param['time_fields']) &&
                            isset($param['time_fields'][$mapped_key])) {
                            $val = $this->mapDate($val, $param['time_fields'][$mapped_key], $params, $key);
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
        if (isset($_SESSION['import_data']['file_name'])) {
            @unlink($_SESSION['import_data']['file_name']);
        }
        $_SESSION['import_data'] = array();
        if (function_exists('_cleanup')) {
            return _cleanup();
        }
    }

}
