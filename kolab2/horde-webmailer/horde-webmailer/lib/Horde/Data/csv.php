<?php
/**
 * @package Horde_Data
 */

/**
 * Horde's File_CSV class.
 */
include_once 'File/CSV.php';

/**
 * Horde_Data implementation for comma-separated data (CSV).
 *
 * $Horde: framework/Data/Data/csv.php,v 1.30.10.12 2009-01-06 15:23:01 jan Exp $
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
class Horde_Data_csv extends Horde_Data {

    var $_extension = 'csv';
    var $_contentType = 'text/comma-separated-values';

    /**
     * Tries to discover the CSV file's parameters.
     *
     * @param string $filename  The name of the file to investigate.
     *
     * @return array  An associative array with the following possible keys:
     * <pre>
     * 'sep':    The field separator
     * 'quote':  The quoting character
     * 'fields': The number of fields (columns)
     * </pre>
     */
    function discoverFormat($filename)
    {
        return File_CSV::discoverFormat($filename);
    }

    /**
     * Imports and parses a CSV file.
     *
     * @param string $filename  The name of the file to parse.
     * @param boolean $header   Does the first line contain the field/column
     *                          names?
     * @param string $sep       The field/column separator.
     * @param string $quote     The quoting character.
     * @param integer $fields   The number or fields/columns.
     * @param string $charset   The file's charset. @since Horde 3.1.
     * @param string $crlf      The file's linefeed characters. @since Horde 3.1.
     *
     * @return array  A two-dimensional array of all imported data rows.  If
     *                $header was true the rows are associative arrays with the
     *                field/column names as the keys.
     */
    function importFile($filename, $header = false, $sep = '', $quote = '',
                        $fields = null, $import_mapping = array(),
                        $charset = null, $crlf = null)
    {
        /* File_CSV is a bit picky at what parameters it expects. */
        $conf = array();
        if ($fields) {
            $conf['fields'] = $fields;
        } else {
            return array();
        }
        if (!empty($quote)) {
            $conf['quote'] = $quote;
        }
        if (empty($sep)) {
            $conf['sep'] = ',';
        } else {
            $conf['sep'] = $sep;
        }
        if (!empty($crlf)) {
            $conf['crlf'] = $crlf;
        }

        /* Strip and keep the first line if it contains the field
         * names. */
        if ($header) {
            $head = File_CSV::read($filename, $conf);
            if (is_a($head, 'PEAR_Error')) {
                return $head;
            }
            if (!empty($charset)) {
                $head = String::convertCharset($head, $charset, NLS::getCharset());
            }
        }

        $data = array();
        while ($line = File_CSV::read($filename, $conf)) {
            if (is_a($line, 'PEAR_Error')) {
                return $line;
            }
            if (!empty($charset)) {
                $line = String::convertCharset($line, $charset, NLS::getCharset());
            }
            if (!isset($head)) {
                $data[] = $line;
            } else {
                $newline = array();
                for ($i = 0; $i < count($head); $i++) {
                    if (isset($import_mapping[$head[$i]])) {
                        $head[$i] = $import_mapping[$head[$i]];
                    }
                    $cell = $line[$i];
                    $cell = preg_replace("/\"\"/", "\"", $cell);
                    $newline[$head[$i]] = empty($cell) ? '' : $cell;
                }
                $data[] = $newline;
            }
        }

        $fp = File_CSV::getPointer($filename, $conf);
        if ($fp && !is_a($fp, 'PEAR_Error')) {
            rewind($fp);
        }

        $this->_warnings = File_CSV::warning();
        return $data;
    }

    /**
     * Builds a CSV file from a given data structure and returns it as a
     * string.
     *
     * @param array $data      A two-dimensional array containing the data set.
     * @param boolean $header  If true, the rows of $data are associative
     *                         arrays with field names as their keys.
     *
     * @return string  The CSV data.
     */
    function exportData($data, $header = false, $export_mapping = array())
    {
        if (!is_array($data) || count($data) == 0) {
            return '';
        }

        $export = '';
        $eol = "\n";
        $head = array_keys(current($data));
        if ($header) {
            foreach ($head as $key) {
                if (!empty($key)) {
                    if (isset($export_mapping[$key])) {
                        $key = $export_mapping[$key];
                    }
                    $export .= '"' . $key . '"';
                }
                $export .= ',';
            }
            $export = substr($export, 0, -1) . $eol;
        }

        foreach ($data as $row) {
            foreach ($head as $key) {
                $cell = $row[$key];
                if (!empty($cell) || $cell === 0) {
                    $export .= '"' . $cell . '"';
                }
                $export .= ',';
            }
            $export = substr($export, 0, -1) . $eol;
        }

        return $export;
    }

    /**
     * Builds a CSV file from a given data structure and triggers its
     * download.  It DOES NOT exit the current script but only outputs the
     * correct headers and data.
     *
     * @param string $filename  The name of the file to be downloaded.
     * @param array $data       A two-dimensional array containing the data
     *                          set.
     * @param boolean $header   If true, the rows of $data are associative
     *                          arrays with field names as their keys.
     */
    function exportFile($filename, $data, $header = false,
                        $export_mapping = array())
    {
        $export = $this->exportData($data, $header, $export_mapping);
        $GLOBALS['browser']->downloadHeaders($filename, 'application/csv', false, strlen($export));
        echo $export;
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
        switch ($action) {
        case IMPORT_FILE:
            $next_step = parent::nextStep($action, $param);
            if (is_a($next_step, 'PEAR_Error')) {
                return $next_step;
            }

            /* Move uploaded file so that we can read it again in the next
               step after the user gave some format details. */
            $file_name = Horde::getTempFile('import', false);
            if (!move_uploaded_file($_FILES['import_file']['tmp_name'], $file_name)) {
                return PEAR::raiseError(_("The uploaded file could not be saved."));
            }
            $_SESSION['import_data']['file_name'] = $file_name;

            /* Try to discover the file format ourselves. */
            $conf = $this->discoverFormat($file_name);
            if (!$conf) {
                $conf = array('sep' => ',');
            }
            $_SESSION['import_data'] = array_merge($_SESSION['import_data'], $conf);

            /* Check if charset was specified. */
            $_SESSION['import_data']['charset'] = Util::getFormData('charset');

            /* Read the file's first two lines to show them to the user. */
            $_SESSION['import_data']['first_lines'] = '';
            $fp = @fopen($file_name, 'r');
            if ($fp) {
                $line_no = 1;
                while ($line_no < 3 && $line = fgets($fp)) {
                    if (!empty($_SESSION['import_data']['charset'])) {
                        $line = String::convertCharset($line, $_SESSION['import_data']['charset'], NLS::getCharset());
                    }
                    $newline = String::length($line) > 100 ? "\n" : '';
                    $_SESSION['import_data']['first_lines'] .= substr($line, 0, 100) . $newline;
                    $line_no++;
                }
            }
            return IMPORT_CSV;

        case IMPORT_CSV:
            $_SESSION['import_data']['header'] = Util::getFormData('header');
            $import_mapping = array();
            if (isset($param['import_mapping'])) {
                $import_mapping = $param['import_mapping'];
            }
            $import_data = $this->importFile($_SESSION['import_data']['file_name'],
                                             $_SESSION['import_data']['header'],
                                             Util::getFormData('sep'),
                                             Util::getFormData('quote'),
                                             Util::getFormData('fields'),
                                             $import_mapping,
                                             $_SESSION['import_data']['charset'],
                                             $_SESSION['import_data']['crlf']);
            $_SESSION['import_data']['data'] = $import_data;
            unset($_SESSION['import_data']['map']);
            return IMPORT_MAPPED;

        default:
            return parent::nextStep($action, $param);
        }
    }

}
